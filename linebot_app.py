import requests
from newspaper import Article
from summa import summarizer
import feedparser
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
import os
from concurrent.futures import ThreadPoolExecutor

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# Line Bot 配置
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 單例翻譯器
translator = GoogleTranslator(source='auto', target='zh-TW')

def process_article(article):
    try:
        # Follow redirects for links
        response = requests.get(article['url'], headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
        real_url = response.url
        art = Article(real_url)
        art.download()
        art.parse()
        if art.text.strip() == "":
            summary = "無法生成摘要"
        else:
            summary = summarizer.summarize(art.text, ratio=0.2, words=50)
        
        # 翻譯到中文
        try:
            translated_title = translator.translate(article['title'])
            translated_summary = translator.translate(summary) if summary != "無法生成摘要" else summary
        except:
            translated_title = article['title']
            translated_summary = summary
        
        news_item = f"📰 標題: {translated_title} (來源: {article['source']})\n🔗 連結: {real_url}\n📑 新聞摘要: {translated_summary}\n"
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
            articles.append({'title': title, 'url': link, 'source': source['name']})

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