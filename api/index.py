import requests
from summa import summarizer
import feedparser
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import os
from concurrent.futures import ThreadPoolExecutor
import re

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# Line Bot 配置
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def process_article(article):
    try:
        summary = article.get('summary', '')
        # Clean HTML tags
        summary = re.sub(r'<[^>]+>', '', summary)
        if summary.strip() == "":
            summary = "無法生成摘要"
        else:
            summary = summarizer.summarize(summary, ratio=0.2, words=50)
        
        news_item = f"📰 標題: {article['title']} (來源: {article['source']})\n🔗 連結: {article['url']}\n📑 新聞摘要: {summary}\n"
        return news_item
    except Exception as e:
        return f"Error processing {article['url']}: {e}\n"

def get_intel_news():
    sources = [
        {'name': 'Intel', 'url': 'https://newsroom.intel.com/feed/'}
    ]
    
    articles = []
    for source in sources:
        response = requests.get(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
        feed = feedparser.parse(response.text)
        for entry in feed.entries[:5]:  # Get first 5 articles per source
            title = entry.title
            link = entry.link
            summary = getattr(entry, 'summary', '')
            articles.append({'title': title, 'url': link, 'source': source['name'], 'summary': summary})

    # 並行處理文章
    news_list = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_article, article) for article in articles]
        for future in futures:
            news_item = future.result()
            news_list.append(news_item)

    return "\n".join(news_list)

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
    if event.message.text.lower() == "新聞":
        news_list = get_intel_news().split('\n\n')  # 分割成每則新聞
        for news_item in news_list:
            if news_item.strip():  # 確保不發送空訊息
                line_bot_api.push_message(event.source.user_id, TextSendMessage(text=news_item.strip()))
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請發送 '新聞' 來獲取最新 Intel 新聞")
        )

if __name__ == "__main__":
    app.run(debug=True)