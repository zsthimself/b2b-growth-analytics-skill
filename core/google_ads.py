# -*- coding: utf-8 -*-
"""
Google Ads API Adapter (v25 REST).
Supports campaign performance, search terms audit, conversion attribution,
and safe negative keyword injection with automated read-back assertions.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from google.oauth2.credentials import Credentials
from core.google_api import GoogleAPIError, execute_request


GOOGLE_ADS_BASE = "https://googleads.googleapis.com"
DEFAULT_API_VERSION = "v25"


@dataclass(frozen=True)
class GoogleAdsConfig:
    developer_token: str
    customer_id: str
    login_customer_id: str | None = None
    api_version: str = DEFAULT_API_VERSION


def config_from_env() -> GoogleAdsConfig:
    dev_token_file = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN_FILE")
    if not dev_token_file or not Path(dev_token_file).is_file():
        raise ValueError(f"GOOGLE_ADS_DEVELOPER_TOKEN_FILE not found or invalid: {dev_token_file}")

    with open(dev_token_file, "r", encoding="utf-8") as f:
        developer_token = f.read().strip()

    customer_id = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "").strip()
    if not customer_id:
        raise ValueError("GOOGLE_ADS_CUSTOMER_ID is required (10 digits).")

    login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "").strip() or None
    api_version = os.environ.get("GOOGLE_ADS_API_VERSION", DEFAULT_API_VERSION).strip()

    return GoogleAdsConfig(
        developer_token=developer_token,
        customer_id=customer_id,
        login_customer_id=login_customer_id,
        api_version=api_version,
    )


class GoogleAdsClient:
    def __init__(self, creds: Credentials, config: GoogleAdsConfig | None = None):
        self.creds = creds
        self.config = config or config_from_env()

    def _headers(self) -> dict[str, str]:
        headers = {"developer-token": self.config.developer_token}
        if self.config.login_customer_id:
            headers["login-customer-id"] = self.config.login_customer_id
        return headers

    def search_stream(self, query: str, customer_id: str | None = None) -> list[dict[str, Any]]:
        """Execute a GAQL query via googleAds:searchStream endpoint."""
        target_customer = customer_id or self.config.customer_id
        url = f"{GOOGLE_ADS_BASE}/{self.config.api_version}/customers/{target_customer}/googleAds:searchStream"
        resp = execute_request(
            method="POST",
            url=url,
            creds=self.creds,
            headers=self._headers(),
            json_body={"query": query},
        )
        # searchStream returns a JSON array of batch results
        rows = []
        if isinstance(resp, list):
            for batch in resp:
                rows.extend(batch.get("results", []))
        return rows

    def get_campaign_metrics(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Fetch daily campaign performance metrics."""
        query = f"""
            SELECT
              segments.date,
              campaign.id,
              campaign.name,
              campaign.status,
              campaign.advertising_channel_type,
              metrics.cost_micros,
              metrics.clicks,
              metrics.impressions,
              metrics.conversions,
              metrics.all_conversions
            FROM campaign
            WHERE segments.date >= '{start_date}' AND segments.date <= '{end_date}'
            ORDER BY segments.date DESC
        """
        rows = self.search_stream(query)
        result = []
        for r in rows:
            seg = r.get("segments", {})
            camp = r.get("campaign", {})
            met = r.get("metrics", {})
            cost = int(met.get("costMicros", 0)) / 1_000_000
            clicks = int(met.get("clicks", 0))
            impr = int(met.get("impressions", 0))
            conv = float(met.get("conversions", 0.0))
            all_conv = float(met.get("allConversions", 0.0))
            result.append({
                "date": seg.get("date"),
                "campaign_id": camp.get("id"),
                "campaign_name": camp.get("name"),
                "status": camp.get("status"),
                "channel_type": camp.get("advertisingChannelType"),
                "cost": round(cost, 2),
                "clicks": clicks,
                "impressions": impr,
                "cpc": round(cost / clicks, 2) if clicks > 0 else 0.0,
                "ctr": f"{round(clicks / impr * 100, 2)}%" if impr > 0 else "0%",
                "conversions": conv,
                "all_conversions": all_conv,
            })
        return result

    def get_search_terms(self, start_date: str, end_date: str, min_clicks: int = 0) -> list[dict[str, Any]]:
        """Fetch search terms audit report."""
        query = f"""
            SELECT
              campaign.name,
              campaign_search_term_view.search_term,
              metrics.cost_micros,
              metrics.clicks,
              metrics.impressions,
              metrics.conversions,
              metrics.all_conversions
            FROM campaign_search_term_view
            WHERE segments.date >= '{start_date}' AND segments.date <= '{end_date}'
        """
        rows = self.search_stream(query)
        terms = []
        for r in rows:
            camp = r.get("campaign", {})
            cst = r.get("campaignSearchTermView", {})
            met = r.get("metrics", {})
            cost = int(met.get("costMicros", 0)) / 1_000_000
            clicks = int(met.get("clicks", 0))
            if clicks < min_clicks and cost == 0:
                continue
            impr = int(met.get("impressions", 0))
            conv = float(met.get("conversions", 0.0))
            all_conv = float(met.get("allConversions", 0.0))
            terms.append({
                "campaign_name": camp.get("name"),
                "search_term": cst.get("searchTerm"),
                "cost": round(cost, 2),
                "clicks": clicks,
                "impressions": impr,
                "cpc": round(cost / clicks, 2) if clicks > 0 else 0.0,
                "conversions": conv,
                "all_conversions": all_conv,
            })
        terms.sort(key=lambda x: x["cost"], reverse=True)
        return terms

    def get_shared_negative_list(self, shared_set_id: str) -> dict[str, dict[str, Any]]:
        """Fetch all negative keywords in a shared set."""
        resource = f"customers/{self.config.customer_id}/sharedSets/{shared_set_id}"
        query = f"""
            SELECT
              shared_criterion.criterion_id,
              shared_criterion.keyword.text,
              shared_criterion.keyword.match_type
            FROM shared_criterion
            WHERE shared_criterion.shared_set = '{resource}'
        """
        rows = self.search_stream(query)
        negatives = {}
        for r in rows:
            sc = r.get("sharedCriterion", {})
            kw = sc.get("keyword", {})
            text = kw.get("text")
            negatives[text] = {
                "criterion_id": sc.get("criterionId"),
                "match_type": kw.get("matchType"),
            }
        return negatives

    def inject_negative_keywords(
        self,
        shared_set_id: str,
        new_keywords: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        Safely append negative keywords to a shared list.
        Performs pre-flight deduplication and post-write assertion.
        `new_keywords` format: [{"text": "sample", "match_type": "PHRASE"}, ...]
        """
        target_resource = f"customers/{self.config.customer_id}/sharedSets/{shared_set_id}"
        before_list = self.get_shared_negative_list(shared_set_id)

        to_add = [kw for kw in new_keywords if kw["text"] not in before_list]
        if not to_add:
            return {"status": "SKIPPED", "message": "All keywords already exist", "total_count": len(before_list)}

        operations = []
        for kw in to_add:
            operations.append({
                "create": {
                    "sharedSet": target_resource,
                    "keyword": {
                        "text": kw["text"],
                        "matchType": kw.get("match_type", "PHRASE").upper(),
                    },
                }
            })

        url = f"{GOOGLE_ADS_BASE}/{self.config.api_version}/customers/{self.config.customer_id}/sharedCriteria:mutate"
        resp = execute_request(
            method="POST",
            url=url,
            creds=self.creds,
            headers=self._headers(),
            json_body={"operations": operations},
        )

        # Read back assertion
        after_list = self.get_shared_negative_list(shared_set_id)
        verified_items = []
        for kw in to_add:
            if kw["text"] in after_list:
                verified_items.append({
                    "text": kw["text"],
                    "match_type": after_list[kw["text"]]["match_type"],
                    "criterion_id": after_list[kw["text"]]["criterion_id"],
                })
            else:
                raise RuntimeError(f"Assertion failed: injected keyword '{kw['text']}' missing in read-back!")

        return {
            "status": "SUCCESS",
            "added_count": len(to_add),
            "before_count": len(before_list),
            "after_count": len(after_list),
            "verified_items": verified_items,
        }
