# -*- coding: utf-8 -*-
"""
Generate Boss-level Visual Weekly/Monthly Growth Report.
Renders standalone, responsive HTML comparison dashboard without external CDN scripts.
Usage:
  python cli/generate_report.py --days 7 --output report.html
"""

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from jinja2 import Template

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.google_auth import credential_paths_from_env, load_credentials
from core.google_ads import GoogleAdsClient, config_from_env
from core.cpl_ledger import CPLLedger


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    load_dotenv()
    parser = argparse.ArgumentParser(description="Generate Visual Growth Report")
    parser.add_argument("--days", type=int, default=7, help="Number of trailing days (default: 7)")
    parser.add_argument("--start-date", type=str, help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, help="End date YYYY-MM-DD")
    parser.add_argument("--brand-name", type=str, default="Brand", help="Brand/Store name")
    parser.add_argument("--output", type=str, default="growth_report.html", help="Output HTML filepath")
    args = parser.parse_args()

    end_d = args.end_date or date.today().strftime("%Y-%m-%d")
    start_d = args.start_date or (date.today() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    creds = load_credentials(credential_paths_from_env())
    ads_client = GoogleAdsClient(creds, config_from_env())

    print(f"Generating Growth Report ({start_d} ~ {end_d})...")

    # Fetch Google Ads data
    campaign_metrics = ads_client.get_campaign_metrics(start_d, end_d)
    top_terms = ads_client.get_search_terms(start_d, end_d, min_clicks=1)[:15]

    # Aggregate campaigns
    camp_summary = {}
    total_cost = 0.0
    total_clicks = 0
    total_impr = 0
    total_conv = 0.0

    for m in campaign_metrics:
        cid = m["campaign_id"]
        if cid not in camp_summary:
            camp_summary[cid] = {
                "campaign_name": m["campaign_name"],
                "status": m["status"],
                "channel_type": m["channel_type"],
                "cost": 0.0,
                "clicks": 0,
                "impressions": 0,
                "conversions": 0.0,
            }
        camp_summary[cid]["cost"] += m["cost"]
        camp_summary[cid]["clicks"] += m["clicks"]
        camp_summary[cid]["impressions"] += m["impressions"]
        camp_summary[cid]["conversions"] += m["conversions"]

        total_cost += m["cost"]
        total_clicks += m["clicks"]
        total_impr += m["impressions"]
        total_conv += m["conversions"]

    campaigns_list = []
    for c in camp_summary.values():
        c["cost"] = round(c["cost"], 2)
        c["cpc"] = round(c["cost"] / c["clicks"], 2) if c["clicks"] > 0 else 0.0
        c["ctr"] = f"{round(c['clicks'] / c['impressions'] * 100, 2)}%" if c["impressions"] > 0 else "0%"
        campaigns_list.append(c)
    campaigns_list.sort(key=lambda x: x["cost"], reverse=True)

    # Inquiries ground truth
    inquiry_path = os.environ.get("INQUIRIES_DATA_PATH", "./data/inquiries.csv")
    raw_inquiries = CPLLedger.load_inquiries_csv(inquiry_path, start_d, end_d)
    cpl_stats = CPLLedger.calculate_cpl_metrics(total_cost, raw_inquiries)

    # Render template
    template_path = Path(__file__).parent.parent / "templates" / "boss_report_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        tpl = Template(f.read())

    days_count = max(1, (datetime.strptime(end_d, "%Y-%m-%d") - datetime.strptime(start_d, "%Y-%m-%d")).days + 1)
    avg_cpc = round(total_cost / total_clicks, 2) if total_clicks > 0 else 0.0

    html_out = tpl.render(
        brand_name=args.brand_name,
        start_date=start_d,
        end_date=end_d,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_cost=round(total_cost, 2),
        daily_avg_cost=round(total_cost / days_count, 2),
        total_clicks=total_clicks,
        avg_cpc=avg_cpc,
        valid_leads=cpl_stats["valid_leads_count"],
        raw_leads=cpl_stats["total_raw_leads"],
        cpl_usd=cpl_stats["cpl_usd"],
        cpl_cny=round(cpl_stats["cpl_usd"] * 7.1, 1),
        campaigns=campaigns_list,
        top_terms=top_terms,
        lead_channels=cpl_stats["channel_distribution"],
    )

    out_file = Path(args.output).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"[SUCCESS] Growth report successfully generated at: {out_file}")


if __name__ == "__main__":
    main()
