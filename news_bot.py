import requests
from newspaper import Article
from summa import summarizer
import feedparser
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import os
import re
from concurrent.futures import ThreadPoolExecutor
import random
from processors import NewsProcessor
from container import NewsBotContainer

# 常量定義
DEFAULT_USER_AGENT = 'Mozilla/5.0'
FULL_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
DEFAULT_KEYWORDS = ["gpu", "電腦", "ai", "workstation", "顯卡"]
REQUEST_TIMEOUT = 15
RSS_TIMEOUT = 10

def create_app():
    """創建並配置 Flask 應用"""
    # 載入環境變數
    load_dotenv()

    app = Flask(__name__)

    # Line Bot 配置
    CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
    CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(CHANNEL_SECRET)

    # 創建新聞處理器實例
    container = NewsBotContainer()
    news_processor = container.create_news_processor()

    @app.route("/callback", methods=['POST'])
    def callback():
        signature = request.headers['X-Line-Signature']
        body = request.get_data(as_text=True)
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)
        return 'OK'

    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_message = event.message.text.lower()
        default_keywords = DEFAULT_KEYWORDS

        if user_message == "news":
            # 獲取每個來源1則最符合預設關鍵字的新聞（總共最多4篇）
            final_news = news_processor.get_intel_news(keywords=default_keywords, filter_at_source=True)

            if final_news:
                # 一篇一篇發送
                for news_item in final_news:
                    line_bot_api.push_message(event.source.user_id, TextSendMessage(text=news_item))
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="目前沒有找到包含關鍵字的新聞")
                )

        else:
            # 檢查用戶輸入是否是一個關鍵字（單詞）
            user_keyword = user_message.strip()
            if user_keyword and len(user_keyword.split()) == 1:  # 確保是單一關鍵字
                # 根據用戶輸入的關鍵字查詢新聞，使用來源層級篩選
                final_news = news_processor.get_intel_news(keywords=[user_keyword], filter_at_source=True)

                if final_news:
                    # 一篇一篇發送
                    for news_item in final_news:
                        line_bot_api.push_message(event.source.user_id, TextSendMessage(text=news_item))
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(f"目前沒有找到包含關鍵字「{user_keyword}」的新聞")
                    )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="請發送 'news' 來獲取每個來源1則最相關的新聞，或發送任何單一關鍵字來搜尋相關新聞")
                )

    return app