import re
from .base_client import BaseAPIClient

# 常量定義
FULL_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
REQUEST_TIMEOUT = 15

class NvidiaAPIClient(BaseAPIClient):
    """NVIDIA API 客戶端"""

    def get_news(self):
        """獲取 NVIDIA 新聞"""
        articles = []
        keywords = ['GPU', 'AI', '顯卡']
        all_posts = []
        seen_urls = set()

        try:
            api_url = 'https://blogs.nvidia.com.tw/wp-json/wp/v2/posts'
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'origin': 'https://www.nvidia.com',
                'referer': 'https://www.nvidia.com/',
                'user-agent': FULL_USER_AGENT
            }

            for keyword in keywords:
                try:
                    params = {
                        '_embed': 'true',
                        'per_page': 5,
                        'page': 1,
                        'search': keyword
                    }

                    response = self._make_request(api_url, method='GET', headers=headers, params=params, timeout=REQUEST_TIMEOUT)

                    if response and response.status_code == 200:
                        posts = response.json()

                        for post in posts:
                            link = post.get('link', '')
                            if link and link not in seen_urls:
                                seen_urls.add(link)
                                title = post.get('title', {}).get('rendered', '').strip()
                                if title:
                                    title = re.sub('<.*?>', '', title)
                                    all_posts.append({'title': title, 'url': link, 'source': 'NVIDIA', 'date': post.get('date', '')})
                except Exception as e:
                    print(f"Error searching NVIDIA with keyword '{keyword}': {e}")
                    continue

            if all_posts:
                all_posts.sort(key=lambda x: x.get('date', ''), reverse=True)
                articles = [{'title': p['title'], 'url': p['url'], 'source': p['source']} for p in all_posts[:5]]

        except Exception as e:
            print(f"Error fetching NVIDIA news: {e}")

        return articles