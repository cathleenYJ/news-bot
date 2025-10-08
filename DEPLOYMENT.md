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

## 內存優化

### 當前優化措施
- **限制並發數量**: 最多 3 個並發線程處理文章
- **限制文章數量**: 最多處理 10 篇文章
- **內存監控**: 添加了內存使用日誌
- **資源清理**: 處理完文章後清理內存
- **緩存機制**: 1小時內避免重複處理相同文章
- **文本限制**: 限制摘要處理的文本長度

### 監控內存使用
應用會在日誌中輸出內存使用情況：
```
開始獲取新聞，當前內存使用: 45.2 MB
RSS 文章數: 8，總文章數: 8
AMD 文章數: 5
NVIDIA 文章數: 5
最終處理文章數: 10，內存使用: 67.8 MB
處理完成，生成 8 條新聞，內存使用: 52.1 MB
```

### 如果仍然遇到內存問題
1. **檢查 Render 日誌** 查看具體的內存使用模式
2. **減少文章數量** 修改 `processors.py` 中的 `max_articles`
3. **降低並發數** 修改 `max_workers` 設置
4. **升級實例類型** 在 Render 中選擇更大的內存配置

## 故障排除

### ModuleNotFoundError
如果遇到模塊導入錯誤，確保：
1. `__init__.py` 文件存在於項目根目錄
2. `api/index.py` 中的路徑設置正確
3. 所有依賴都在 `requirements.txt` 中

### 內存不足錯誤
如果仍然遇到內存問題：
1. 檢查應用日誌中的內存使用情況
2. 考慮減少 `max_articles` 和 `max_workers`
3. 在 Render 中升級到更大的實例類型

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