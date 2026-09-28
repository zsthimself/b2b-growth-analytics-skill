# -*- coding: utf-8 -*-
"""
One-click Health Doctor for B2B Growth Analytics.
Checks credentials, tokens, Google Ads, GA4, and GSC connectivity.
Usage:
  python cli/doctor.py
  python cli/doctor.py --reauthorize
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure core package can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.google_auth import (
    credential_paths_from_env,
    load_credentials,
    run_interactive_authorization,
)
from core.google_ads import GoogleAdsClient, config_from_env
from core.ga4 import GA4Client
from core.gsc import GSCClient


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    load_dotenv()
    parser = argparse.ArgumentParser(description="Health Doctor for Google Analytics & Ads")
    parser.add_argument("--reauthorize", action="store_true", help="Launch interactive browser OAuth flow")
    args = parser.parse_args()

    paths = credential_paths_from_env()

    if args.reauthorize:
        print(f"Launching interactive OAuth consent flow...")
        creds = run_interactive_authorization(paths)
        print(f"Authorization successful! Token saved to: {paths.token_file}")
        return

    print("=" * 70)
    print("B2B Growth Analytics Health Check (Doctor)")
    print("=" * 70)

    # 1. Credentials Check
    print("\n1. Checking OAuth 2.0 Credentials...")
    try:
        creds = load_credentials(paths)
        print(f"  [PASS] OAuth token valid at: {paths.token_file}")
    except Exception as e:
        print(f"  [FAIL] Credentials error: {e}")
        print("  Hint: Run 'python cli/doctor.py --reauthorize' to authorize in browser.")
        return

    # 2. Google Ads API Check
    print("\n2. Checking Google Ads API Connectivity...")
    try:
        ads_config = config_from_env()
        ads_client = GoogleAdsClient(creds, ads_config)
        rows = ads_client.search_stream(
            "SELECT customer.id, customer.descriptive_name, customer.currency_code, customer.time_zone FROM customer LIMIT 1"
        )
        if rows:
            cust = rows[0].get("customer", {})
            print(f"  [PASS] Google Ads Connected! Customer: {cust.get('id')} ({cust.get('descriptiveName')}) | Currency: {cust.get('currencyCode')} | Timezone: {cust.get('timeZone')}")
        else:
            print(f"  [PASS] Connected to Google Ads customer: {ads_config.customer_id}")
    except Exception as e:
        print(f"  [WARN] Google Ads check failed: {e}")

    # 3. GA4 Check
    print("\n3. Checking Google Analytics 4 (GA4)...")
    try:
        ga4_client = GA4Client(creds)
        # Simple test query
        body = {
            "dateRanges": [{"startDate": "7daysAgo", "endDate": "yesterday"}],
            "metrics": [{"name": "sessions"}],
        }
        res = ga4_client.run_report(body)
        print(f"  [PASS] GA4 Connected! Property ID: {ga4_client.property_id}")
    except Exception as e:
        print(f"  [WARN] GA4 check failed: {e}")

    # 4. GSC Check
    print("\n4. Checking Google Search Console (GSC)...")
    try:
        gsc_client = GSCClient(creds)
        res = gsc_client.query_search_analytics("7daysAgo", "yesterday", row_limit=1)
        print(f"  [PASS] GSC Connected! Site URL: {gsc_client.site_url}")
    except Exception as e:
        print(f"  [WARN] GSC check failed: {e}")

    print("\n" + "=" * 70)
    print("Health check completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
