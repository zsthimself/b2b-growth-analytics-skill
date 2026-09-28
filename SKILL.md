---
name: b2b-growth-analytics-skill
description: Enterprise-grade Google Ads, GA4, GSC analytics & automated negative keyword injection engine for B2B cross-border growth.
---

# B2B Growth Analytics & Ad Ops Skill

This skill equips any AI Agent (Antigravity, Claude Code, Cursor, Codex) to act as a senior Growth Marketing Engineer & Media Buyer.
It connects directly to Google Ads API (REST v25), Google Analytics 4 (Data API), Google Search Console, and CRM Lead Ledgers to monitor ad spend, detect non-converting search terms, safely inject negative keywords, and report true B2B Cost Per Lead (CPL).

---

## 1. When to Activate This Skill

Use this skill when the user asks to:
1. **Check ad performance / spend / CPC**: e.g., "查看过去几天的广告数据", "看下出海广告表现", "广告花费怎么样";
2. **Audit search queries & wasted budget**: e.g., "分析搜索词", "有没有跑偏的吸血词", "看下 PMax 搜了什么词";
3. **Add negative keywords (排否)**: e.g., "把这几个词加到否词表", "排否", "过滤竞品和无效词";
4. **Reconcile conversion tracking & leads**: e.g., "今天收到几笔询盘", "算一下真实 CPL 获客成本", "核对 GA4 关键事件";
5. **Generate owner-level growth reports**: e.g., "出周报", "生成老板看板", "做一份广告对比分析".

---

## 2. Core Capabilities & CLI Tools

All CLI tools read configuration from `.env` and can be invoked directly from the terminal:

### 1) Health Check & Re-authorization
Verify API connectivity, token validity, and Google Ads customer accounts:
```bash
python cli/doctor.py
# If token is expired or scopes need updating:
python cli/doctor.py --reauthorize
```

### 2) Search Terms Audit & Waste Detection
Scan trailing N days of search queries, highlighting spend, clicks, CPC, and conversions:
```bash
python cli/audit_search_terms.py --days 7
python cli/audit_search_terms.py --start-date 2026-09-20 --end-date 2026-09-27
```

### 3) Automated Safe Negative Keyword Injection
Safely append phrase/exact negative keywords to a shared negative list via Google Ads REST API v25.
Enforces **pre-flight deduplication** and **post-write read-back assertions** to guarantee 0 accidental deletions or modifications:
```bash
python cli/inject_negatives.py --keywords "competitor factory" "unwanted term" --match-type PHRASE
# Or specify a custom shared list ID:
python cli/inject_negatives.py --list-id 12244195948 --keywords "bad query" --match-type PHRASE
```

### 4) Generate Owner Comparison Dashboard (HTML)
Renders a lightweight, standalone, responsive visual comparison report (pure CSS, no CDN dependencies):
```bash
python cli/generate_report.py --days 7 --brand-name "MyBrand" --output report.html
```

---

## 3. Decision Framework & Guardrails

When auditing and optimizing B2B ads:

1. **Protect Independent Brand Intent (切忌误杀初创品牌词)**:
   - Queries like `create my own clothing brand`, `create fashion brand`, `custom clothing with low moq` often look like casual consumers to junior buyers, but in B2B foreign trade, these are typically founders of independent labels placing initial 50-100 unit sample/bulk orders. **Never negate these unless verified spam.**
2. **Strictly Block Parasitic Competitor & Irrelevant Regional Traffic**:
   - Target overseas regional clusters searching for local factories (e.g., `sialkot`, `portugal factory`, `sri lanka manufacturers` when manufacturing in China).
   - Competitor manufacturer names and B2C accessory parts (e.g., zippers, pompoms, raw fabrics when selling finished garments).
3. **Idempotent & Safe Mutation Protocol**:
   - Always read the existing negative list before mutating.
   - Assert `len(after) == len(before) + len(new_added)`.
   - Never touch existing positive keywords or bidding strategies without explicit user consent.
