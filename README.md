# B2B Growth Analytics & Ad Ops Skill 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![Google Ads API](https://img.shields.io/badge/Google%20Ads%20API-v25-orange.svg)](https://developers.google.com/google-ads/api)
[![GA4 Data API](https://img.shields.io/badge/GA4%20API-v1beta-yellow.svg)](https://developers.google.com/analytics/devguides/reporting/data/v1)

> **Enterprise-grade Google Ads, GA4, GSC analytics & automated negative keyword injection engine designed for B2B cross-border growth.**
> 专为 B2B 独立站与出海品牌打造的 Google 广告监控、搜索词审计、自动化排否注入与多渠道真实询盘（CPL）闭环操盘引擎。

---

## 💡 Background & Pain Points (为什么需要这套工具？)

很多出海独立站和 B2B 外贸团队在投放 Google Ads（尤其是 Performance Max 和搜索广告）时，普遍面临三大痛点：
1. **数据孤岛与黑盒消耗**：广告后台点击看似很多，但不知道到底搜了什么词进站，大量预算被海外低价同行产业带词、竞品工厂词、C端小配件词悄悄吃掉；
2. **排否操作繁琐且易误杀**：人工在后台一个个翻搜索词并手动加否词不仅效率低下，且容易误把“高意向初创品牌搜索词”误杀；
3. **转化率与真实获客脱节**：平台后台的转化数字与业务员实际收到的表单、邮件、WhatsApp 询盘长期对不上账，老板无法得知真实的单个询盘获客成本（True CPL）。

本项目将我们在生产一线沉淀的这套实战系统开源出来——**集成了 Google Ads API (REST v25)、GA4 官方接口、搜索词智能排查、自动化安全排否闭环、以及极简老板看板生成**。

不仅可作为人类运营的 CLI 生产力工具，更自带标准 `SKILL.md`，可直接赋能给 **Claude Code、Antigravity、Cursor、Codex 等 AI 编程智能体**！

---

## ✨ Features (核心亮点)

*   **⚡ 官方 API 底层直连**：直连 Google Ads REST v25 与 GA4 v1beta 接口，秒级调取展示、点击、花费、CPC、CTR 与细分转化。
*   **🎯 搜索词穿透与吸血词侦测**：自动抓取产生花费的真实买家搜索词，智能辨识海外竞品名、非目标产业带地名与非标杂质。
*   **🛡️ 自动化排否安全闭环**：通过 `sharedCriteria:mutate` 批量向共享否定词表注入否定词，内置**预检去重**与**写入后双向回读断言**，确保 100% 成功、零误改、零误删！
*   **🤝 真实询盘对账与综合 CPL 测算**：打通独立站表单、邮件、WhatsApp、小满 CRM 等真实有效线索台账，自动剔除推销垃圾，计算真实的地面真值获客成本 (CPL)。
*   **📊 极简老板图形对比看板**：基于原生 HTML+CSS 打造的轻量级对比看板（无任何外部 CDN 依赖，离线秒开，支持双柱对比与系列长条占比，打印自适应）。
*   **🤖 智能体原生适配 (Agent-Ready)**：内置 `SKILL.md`，任何支持 Skill 规范的 AI Agent 加载后即可自主操盘分析。

---

## 🏗️ Architecture (工程架构)

```text
b2b-growth-analytics-skill/
├── .env.example                  # 环境变量配置模板
├── SKILL.md                      # Agent 技能规范（供 AI 智能体自主调用）
├── requirements.txt              # 核心依赖清单
├── core/                         # 核心 API 与业务引擎
│   ├── google_auth.py            # OAuth 2.0 凭据加载、刷新与多 scope 保护
│   ├── google_api.py             # 统一底层 HTTP 传输与秘密脱敏拦截
│   ├── google_ads.py             # Google Ads 指标拉取、搜索词穿透、否定词 mutate 注入
│   ├── ga4.py                    # GA4 会话质量、关键事件与落地页穿透
│   ├── gsc.py                    # Google Search Console 自然搜索分析
│   └── cpl_ledger.py             # 真实询盘台账解析与 CPL 测算引擎
├── cli/                          # 开箱即用的一键命令行工具
│   ├── doctor.py                 # 一键环境体检与授权引导
│   ├── audit_search_terms.py     # 搜索词自动化穿透与建议排否
│   ├── inject_negatives.py       # 安全注入否定词与双向回读断言
│   └── generate_report.py        # 一键生成老板极简对比看板 (HTML)
├── templates/
│   └── boss_report_template.html # 极简可视化看板模板
└── docs/
    └── setup-guide.md            # 从零申请 Google 凭据教程
```

---

## 🚀 Quick Start (5 分钟快速上手)

### 1. 克隆与安装依赖

```bash
git clone https://github.com/zsthimself/b2b-growth-analytics-skill.git
cd b2b-growth-analytics-skill

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`：
```bash
cp .env.example .env
```
根据实际情况填入：
*   `GOOGLE_OAUTH_CLIENT_FILE`: 从 Google Cloud Console 下载的 OAuth 桌面客户端凭据；
*   `GOOGLE_ADS_DEVELOPER_TOKEN_FILE`: 你的 22 位 Google Ads 开发者令牌；
*   `GOOGLE_ADS_CUSTOMER_ID`: 你的 10 位 Google Ads 客户 ID；
*   `GA4_PROPERTY_ID`: 你的 GA4 媒体资源 ID。

*(详细申请指南请见 [docs/setup-guide.md](docs/setup-guide.md))*

### 3. 一键体检与授权

```bash
# 检查凭据与连通性（首次运行将自动弹出浏览器引导授权）
python cli/doctor.py --reauthorize
```

### 4. 核心功能调用

**① 审计最近 7 天的搜索词与吸血词**：
```bash
python cli/audit_search_terms.py --days 7
```

**② 安全批量注入否定词到共享词表**：
```bash
python cli/inject_negatives.py --keywords "competitor factory" "unwanted term" --match-type PHRASE
```

**③ 一键生成极简老板看板 (HTML)**：
```bash
python cli/generate_report.py --days 7 --brand-name "MyBrand" --output report.html
```

---

## 🛡️ Best Practices for B2B Paid Media (出海操盘实战守则)

1. **切忌误杀初创品牌词 (Protect Independent Brand Intent)**：
   * 在 B2B 外贸中，诸如 `create my own clothing brand`、`create fashion brand`、`low moq manufacturer` 看似像 C 端散客，但绝大多数是欧美独立新锐品牌的创始人！首批 50-100 件测试订单恰恰是利润最丰厚的订单，**严禁排否**。
2. **坚决封堵外地低价产业带与竞品 (Block Irrelevant Clusters)**：
   * 针对买家搜索非目标国家当地工厂（如买家搜索孟加拉、巴基斯坦、葡萄牙本地厂）、同行巨头或精密辅料配件（如成衣厂被搜索拉链、纽扣、毛球），应果断通过共享否定词表切断。
3. **双向断言与零误碰原则**：
   * 任何自动化修改必须以“只追加、不改动历史词”为原则，写入后必须通过 API 回查断言，保障账户算法稳定。

---

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。欢迎广大出海独立站创始人、外贸操盘手、开发者提交 Issue 与 PR 共同完善！
