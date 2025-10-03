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
import random

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

def scrape_amd_news():
    """使用 AMD API 獲取新聞（帶關鍵字搜尋）"""
    import json
    articles = []
    try:
        api_url = 'https://xilinxcomprode2rjoqok.org.coveo.com/rest/search/v2?organizationId=xilinxcomprode2rjoqok'
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'authorization': 'Bearer xx5ee91b6a-e227-4c6f-83f2-f2120ca3509e',
            'content-type': 'application/json',
            'origin': 'https://www.amd.com',
            'referer': 'https://www.amd.com/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        # API 請求資料 - 使用關鍵字搜尋
        # Coveo API 使用 OR 邏輯搜尋多個關鍵字
        data = {
            "locale": "zh-TW",
            "cq": "(@amd_result_type==\"Press Releases\")",
            "context": {"amd_lang": "zh-TW"},
            "q": "GPU OR AI OR 顯卡 OR workstation OR 電腦",  # 在 API 層級就篩選關鍵字
            "sortCriteria": "@amd_release_date descending",
            "numberOfResults": 10,
            "firstResult": 0
        }
        
        response = requests.post(api_url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            results = result.get('results', [])
            
            for item in results[:5]:
                title = item.get('title', '').strip()
                link = item.get('clickUri', '') or item.get('uri', '')
                
                if title and link:
                    articles.append({'title': title, 'url': link, 'source': 'AMD'})
        
    except Exception as e:
        print(f"Error fetching AMD news: {e}")
    
    return articles

def scrape_nvidia_news():
    """使用 NVIDIA WordPress API 獲取新聞（帶關鍵字搜尋）"""
    import json
    articles = []
    
    # WordPress API 的 search 參數只能搜尋單一關鍵字
    # 所以我們搜尋多個關鍵字，合併結果
    keywords = ['GPU', 'AI', '顯卡']  # 選擇最重要的關鍵字
    all_posts = []
    seen_urls = set()
    
    try:
        api_url = 'https://blogs.nvidia.com.tw/wp-json/wp/v2/posts'
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://www.nvidia.com',
            'referer': 'https://www.nvidia.com/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        # 對每個關鍵字進行搜尋
        for keyword in keywords:
            try:
                params = {
                    '_embed': 'true',
                    'per_page': 5,
                    'page': 1,
                    'search': keyword  # 使用關鍵字搜尋
                }
                
                response = requests.get(api_url, headers=headers, params=params, timeout=15)
                
                if response.status_code == 200:
                    posts = response.json()
                    
                    for post in posts:
                        link = post.get('link', '')
                        # 去重：避免同一篇文章被多個關鍵字搜到
                        if link and link not in seen_urls:
                            seen_urls.add(link)
                            title = post.get('title', {}).get('rendered', '').strip()
                            if title:
                                # 移除 HTML 標籤
                                import re
                                title = re.sub('<.*?>', '', title)
                                all_posts.append({'title': title, 'url': link, 'source': 'NVIDIA', 'date': post.get('date', '')})
            except Exception as e:
                print(f"Error searching NVIDIA with keyword '{keyword}': {e}")
                continue
        
        # 按日期排序，取最新的 5 篇
        if all_posts:
            all_posts.sort(key=lambda x: x.get('date', ''), reverse=True)
            articles = [{'title': p['title'], 'url': p['url'], 'source': p['source']} for p in all_posts[:5]]
        
    except Exception as e:
        print(f"Error fetching NVIDIA news: {e}")
    
    return articles

def get_intel_news(keywords=None, filter_at_source=True):
    """獲取多來源新聞，可選擇在抓取階段進行關鍵字篩選"""
    if keywords is None:
        keywords = ["gpu", "電腦", "ai", "workstation", "顯卡"]
    
    # RSS feed 來源
    rss_sources = [
        {'name': 'Intel', 'url': 'https://newsroom.intel.com/zh-tw/feed/', 'type': 'rss'},
        {'name': 'Tom\'s Hardware', 'url': 'https://www.tomshardware.com/feeds/all', 'type': 'rss'},
    ]
    
    articles = []
    
    # 從 RSS feed 抓取
    for source in rss_sources:
        try:
            response = requests.get(source['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            feed = feedparser.parse(response.text)
            
            if filter_at_source and keywords:
                # 篩選包含關鍵字的文章
                filtered_entries = []
                for entry in feed.entries:
                    title = entry.title
                    # 檢查標題是否包含關鍵字
                    if any(keyword.lower() in title.lower() for keyword in keywords):
                        filtered_entries.append(entry)
                
                # 從篩選後的文章中取最多5篇
                entries_to_process = filtered_entries[:5]
            else:
                # 不篩選，取前5篇
                entries_to_process = feed.entries[:5]
            
            # 處理選定的文章
            for entry in entries_to_process:
                title = entry.title
                link = entry.link
                articles.append({'title': title, 'url': link, 'source': source['name']})
        except Exception as e:
            print(f"Error fetching from {source['name']}: {e}")
            continue
    
    # 從網頁爬取 AMD 和 NVIDIA 新聞
    try:
        amd_articles = scrape_amd_news()
        articles.extend(amd_articles[:5])
    except Exception as e:
        print(f"Error adding AMD articles: {e}")
    
    try:
        nvidia_articles = scrape_nvidia_news()
        articles.extend(nvidia_articles[:5])
    except Exception as e:
        print(f"Error adding NVIDIA articles: {e}")
    
    # 並行處理文章
    news_list = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_article, article) for article in articles]
        for future in futures:
            try:
                news_item = future.result(timeout=30)
                news_list.append(news_item)
            except Exception as e:
                print(f"Error processing article: {e}")
                continue

    return news_list

def get_keyword_filtered_news(news_list, keywords, target_count=5, already_filtered=False):
    """篩選包含關鍵字的新聞，確保每個來源至少一篇，然後隨機補充到指定數量
    
    Args:
        news_list: 新聞列表
        keywords: 關鍵字列表
        target_count: 目標數量
        already_filtered: 是否已經在來源層級進行過關鍵字篩選
    """
    import random

    # 按來源分組新聞
    source_groups = {}
    for news_item in news_list:
        if news_item.strip() and not news_item.startswith("Error"):
            # 如果已經在來源層級篩選過，就不需要再次檢查關鍵字
            if already_filtered or any(keyword.lower() in news_item.lower() for keyword in keywords):
                # 從新聞中提取來源
                source_start = news_item.find("(來源: ") + 5
                source_end = news_item.find(")", source_start)
                if source_start > 4 and source_end > source_start:
                    source = news_item[source_start:source_end]
                    if source not in source_groups:
                        source_groups[source] = []
                    source_groups[source].append(news_item.strip())

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
    default_keywords = ["gpu", "電腦", "ai", "workstation", "顯卡"]

    if user_message == "news":
        # 獲取所有新聞並篩選包含預設關鍵字的5篇（隨機，但確保每個來源至少一篇）
        # RSS 來源已在抓取時進行關鍵字篩選
        all_news = get_intel_news()
        final_news = get_keyword_filtered_news(all_news, default_keywords, target_count=5, already_filtered=True)

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
            # 根據用戶輸入的關鍵字查詢新聞（使用傳統篩選模式，因為是自訂關鍵字）
            all_news = get_intel_news(keywords=[user_keyword], filter_at_source=False)  # 不使用來源層級篩選
            final_news = get_keyword_filtered_news(all_news, [user_keyword], target_count=5, already_filtered=False)

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
                TextSendMessage(text="請發送 'news' 來獲取最新包含 GPU、電腦、AI、workstation、顯卡 關鍵字的隨機5篇新聞，或發送任何單一關鍵字來搜尋相關新聞")
            )

if __name__ == "__main__":
    app.run(debug=True)