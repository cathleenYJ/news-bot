# News Bot 部署指南

## Render 部署

### 1. 準備工作
- 確保所有代碼已推送到 GitHub
- 確保 `requirements.txt` 包含所有依賴
- 設置環境變數：`CHANNEL_ACCESS_TOKEN` 和 `CHANNEL_SECRET`

### 2. 在 Render 上創建 Web Service
1. 登入 [Render](https://render.com)
2. 點擊 "New" -> "Web Service"
3. 連接您的 GitHub 倉庫
4. 配置服務：
   - **Name**: news-bot-api
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python api/index.py`

### 3. 環境變數設置
在 Render 的 Environment 設置中添加：
- `CHANNEL_ACCESS_TOKEN`: 您的 Line Bot Channel Access Token
- `CHANNEL_SECRET`: 您的 Line Bot Channel Secret
- `PORT`: 10000 (Render 會自動設置)

### 4. 部署
點擊 "Create Web Service" 開始部署。

## 本地測試部署

```bash
# 設置環境變數
export CHANNEL_ACCESS_TOKEN="your_token"
export CHANNEL_SECRET="your_secret"
export PORT=8000

# 運行應用
python api/index.py
```

## 故障排除

### ModuleNotFoundError
如果遇到模塊導入錯誤，確保：
1. `__init__.py` 文件存在於項目根目錄
2. `api/index.py` 中的路徑設置正確
3. 所有依賴都在 `requirements.txt` 中

### Line Bot SDK 警告
目前使用的 Line Bot SDK 版本較舊，建議升級到 v3：
```bash
pip install line-bot-sdk==3.0.0
```

然後更新導入：
```python
from linebot.v3 import LineBotApi
from linebot.v3.webhook import WebhookHandler
```