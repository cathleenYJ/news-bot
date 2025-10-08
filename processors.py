from clients import AMDAPIClient, NvidiaAPIClient, RSSClient, ArticleClient
import psutil
import os
from functools import lru_cache
import time
import feedparser

# 常量定義
DEFAULT_KEYWORDS = ["gpu", "電腦", "ai", "workstation", "顯卡"]
DEFAULT_USER_AGENT = 'Mozilla/5.0'
REQUEST_TIMEOUT = 15
RSS_TIMEOUT = 10

def get_memory_usage():
    """獲取當前內存使用情況"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

class NewsProcessor:
    """新聞處理器類別，負責所有新聞抓取和處理邏輯"""

    def __init__(self, amd_client, nvidia_client, rss_client, article_client):
        self.amd_client = amd_client
        self.nvidia_client = nvidia_client
        self.rss_client = rss_client
        self.article_client = article_client

    def process_article(self, article):
        """處理單篇文章，生成摘要"""
        return self.article_client.process_article(article)

    def scrape_amd_news(self):
        """使用 AMD API 獲取新聞（帶關鍵字搜尋）"""
        return self.amd_client.get_news()

    def scrape_nvidia_news(self):
        """使用 NVIDIA WordPress API 獲取新聞（帶關鍵字搜尋）"""
        return self.nvidia_client.get_news()

    def get_intel_news(self, keywords=None, filter_at_source=True):
        """獲取多來源新聞，為每個來源選擇1則最符合關鍵字且最新的新聞"""
        print(f"開始獲取新聞，當前內存使用: {get_memory_usage():.1f} MB")

        if not keywords:
            keywords = DEFAULT_KEYWORDS

        selected_news = []

        # 並發獲取所有來源的新聞
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def fetch_rss_source(source):
            """獲取單個RSS來源的新聞"""
            try:
                rss_articles = self.rss_client.get_news([source], keywords, filter_at_source=True)
                if rss_articles:
                    return rss_articles[0]  # 取最新的1則
                return None
            except Exception as e:
                print(f"Error fetching from {source['name']}: {e}")
                return None

        def fetch_amd_news():
            """獲取AMD新聞"""
            try:
                amd_articles = self.scrape_amd_news()
                matching_amd = [
                    article for article in amd_articles
                    if any(keyword.lower() in article.get('title', '').lower() for keyword in keywords)
                ]
                if matching_amd:
                    return {
                        'title': matching_amd[0]['title'],
                        'url': matching_amd[0]['url'],
                        'source': 'AMD'
                    }
                return None
            except Exception as e:
                print(f"Error processing AMD articles: {e}")
                return None

        def fetch_nvidia_news():
            """獲取NVIDIA新聞"""
            try:
                nvidia_articles = self.scrape_nvidia_news()
                matching_nvidia = [
                    article for article in nvidia_articles
                    if any(keyword.lower() in article.get('title', '').lower() for keyword in keywords)
                ]
                if matching_nvidia:
                    return {
                        'title': matching_nvidia[0]['title'],
                        'url': matching_nvidia[0]['url'],
                        'source': 'NVIDIA'
                    }
                return None
            except Exception as e:
                print(f"Error processing NVIDIA articles: {e}")
                return None

        # RSS feed 來源
        rss_sources = [
            {'name': 'Intel', 'url': 'https://newsroom.intel.com/zh-tw/feed/', 'type': 'rss'},
            {'name': 'Tom\'s Hardware', 'url': 'https://www.tomshardware.com/feeds/all', 'type': 'rss'},
        ]

        # 並發執行所有來源的獲取任務
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 提交所有任務
            future_to_source = {}

            # RSS來源任務
            for source in rss_sources:
                future = executor.submit(fetch_rss_source, source)
                future_to_source[future] = source['name']

            # AMD任務
            amd_future = executor.submit(fetch_amd_news)
            future_to_source[amd_future] = 'AMD'

            # NVIDIA任務
            nvidia_future = executor.submit(fetch_nvidia_news)
            future_to_source[nvidia_future] = 'NVIDIA'

            # 收集結果
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    result = future.result(timeout=15)  # 15秒超時
                    if result:
                        selected_news.append(result)
                        print(f"{source_name}: 找到 1 則符合關鍵字的新聞")
                except Exception as e:
                    print(f"Error getting result from {source_name}: {e}")

        print(f"各來源篩選完成，共 {len(selected_news)} 篇文章")

        # 如果沒有文章，返回空列表
        if not selected_news:
            print("沒有找到符合條件的新聞")
            return []

        # 並行處理選定的文章 - 增加並發數並減少超時時間
        news_list = []

        # 增加並發數，減少超時時間以提升響應速度
        max_workers = min(6, len(selected_news))  # 增加到6個並發線程

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_article, article) for article in selected_news]
            for future in as_completed(futures):
                try:
                    news_item = future.result(timeout=20)  # 減少到20秒超時
                    if news_item and news_item.strip():
                        news_list.append(news_item)
                except Exception as e:
                    print(f"Error processing article: {e}")
                    continue

        print(f"處理完成，生成 {len(news_list)} 條新聞，內存使用: {get_memory_usage():.1f} MB")
        return news_list

    def get_keyword_filtered_news(self, news_list, keywords, target_count=5, already_filtered=False):
        """篩選包含關鍵字的新聞，確保每個來源至少一篇，然後隨機補充到指定數量

        Args:
            news_list: 新聞列表
            keywords: 關鍵字列表
            target_count: 目標數量
            already_filtered: 是否已經在來源層級進行過關鍵字篩選
        """
        import random

        print(f"開始關鍵字過濾，共 {len(news_list)} 條新聞，關鍵字: {keywords}")

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
                        print(f"  添加 {source} 新聞到組")
                    else:
                        print(f"  無法提取來源: {news_item[:100]}...")
                else:
                    print(f"  跳過不包含關鍵字的新聞: {news_item[:100]}...")
            else:
                print(f"  跳過無效新聞: {news_item[:50]}...")

        print(f"來源分組結果: {dict((k, len(v)) for k, v in source_groups.items())}")

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