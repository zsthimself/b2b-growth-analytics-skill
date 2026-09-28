# -*- coding: utf-8 -*-
"""
Google Search Console (GSC) API Adapter.
Supports organic search performance, top query ranking, and page-level clicks/CTR.
"""

from __future__ import annotations

import os
from urllib.parse import quote_plus
from typing import Any
from google.oauth2.credentials import Credentials
from core.google_api import execute_request


GSC_BASE = "https://www.googleapis.com/webmasters/v3"


class GSCClient:
    def __init__(self, creds: Credentials, site_url: str | None = None):
        self.creds = creds
        self.site_url = site_url or os.environ.get("GSC_SITE_URL", "").strip()
        if not self.site_url:
            raise ValueError("GSC_SITE_URL is required.")

    def query_search_analytics(
        self,
        start_date: str,
        end_date: str,
        dimensions: list[str] | None = None,
        row_limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query Search Console searchAnalytics data."""
        encoded_site = quote_plus(self.site_url)
        url = f"{GSC_BASE}/sites/{encoded_site}/searchAnalytics/query"
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions or ["query"],
            "rowLimit": row_limit,
        }
        resp = execute_request(method="POST", url=url, creds=self.creds, json_body=body)
        rows = []
        for r in resp.get("rows", []):
            keys = r.get("keys", [])
            clicks = int(r.get("clicks", 0))
            impressions = int(r.get("impressions", 0))
            ctr = float(r.get("ctr", 0.0))
            position = float(r.get("position", 0.0))
            rows.append({
                "keys": keys,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": f"{round(ctr * 100, 2)}%",
                "position": round(position, 1),
            })
        return rows
