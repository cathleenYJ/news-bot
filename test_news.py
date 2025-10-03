#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from newspaper import Article
from summa import summarizer
import feedparser
from concurrent.futures import ThreadPoolExecutor

def process_article(article):
    try:
        print(f"正在處理文章: {article['title'][:50]}...")
        # Follow redirects for links
        response = requests.get(article['url'], headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True, timeout=15)
        real_url = response.url
        art = Article(real_url)

        # 增加 newspaper3k 的超時時間
        art.config.browser_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        art.config.request_timeout = 15  # 增加到 15 秒

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
        # 記錄詳細錯誤訊息
        error_msg = f"Error processing {article['url']}: {str(e)}"
        print(f"❌ 詳細錯誤: {error_msg}")
        print(f"   文章來源: {article.get('source', 'Unknown')}")
        print(f"   文章標題: {article.get('title', 'Unknown')[:50]}...")
        return error_msg

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

def get_multi_source_news(keywords=None, filter_at_source=False):
    """獲取多來源新聞，可選擇在抓取階段進行關鍵字篩選"""
    print("開始抓取多來源新聞...")
    print("=" * 70)
    if filter_at_source and keywords:
        print(f"關鍵字篩選: {', '.join(keywords)}")
        print("=" * 70)
    else:
        print("抓取所有文章（稍後進行關鍵字篩選）")
        print("=" * 70)
    
    # RSS feed 來源
    rss_sources = [
        {'name': 'Intel', 'url': 'https://newsroom.intel.com/zh-tw/feed/', 'type': 'rss'},
        {'name': 'Tom\'s Hardware', 'url': 'https://www.tomshardware.com/feeds/all', 'type': 'rss'},
    ]
    
    articles = []
    
    # 從 RSS feed 抓取
    for source in rss_sources:
        print(f"\n📡 抓取來源 (RSS): {source['name']}")
        print(f"   URL: {source['url']}")
        try:
            response = requests.get(source['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            feed = feedparser.parse(response.text)
            print(f"   ✅ 找到 {len(feed.entries)} 篇文章")
            
            if filter_at_source and keywords:
                # 篩選包含關鍵字的文章
                filtered_entries = []
                for entry in feed.entries:
                    title = entry.title
                    # 檢查標題是否包含關鍵字
                    if any(keyword.lower() in title.lower() for keyword in keywords):
                        filtered_entries.append(entry)
                
                print(f"   🔍 關鍵字篩選後: {len(filtered_entries)} 篇文章")
                entries_to_process = filtered_entries[:5]
            else:
                # 不篩選，取前5篇
                entries_to_process = feed.entries[:5]
            
            # 處理選定的文章
            for entry in entries_to_process:
                title = entry.title
                link = entry.link
                print(f"   - {title[:60]}...")
                articles.append({'title': title, 'url': link, 'source': source['name']})
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
            continue
    
    # 從 API 獲取 AMD 新聞
    print(f"\n🔌 API 獲取: AMD")
    print(f"   API: Coveo Search API")
    try:
        amd_articles = scrape_amd_news()
        if amd_articles:
            print(f"   ✅ 找到 {len(amd_articles)} 篇文章")
            for article in amd_articles[:5]:
                print(f"   - {article['title'][:60]}...")
                articles.append(article)
        else:
            print(f"   ⚠️  未找到文章")
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
    
    # 從 API 獲取 NVIDIA 新聞
    print(f"\n🔌 API 獲取: NVIDIA")
    print(f"   API: WordPress REST API")
    try:
        nvidia_articles = scrape_nvidia_news()
        if nvidia_articles:
            print(f"   ✅ 找到 {len(nvidia_articles)} 篇文章")
            for article in nvidia_articles[:5]:
                print(f"   - {article['title'][:60]}...")
                articles.append(article)
        else:
            print(f"   ⚠️  未找到文章")
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")

    if not articles:
        return "沒有找到任何文章"

    print(f"\n{'=' * 70}")
    print(f"總共收集到 {len(articles)} 篇文章，開始處理...")
    print("=" * 70)
    
    # 並行處理文章
    news_list = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_article, article) for article in articles]
        for i, future in enumerate(futures, 1):
            try:
                news_item = future.result(timeout=30)
                if not news_item.startswith("Error"):
                    news_list.append(news_item)
                    print(f"✅ 完成 {i}/{len(articles)}")
                else:
                    print(f"⚠️  跳過 {i}/{len(articles)} (處理失敗)")
            except Exception as e:
                print(f"❌ 錯誤 {i}/{len(articles)}: {e}")
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

    # 確保每個來源至少有一篇
    selected_news = []
    available_sources = list(source_groups.keys())

    # 第一輪：每個來源選一篇
    for source in available_sources:
        if source_groups[source]:
            # 隨機選一篇
            selected = random.choice(source_groups[source])
            selected_news.append(selected)
            source_groups[source].remove(selected)

    # 如果來源數量超過目標數量，隨機選擇需要的來源
    if len(selected_news) > target_count:
        selected_news = random.sample(selected_news, target_count)
    elif len(selected_news) < target_count:
        # 需要補充的新聞數量
        remaining_slots = target_count - len(selected_news)

        # 收集所有剩餘的新聞
        remaining_news = []
        for source in available_sources:
            remaining_news.extend(source_groups[source])

        # 隨機選擇補充的新聞
        if remaining_news:
            additional_news = random.sample(remaining_news, min(remaining_slots, len(remaining_news)))
            selected_news.extend(additional_news)

    return selected_news

def test_keywords(news_list):
    print("\n" + "=" * 70)
    print("🔍 關鍵字篩選測試")
    print("=" * 70)
    default_keywords = ["gpu", "電腦", "ai", "workstation", "顯卡"]
    print(f"預設關鍵字: {', '.join(default_keywords)}\n")

    # 測試預設關鍵字篩選（模擬輸入 "news"）
    print("📝 測試預設關鍵字篩選（輸入 'news'）:")
    filtered_news_default = get_keyword_filtered_news(news_list, default_keywords, target_count=5)

    print(f"   ✅ 找到 {len(filtered_news_default)} 篇包含預設關鍵字的新聞（隨機5篇，確保每個來源至少一篇）")

    # 測試自訂關鍵字篩選（模擬輸入單一關鍵字）
    test_keywords = ["gpu", "ai", "nvidia", "intel"]
    print("\n📝 測試自訂關鍵字篩選（輸入單一關鍵字）:")

    for test_keyword in test_keywords:
        filtered_news_custom = get_keyword_filtered_news(news_list, [test_keyword], target_count=5)
        print(f"   🔍 關鍵字「{test_keyword}」: 找到 {len(filtered_news_custom)} 篇新聞（隨機5篇，確保每個來源至少一篇）")

    # 顯示找到的新聞
    if filtered_news_default:
        print(f"\n✅ 預設關鍵字篩選結果（{len(filtered_news_default)} 篇）:\n")
        for i, news in enumerate(filtered_news_default, 1):
            print(f"\n【新聞 {i}】")
            print("=" * 70)
            print(news)
    else:
        print("\n❌ 沒有找到包含預設關鍵字的新聞")

def test_source_level_filtering():
    """測試來源層級關鍵字篩選"""
    print("\n" + "=" * 70)
    print("🔍 來源層級關鍵字篩選測試")
    print("=" * 70)
    
    default_keywords = ["gpu", "電腦", "ai", "workstation", "顯卡"]
    print(f"預設關鍵字: {', '.join(default_keywords)}")
    print("（RSS 來源在抓取時就進行關鍵字篩選）")
    print("=" * 70)
    
    # 使用來源層級篩選抓取新聞
    filtered_news_list = get_multi_source_news(keywords=default_keywords, filter_at_source=True)
    
    if isinstance(filtered_news_list, str):
        print(f"\n❌ 錯誤: {filtered_news_list}")
        return
    
    print(f"\n{'=' * 70}")
    print(f"📊 來源層級篩選統計")
    print("=" * 70)
    print(f"成功處理: {len(filtered_news_list)} 篇文章")
    
    # 統計各來源的文章數量
    source_count = {}
    for news_item in filtered_news_list:
        if news_item.strip() and not news_item.startswith("Error"):
            source_start = news_item.find("(來源: ") + 5
            source_end = news_item.find(")", source_start)
            if source_start > 4 and source_end > source_start:
                source = news_item[source_start:source_end]
                source_count[source] = source_count.get(source, 0) + 1
    
    print("各來源文章數量:")
    for source, count in source_count.items():
        print(f"   {source}: {count} 篇")
    
    # 應用最終選擇邏輯（隨機5篇，確保每個來源至少一篇）
    final_selection = get_keyword_filtered_news(filtered_news_list, default_keywords, target_count=5, already_filtered=True)
    
    print(f"\n最終選擇: {len(final_selection)} 篇新聞")
    if final_selection:
        print("\n✅ 最終選擇結果:\n")
        for i, news in enumerate(final_selection, 1):
            print(f"\n【新聞 {i}】")
            print("=" * 70)
            print(news)

if __name__ == "__main__":
    print("\n" + "🚀 多來源新聞爬取測試".center(70, "="))
    print()
    
    # 測試傳統模式：抓取所有文章，然後進行關鍵字篩選
    print("📋 測試模式 1: 傳統關鍵字篩選（抓取後篩選）")
    news_list = get_multi_source_news(filter_at_source=False)
    
    if isinstance(news_list, str):
        print(f"\n❌ 錯誤: {news_list}")
    else:
        print(f"\n{'=' * 70}")
        print(f"📊 抓取統計")
        print("=" * 70)
        print(f"成功處理: {len(news_list)} 篇文章")
        
        # 測試關鍵字篩選
        test_keywords(news_list)
    
    print("\n" + "🔄 切換到來源層級篩選測試".center(70, "-"))
    
    # 測試新模式：RSS 來源在抓取時就進行關鍵字篩選
    test_source_level_filtering()
    
    print("\n" + "=" * 70)
    print("✨ 測試完成！")
    print("=" * 70)

if __name__ == "__main__":
    print("\n" + "🚀 多來源新聞爬取測試".center(70, "="))
    print()
    
    # 測試新聞爬取
    news_list = get_multi_source_news()
    
    if isinstance(news_list, str):
        print(f"\n❌ 錯誤: {news_list}")
    else:
        print(f"\n{'=' * 70}")
        print(f"📊 爬取統計")
        print("=" * 70)
        print(f"成功處理: {len(news_list)} 篇文章")
        
        # 測試關鍵字篩選
        test_keywords(news_list)
    
    print("\n" + "=" * 70)
    print("✨ 測試完成！")
    print("=" * 70)
