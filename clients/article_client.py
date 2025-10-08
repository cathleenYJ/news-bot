from newspaper import Article
from summa import summarizer
from .base_client import BaseAPIClient
from functools import lru_cache
import time

# 常量定義
DEFAULT_USER_AGENT = 'Mozilla/5.0'

class ArticleClient(BaseAPIClient):

    def __init__(self):
        super().__init__()
        self._cache = {}
        self._cache_timeout = 3600  # 1小時緩存

    def _get_cache_key(self, url):
        """生成緩存鍵"""
        return f"article_{hash(url)}"

    def _is_cache_valid(self, cache_key):
        """檢查緩存是否有效"""
        if cache_key in self._cache:
            timestamp, _ = self._cache[cache_key]
            return time.time() - timestamp < self._cache_timeout
        return False

    def _cleanup_cache(self):
        """清理過期的緩存項目"""
        current_time = time.time()
        expired_keys = [
            key for key, (timestamp, _) in self._cache.items()
            if current_time - timestamp > self._cache_timeout
        ]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            print(f"清理了 {len(expired_keys)} 個過期緩存項目")

    def process_article(self, article):
        """處理單篇文章"""
        url = article['url']
        cache_key = self._get_cache_key(url)

        # 增加緩存大小，減少清理頻率
        if len(self._cache) > 100:  # 增加到100個項目
            self._cleanup_cache()

        # 檢查緩存
        if self._is_cache_valid(cache_key):
            print(f"使用緩存的文章: {url}")
            _, cached_result = self._cache[cache_key]
            return cached_result

        try:
            response = self._make_request(url, headers={'User-Agent': DEFAULT_USER_AGENT}, allow_redirects=True, timeout=10)  # 減少請求超時
            if response:
                real_url = response.url
                art = Article(real_url)

                # 設置更短的超時時間
                art.config.timeout = 8  # newspaper3k下載超時
                art.download()
                art.parse()

                # 清理不需要的數據以節省內存
                if hasattr(art, 'html'):
                    art.html = None

                if art.text.strip() == "":
                    summary = "無法生成摘要"
                else:
                    # 優化摘要生成：減少文本長度和參數以提升速度
                    text_to_summarize = art.text[:8000]  # 減少到8000字符
                    summary = summarizer.summarize(text_to_summarize, ratio=0.15, words=25)  # 增加ratio，減少words以加快處理
                    if len(summary) > 120:  # 減少摘要長度
                        summary = summary[:120] + "..."

                news_item = f"📰 標題: {article['title']} (來源: {article['source']})\n🔗 連結: {real_url}\n📑 新聞摘要: {summary}\n"

                # 存儲到緩存
                self._cache[cache_key] = (time.time(), news_item)

                return news_item
        except Exception as e:
            error_msg = f"Error processing {url}: {e}\n"
            # 即使出錯也緩存，避免重複錯誤
            self._cache[cache_key] = (time.time(), error_msg)
            return error_msg
        finally:
            # 確保清理資源
            import gc
            gc.collect()
        return ""