# News Bot - 多來源新聞 Line Bot

此專案整合多個科技新聞來源（Intel、AMD、NVIDIA、Tom's Hardware），自動抓取最新新聞，生成摘要，並通過 Line Bot 提供即時新聞服務。

## 功能特色

- **多來源新聞整合**：整合 Intel、AMD、NVIDIA、Tom's Hardware 等多家科技媒體
- **智能關鍵字篩選**：支援預設關鍵字和自訂關鍵字搜尋
- **自動摘要生成**：使用 NLP 技術生成文章摘要
- **Line Bot 整合**：支援即時聊天獲取新聞
- **來源均衡**：確保每個新聞來源都有代表性

## 技術架構

- **後端框架**：Flask + Line Bot SDK
- **新聞處理**：Newspaper3k + Summa (NLP 摘要)
- **資料來源**：RSS Feed + REST API
- **部署方式**：支援本地開發和雲端部署（Vercel/Heroku）

## 需求環境

- Python 3.8+
- 支援的作業系統：macOS, Linux, Windows

## 安裝步驟

1. **克隆專案**
   ```bash
   git clone <repository-url>
   cd news-bot
   ```

2. **創建虛擬環境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # 或在 Windows 上：venv\Scripts\activate
   ```

3. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

4. **環境配置**
   ```bash
   cp .env.example .env
   # 編輯 .env 文件，填入 Line Bot 的 Token 和 Secret
   ```

## 使用方法

### 本地開發

```bash
# 運行本地開發版本
python linebot_app.py
```

### 生產部署

專案支援多種部署方式：

#### Vercel 部署
- 將 `api/index.py` 部署為 serverless function
- Webhook URL 格式：`https://your-domain.vercel.app/api/index`

#### Heroku 部署
```bash
# 設定環境變數
heroku config:set CHANNEL_ACCESS_TOKEN=your_token
heroku config:set CHANNEL_SECRET=your_secret
heroku config:set PORT=5000
```

### Line Bot 設定

1. 前往 [Line Developers Console](https://developers.line.biz/)
2. 創建 Messaging API channel
3. 複製 Channel Access Token 和 Channel Secret 到 `.env` 文件
4. 設定 Webhook URL 指向您的部署域名 + `/callback`
5. 在 Line 中添加 Bot 為好友

### 聊天指令

- **發送 "news"**：獲取預設關鍵字的新聞（GPU、電腦、AI、workstation、顯卡）
- **發送單一關鍵字**：如 "CPU"、"記憶體" 等，獲取相關新聞
- **支援中文關鍵字**：如 "AI"、"顯卡" 等

## 專案結構

```
news-bot/
├── news_bot.py          # 核心邏輯模塊
│   ├── NewsProcessor    # 新聞處理類別
│   └── create_app()     # Flask 應用工廠
├── linebot_app.py       # 本地開發入口
├── api/
│   └── index.py         # 生產部署入口
├── requirements.txt     # Python 依賴
├── .env.example         # 環境變數範例
├── README.md           # 專案說明
└── .gitignore          # Git 忽略規則
```

## 開發說明

### 核心模塊

- **`news_bot.py`**：包含所有業務邏輯
  - `NewsProcessor` 類別處理新聞抓取和摘要
  - `create_app()` 函數創建 Flask 應用

### 新聞來源

目前支援的新聞來源：
- **Intel Newsroom** (RSS)
- **AMD Press Releases** (API)
- **NVIDIA Blogs** (WordPress API)
- **Tom's Hardware** (RSS)

### 關鍵字篩選邏輯

1. **來源層級篩選**：在抓取時就篩選關鍵字（預設關鍵字）
2. **內容層級篩選**：在處理後篩選關鍵字（自訂關鍵字）
3. **來源均衡**：確保每個來源至少有一篇新聞

## 注意事項

- 新聞抓取可能受到來源網站限制
- Line Bot 有訊息長度限制，新聞會分條發送
- 建議定期檢查新聞來源的 API 變化
- 生產環境建議使用環境變數管理敏感信息

## 授權

此專案僅供學習和個人使用，請遵守各新聞來源的使用條款。
