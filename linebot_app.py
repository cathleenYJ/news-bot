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
from concurrent.futures import ThreadPoolExecutor

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
        # Follow redirects for links
        response = requests.get(article['url'], headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
        real_url = response.url
        art = Article(real_url)
        art.download()
        art.parse()
        if art.text.strip() == "":
            summary = "無法生成摘要"
        else:
            # 針對中文內容調整摘要參數
            summary = summarizer.summarize(art.text, ratio=0.1, words=30)
            # 如果摘要仍然太長，手動截斷到合理長度
            if len(summary) > 150:
                summary = summary[:150] + "..."
        
        news_item = f"📰 標題: {article['title']} (來源: {article['source']})\n🔗 連結: {real_url}\n📑 新聞摘要: {summary}\n"
        return news_item
    except Exception as e:
        return f"Error processing {article['url']}: {e}\n"

def get_intel_news():
    sources = [
        {'name': 'Intel', 'url': 'https://newsroom.intel.com/zh-tw/feed/'}
    ]
    
    articles = []
    for source in sources:
        response = requests.get(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
        feed = feedparser.parse(response.text)
        for entry in feed.entries[:20]:  # 取前20篇文章來篩選，確保有足夠的選擇
            title = entry.title
            link = entry.link
            articles.append({'title': title, 'url': link, 'source': source['name']})

    # 並行處理文章
    news_list = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_article, article) for article in articles]
        for future in futures:
            news_item = future.result()
            news_list.append(news_item)

    return news_list

def get_keyword_filtered_news(news_list, keywords, target_count=5):
    """篩選包含關鍵字的新聞，返回最新的指定數量文章"""
    filtered_news = []
    
    for news_item in news_list:
        if news_item.strip() and not news_item.startswith("Error"):
            # 檢查是否包含關鍵字
            if any(keyword.lower() in news_item.lower() for keyword in keywords):
                filtered_news.append(news_item.strip())
                # 達到目標數量就停止
                if len(filtered_news) >= target_count:
                    break
    
    return filtered_news

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
    keywords = ["gpu", "電腦", "ai", "workstation", "顯卡"]
    
    if user_message == "news":
        # 獲取所有新聞並篩選包含關鍵字的5篇
        all_news = get_intel_news()
        final_news = get_keyword_filtered_news(all_news, keywords, target_count=5)
        
        if final_news:
            # 一篇一篇發送
            for news_item in final_news:
                line_bot_api.push_message(event.source.user_id, TextSendMessage(text=news_item))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="目前沒有找到包含關鍵字的新聞")
            )
            
    elif any(keyword in user_message for keyword in keywords):
        # 篩選包含特定關鍵字的新聞
        all_news = get_intel_news()
        filtered_news = []
        for news_item in all_news:
            if news_item.strip() and any(keyword.lower() in news_item.lower() for keyword in keywords):
                filtered_news.append(news_item.strip())
                # 達到目標數量就停止
                if len(filtered_news) >= 5:
                    break
        
        if filtered_news:
            # 一篇一篇發送
            for news_item in filtered_news:
                line_bot_api.push_message(event.source.user_id, TextSendMessage(text=news_item))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="目前沒有找到相關關鍵字的新聞")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請發送 'news' 來獲取最新包含關鍵字的 Intel 新聞，或發送關鍵字 (GPU、電腦、AI、workstation、顯卡) 來搜尋相關新聞")
        )

if __name__ == "__main__":
    app.run(debug=True)