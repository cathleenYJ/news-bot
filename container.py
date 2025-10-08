"""
依賴注入容器示例
展示如何使用自定義的 API 客戶端實例
"""

from clients import AMDAPIClient, NvidiaAPIClient, RSSClient, ArticleClient
from processors import NewsProcessor

class MockAMDClient(AMDAPIClient):
    """模擬 AMD 客戶端，用於測試"""
    def get_news(self):
        return [
            {'title': 'Mock AMD News', 'url': 'https://example.com/amd', 'source': 'AMD'}
        ]

class NewsBotContainer:
    """新聞機器人依賴注入容器"""

    def __init__(self):
        # 可以根據環境配置不同的客戶端
        self.amd_client = AMDAPIClient()  # 或 MockAMDClient() 用於測試
        self.nvidia_client = NvidiaAPIClient()
        self.rss_client = RSSClient()
        self.article_client = ArticleClient()

    def create_news_processor(self):
        """創建配置好的新聞處理器"""
        return NewsProcessor(
            amd_client=self.amd_client,
            nvidia_client=self.nvidia_client,
            rss_client=self.rss_client,
            article_client=self.article_client
        )

# 使用示例
if __name__ == "__main__":
    container = NewsBotContainer()
    processor = container.create_news_processor()

    # 測試新聞獲取
    news = processor.get_intel_news()
    print(f"獲取到 {len(news)} 條新聞")