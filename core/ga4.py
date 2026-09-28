# -*- coding: utf-8 -*-
"""
Google Analytics 4 (GA4) API Adapter.
Supports session engagement quality, paid traffic landing pages,
and granular key conversion event attribution.
"""

from __future__ import annotations

import os
from typing import Any
from google.oauth2.credentials import Credentials
from core.google_api import execute_request


GA4_DATA_BASE = "https://analyticsdata.googleapis.com/v1beta"


class GA4Client:
    def __init__(self, creds: Credentials, property_id: str | None = None):
        self.creds = creds
        self.property_id = property_id or os.environ.get("GA4_PROPERTY_ID", "").strip()
        if not self.property_id:
            raise ValueError("GA4_PROPERTY_ID is required.")

    def run_report(self, body: dict[str, Any]) -> dict[str, Any]:
        """Run custom GA4 report."""
        url = f"{GA4_DATA_BASE}/properties/{self.property_id}:runReport"
        return execute_request(method="POST", url=url, creds=self.creds, json_body=body)

    def get_traffic_acquisition(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Fetch traffic acquisition and engagement metrics by campaign."""
        body = {
            "dimensions": [
                {"name": "sessionSourceMedium"},
                {"name": "sessionCampaignName"},
            ],
            "metrics": [
                {"name": "sessions"},
                {"name": "engagedSessions"},
                {"name": "engagementRate"},
                {"name": "userEngagementDuration"},
                {"name": "keyEvents"},
            ],
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "limit": 50,
        }
        resp = self.run_report(body)
        rows = []
        for r in resp.get("rows", []):
            dims = [d["value"] for d in r.get("dimensionValues", [])]
            mets = [m["value"] for m in r.get("metricValues", [])]
            sessions = int(mets[0])
            engaged = int(mets[1])
            rate = float(mets[2])
            duration = float(mets[3])
            key_events = int(mets[4])
            rows.append({
                "source_medium": dims[0],
                "campaign_name": dims[1],
                "sessions": sessions,
                "engaged_sessions": engaged,
                "engagement_rate": f"{round(rate * 100, 1)}%",
                "avg_engagement_time_sec": round(duration / sessions, 1) if sessions > 0 else 0,
                "key_events": key_events,
            })
        return rows

    def get_key_events_log(
        self,
        start_date: str,
        end_date: str,
        event_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch chronological log of high-intent conversion events."""
        default_events = [
            "inquiry_submitted",
            "whatsapp_lead_submitted",
            "contact_email_copied",
            "contact_mail_client_opened",
            "GA4-点击 Whatsapp",
            "GA4-点击邮箱",
            "GA4-Request a quote",
        ]
        target_events = event_names or default_events

        body = {
            "dimensions": [
                {"name": "dateHourMinute"},
                {"name": "eventName"},
                {"name": "country"},
                {"name": "city"},
                {"name": "sessionSourceMedium"},
                {"name": "sessionCampaignName"},
                {"name": "pagePathPlusQueryString"},
            ],
            "metrics": [{"name": "eventCount"}],
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensionFilter": {
                "filter": {
                    "fieldName": "eventName",
                    "inListFilter": {"values": target_events},
                }
            },
            "limit": 250,
        }
        resp = self.run_report(body)
        records = []
        for r in resp.get("rows", []):
            dims = [d["value"] for d in r.get("dimensionValues", [])]
            cnt = int(r.get("metricValues", [{}])[0].get("value", 1))
            records.append({
                "timestamp": dims[0],
                "event_name": dims[1],
                "country": dims[2],
                "city": dims[3],
                "source_medium": dims[4],
                "campaign_name": dims[5],
                "page_path": dims[6],
                "count": cnt,
            })
        return records
