# -*- coding: utf-8 -*-
"""
Safe Negative Keyword Injection CLI.
Appends negative keywords to a Google Ads Shared Negative List via REST API.
Enforces pre-check deduplication and post-write verification assertions.
Usage:
  python cli/inject_negatives.py --list-id 12244195948 --keywords "bad term 1" "bad competitor"
  python cli/inject_negatives.py --keywords "sample phrase" --match-type EXACT
"""

import argparse
import os
import sys
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
    parser = argparse.ArgumentParser(description="Safely inject negative keywords to a shared set")
    parser.add_argument("--list-id", type=str, help="Target shared set ID (or reads GOOGLE_ADS_SHARED_NEGATIVE_LIST_ID)")
    parser.add_argument("--keywords", nargs="+", required=True, help="One or more negative keywords to add")
    parser.add_argument("--match-type", default="PHRASE", choices=["PHRASE", "EXACT", "BROAD"], help="Match type (default: PHRASE)")
    args = parser.parse_args()

    shared_set_id = args.list_id or os.environ.get("GOOGLE_ADS_SHARED_NEGATIVE_LIST_ID")
    if not shared_set_id:
        print("[ERROR] Shared negative list ID must be provided via --list-id or GOOGLE_ADS_SHARED_NEGATIVE_LIST_ID env.")
        sys.exit(1)

    creds = load_credentials(credential_paths_from_env())
    client = GoogleAdsClient(creds, config_from_env())

    items = [{"text": kw.strip().strip('"').strip("'"), "match_type": args.match_type} for kw in args.keywords if kw.strip()]

    print("=" * 75)
    print(f"Injecting Negative Keywords into Shared Set: {shared_set_id}")
    print(f"Candidate words: {[x['text'] for x in items]} ({args.match_type})")
    print("=" * 75)

    try:
        result = client.inject_negative_keywords(shared_set_id, items)
        if result["status"] == "SKIPPED":
            print(f"Notice: {result['message']}. Total items in list: {result['total_count']}")
        else:
            print("\n[SUCCESS] Negative keywords successfully injected and verified via API!")
            print(f"  - Added Count: {result['added_count']}")
            print(f"  - Total Before: {result['before_count']} --> Total After: {result['after_count']}")
            print("  - Verified Created Items:")
            for it in result["verified_items"]:
                print(f"    * '{it['text']}' (Match: {it['match_type']}, ID: {it['criterion_id']})")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Injection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
