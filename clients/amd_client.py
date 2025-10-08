from .base_client import BaseAPIClient

# 常量定義
FULL_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
REQUEST_TIMEOUT = 15

class AMDAPIClient(BaseAPIClient):
    """AMD API 客戶端"""

    def get_news(self):
        """獲取 AMD 新聞"""
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
                'user-agent': FULL_USER_AGENT
            }

            data = {
                "locale": "zh-TW",
                "cq": "(@amd_result_type==\"Press Releases\")",
                "context": {"amd_lang": "zh-TW"},
                "q": "GPU OR AI OR 顯卡 OR workstation OR 電腦",
                "sortCriteria": "@amd_release_date descending",
                "numberOfResults": 10,
                "firstResult": 0
            }

            response = self._make_request(api_url, method='POST', headers=headers, json_data=data, timeout=REQUEST_TIMEOUT)

            if response and response.status_code == 200:
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