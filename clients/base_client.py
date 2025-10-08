import requests

# 常量定義
REQUEST_TIMEOUT = 15

class BaseAPIClient:
    """基礎 API 客戶端類別，提供通用請求方法"""

    def _make_request(self, url, method='GET', headers=None, params=None, data=None, json_data=None, timeout=REQUEST_TIMEOUT, allow_redirects=True):
        """通用 API 請求方法"""
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=timeout, allow_redirects=allow_redirects)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=json_data, data=data, timeout=timeout, allow_redirects=allow_redirects)
            else:
                raise ValueError(f"Unsupported method: {method}")
            return response
        except Exception as e:
            print(f"Request error for {url}: {e}")
            return None