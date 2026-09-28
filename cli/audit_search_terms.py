# -*- coding: utf-8 -*-
"""
Search Terms Audit & Negative Discovery CLI.
Audits actual search queries, highlights high-cost non-converting terms,
and detects potential competitor / irrelevant keywords.
Usage:
  python cli/audit_search_terms.py --days 7
  python cli/audit_search_terms.py --start-date 2026-09-20 --end-date 2026-09-27
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.google_auth import credential_paths_from_env, load_credentials
from core.google_ads import GoogleAdsClient, config_from_env


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    load_dotenv()
    parser = argparse.ArgumentParser(description="Audit Google Ads Search Terms")
    parser.add_argument("--days", type=int, default=7, help="Number of trailing days to audit (default: 7)")
    parser.add_argument("--start-date", type=str, help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, help="End date YYYY-MM-DD")
    parser.add_argument("--min-clicks", type=int, default=1, help="Min clicks filter (default: 1)")
    args = parser.parse_args()

    end_d = args.end_date or date.today().strftime("%Y-%m-%d")
    start_d = args.start_date or (date.today() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    creds = load_credentials(credential_paths_from_env())
    client = GoogleAdsClient(creds, config_from_env())

    print("=" * 85)
    print(f"Google Ads Search Terms Audit ({start_d} ~ {end_d})")
    print("=" * 85)

    terms = client.get_search_terms(start_d, end_d, min_clicks=args.min_clicks)
    if not terms:
        print("No search terms found in this window.")
        return

    total_cost = sum(t["cost"] for t in terms)
    total_clicks = sum(t["clicks"] for t in terms)
    total_conv = sum(t["conversions"] for t in terms)

    print(f"Summary: {len(terms)} queries | Total Cost: ${total_cost:.2f} | Total Clicks: {total_clicks} | Conversions: {total_conv}\n")
    print(f"{'Spend($)':<8} | {'Clicks':<6} | {'Impr':<6} | {'CPC':<7} | {'Conv':<6} | {'Campaign':<16} | {'Search Term'}")
    print("-" * 85)

    for t in terms[:40]:
        print(f"${t['cost']:>7.2f} | {t['clicks']:>6} | {t['impressions']:>6} | ${t['cpc']:>5.2f} | {t['conversions']:>6.1f} | {t['campaign_name'][:16]:<16} | {t['search_term']}")

    print("\n" + "=" * 85)
    print("Audit recommendations:")
    print("1. Review terms with high CPC and 0 conversions.")
    print("2. Check for overseas non-target manufacturing regions or competitor factory names.")
    print("3. Use 'cli/inject_negatives.py' to safely block unwanted terms.")
    print("=" * 85)


if __name__ == "__main__":
    main()
