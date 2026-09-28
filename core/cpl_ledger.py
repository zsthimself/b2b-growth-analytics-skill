# -*- coding: utf-8 -*-
"""
Lead Ground Truth & Cost Per Lead (CPL) Ledger Engine.
Reconciles ad spend against actual CRM/form inquiries to calculate true business CPL.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any


class CPLLedger:
    @staticmethod
    def load_inquiries_csv(csv_path: str | Path, start_date: str | None = None, end_date: str | None = None) -> list[dict[str, Any]]:
        """Load standardized inquiries CSV."""
        path = Path(csv_path)
        if not path.is_file():
            return []

        inquiries = []
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dt = row.get("date", "").strip()
                if start_date and dt < start_date:
                    continue
                if end_date and dt > end_date:
                    continue

                # Auto classify channel / invalid
                channel = row.get("channel", "Unknown").strip()
                content = row.get("content", "").strip()
                is_invalid = "无效" in channel or row.get("status", "").lower() in ["invalid", "spam"]
                
                inquiries.append({
                    "seq": row.get("seq", len(inquiries) + 1),
                    "date": dt,
                    "channel": channel,
                    "name": row.get("name", "Unknown").strip(),
                    "country": row.get("country", "Unknown").strip(),
                    "content": content,
                    "is_valid": not is_invalid,
                })
        return inquiries

    @staticmethod
    def calculate_cpl_metrics(ad_spend_usd: float, inquiries: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate overall CPL and distribution breakdowns."""
        valid_inquiries = [x for x in inquiries if x["is_valid"]]
        valid_count = len(valid_inquiries)
        cpl_usd = round(ad_spend_usd / valid_count, 2) if valid_count > 0 else 0.0

        channel_dist = defaultdict(int)
        country_dist = defaultdict(int)
        for item in valid_inquiries:
            channel_dist[item["channel"]] += 1
            country_dist[item["country"]] += 1

        return {
            "total_spend_usd": round(ad_spend_usd, 2),
            "total_raw_leads": len(inquiries),
            "valid_leads_count": valid_count,
            "cpl_usd": cpl_usd,
            "channel_distribution": dict(sorted(channel_dist.items(), key=lambda x: x[1], reverse=True)),
            "country_distribution": dict(sorted(country_dist.items(), key=lambda x: x[1], reverse=True)),
        }
