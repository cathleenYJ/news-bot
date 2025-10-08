from clients import AMDAPIClient, NvidiaAPIClient, RSSClient, ArticleClient

# 常量定義
DEFAULT_KEYWORDS = ["gpu", "電腦", "ai", "workstation", "顯卡"]
REQUEST_TIMEOUT = 15
RSS_TIMEOUT = 10

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
        """獲取多來源新聞，可選擇在抓取階段進行關鍵字篩選"""
        if keywords is None:
            keywords = DEFAULT_KEYWORDS

        # RSS feed 來源
        rss_sources = [
            {'name': 'Intel', 'url': 'https://newsroom.intel.com/zh-tw/feed/', 'type': 'rss'},
            {'name': 'Tom\'s Hardware', 'url': 'https://www.tomshardware.com/feeds/all', 'type': 'rss'},
        ]

        articles = []

        # 從 RSS feed 抓取
        rss_articles = self.rss_client.get_news(rss_sources, keywords, filter_at_source)
        articles.extend(rss_articles)

        # 從網頁爬取 AMD 和 NVIDIA 新聞
        try:
            amd_articles = self.scrape_amd_news()
            articles.extend(amd_articles[:5])
        except Exception as e:
            print(f"Error adding AMD articles: {e}")

        try:
            nvidia_articles = self.scrape_nvidia_news()
            articles.extend(nvidia_articles[:5])
        except Exception as e:
            print(f"Error adding NVIDIA articles: {e}")

        # 並行處理文章
        news_list = []
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.process_article, article) for article in articles]
            for future in futures:
                try:
                    news_item = future.result(timeout=30)
                    news_list.append(news_item)
                except Exception as e:
                    print(f"Error processing article: {e}")
                    continue

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