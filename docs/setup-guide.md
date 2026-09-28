# Google API & OAuth 凭据配置实战指南 (Step-by-Step Setup Guide)

本文档将手把手指导您完成 Google Cloud OAuth 2.0 桌面凭据、Google Ads Developer Token 以及相关媒体资源 ID 的获取与配置。

---

## 步骤一：创建 Google Cloud 项目并启用 API

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)。
2. 新建或选择一个项目（如 `my-b2b-analytics`）。
3. 导航至 **API 和服务 (APIs & Services) > 库 (Library)**，依次搜索并**启用 (Enable)** 以下 3 个 API：
   * **Google Ads API**
   * **Google Analytics Data API** (用于 GA4)
   * **Google Search Console API** (用于 GSC)

---

## 步骤二：配置 OAuth 同意屏幕 (Consent Screen)

1. 导航至 **API 和服务 > OAuth 同意屏幕**。
2. 用户类型选择 **外部 (External)**，点击创建。
3. 填写应用名称（如 `Growth Analytics Engine`）和您的开发者支持邮箱。
4. **作用域 (Scopes)**：添加以下 3 个核心权限：
   * `https://www.googleapis.com/auth/analytics.readonly`
   * `https://www.googleapis.com/auth/webmasters.readonly`
   * `https://www.googleapis.com/auth/adwords`
5. **测试用户 (Test Users)**：在发布前，将您用于登录 Google Ads 和 GA4 的 Gmail/Google Workspace 账号添加到测试用户列表中。

---

## 步骤三：创建 OAuth 2.0 凭据 (Desktop App)

1. 导航至 **API 和服务 > 凭据 (Credentials)**。
2. 点击 **创建凭据 (Create Credentials) > OAuth 客户端 ID (OAuth Client ID)**。
3. 应用类型必须选择：**桌面应用 (Desktop App)**。
4. 名称可填写 `Desktop Analytics Client`，点击创建。
5. 点击下载 JSON 文件，重命名并放置在本地项目路径，例如：
   `./credentials/client_secret.json`。

---

## 步骤四：获取 Google Ads 开发者令牌 (Developer Token)

1. 使用拥有 **MCC 管理员账号 (Manager Account)** 的 Google 账号登录 Google Ads。
2. 点击右上角 **工具和设置 (Tools & Settings) > 开发者令牌 (Developer Token)**。
3. 申请开发者令牌（测试级访问权限 Test Access 即可满足日常拉取与操作需求）。
4. 获得一个 22 位的字符串（形如 `AbCdEf123456GhIjKl7890`）。
5. 将该令牌保存为纯文本文件：
   `./credentials/developer-token.txt`。

---

## 步骤五：配置环境变量与首次一键授权

1. 将 `.env.example` 复制为 `.env`：
   ```bash
   cp .env.example .env
   ```
2. 编辑 `.env` 文件，填入您的实际路径与客户 ID：
   ```ini
   GOOGLE_OAUTH_CLIENT_FILE="./credentials/client_secret.json"
   GOOGLE_TOKEN_FILE="./credentials/token.json"
   GOOGLE_ADS_DEVELOPER_TOKEN_FILE="./credentials/developer-token.txt"
   GOOGLE_ADS_CUSTOMER_ID="1234567890"  # 您的 10 位 Google Ads 账号 ID
   GA4_PROPERTY_ID="123456789"          # 您的 GA4 媒体资源 ID
   GSC_SITE_URL="sc-domain:example.com" # 您的 GSC 站点标识
   ```
3. 运行一键体检与授权命令：
   ```bash
   python cli/doctor.py --reauthorize
   ```
4. 此时浏览器会自动弹出 Google 官方授权窗口，登录您的管理账号并点击“允许”。
5. 系统将自动生成 `./credentials/token.json`，以后所有操作均无需再次登录，支持完全自动化静默运行！
