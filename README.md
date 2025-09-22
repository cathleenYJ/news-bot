# Intel 新聞抓取器與 Line Bot

此專案從官方 Intel 新聞室 RSS feed 獲取最新的 Intel 新聞文章，提取文章內容，並生成摘要。可以通過命令行運行或整合到 Line Bot 中。

## 功能

- 獲取最近的 Intel 新聞文章
- 下載並解析文章內容
- 使用提取式摘要生成文本摘要
- 以帶有 emoji 的格式輸出
- 整合 Line Bot，通過聊天獲取新聞

## 需求

- Python 3.7+
- requests
- beautifulsoup4
- lxml
- newspaper3k
- summa
- feedparser
- flask
- line-bot-sdk

## 安裝

1. 克隆或下載專案。
2. 創建虛擬環境：`python -m venv venv`
3. 激活環境：`source venv/bin/activate` (在 macOS/Linux 上)
4. 安裝依賴：`pip install requests beautifulsoup4 lxml newspaper3k summa feedparser flask line-bot-sdk python-dotenv`

## 使用方法

### 命令行運行

運行腳本：`python intel_news_scraper.py`

輸出格式為：

📰 標題: [文章標題] (來源: [來源])
🔗 連結: [文章連結]
📑 新聞摘要: [摘要]

### Line Bot 設定

1. 在 [Line Developers](https://developers.line.biz/) 創建 Messaging API channel。
2. 獲取 Channel Access Token 和 Channel Secret。
3. 複製 `.env.example` 到 `.env`，並填入您的 Token 和 Secret。
4. 部署應用到伺服器（如 Heroku, AWS 等），並設定 Webhook URL 為 `https://your-domain/callback`。
5. 在 Line 中添加 Bot 為好友，發送 "新聞" 來獲取最新 Intel 新聞。

## 注意事項

- 腳本自動從 Intel RSS feed 獲取最新文章。
- 如果文章無法抓取，會顯示警告並跳過摘要。
- Line Bot 會將新聞分割成多條訊息發送，以避免長度限制。
