import feedparser
from .base_client import BaseAPIClient

# 常量定義
DEFAULT_USER_AGENT = 'Mozilla/5.0'
RSS_TIMEOUT = 10

class RSSClient(BaseAPIClient):
    """RSS Feed 客戶端"""

    def get_news(self, sources, keywords=None, filter_at_source=True):
        """獲取 RSS 新聞"""
        articles = []

        for source in sources:
            try:
                response = self._make_request(source['url'], headers={'User-Agent': DEFAULT_USER_AGENT}, timeout=RSS_TIMEOUT)
                if response:
                    feed = feedparser.parse(response.text)

                    if filter_at_source and keywords:
                        filtered_entries = [
                            entry for entry in feed.entries
                            if any(keyword.lower() in entry.title.lower() for keyword in keywords)
                        ]
                        entries_to_process = filtered_entries[:5]
                    else:
                        entries_to_process = feed.entries[:5]

                    for entry in entries_to_process:
                        title = entry.title
                        link = entry.link
                        articles.append({'title': title, 'url': link, 'source': source['name']})
            except Exception as e:
                print(f"Error fetching from {source['name']}: {e}")
                continue

        return articles