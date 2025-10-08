from newspaper import Article
from summa import summarizer
from .base_client import BaseAPIClient

# 常量定義
DEFAULT_USER_AGENT = 'Mozilla/5.0'

class ArticleClient(BaseAPIClient):
    """文章處理客戶端"""

    def process_article(self, article):
        """處理單篇文章"""
        try:
            response = self._make_request(article['url'], headers={'User-Agent': DEFAULT_USER_AGENT}, allow_redirects=True)
            if response:
                real_url = response.url
                art = Article(real_url)
                art.download()
                art.parse()
                if art.text.strip() == "":
                    summary = "無法生成摘要"
                else:
                    summary = summarizer.summarize(art.text, ratio=0.1, words=30)
                    if len(summary) > 150:
                        summary = summary[:150] + "..."

                news_item = f"📰 標題: {article['title']} (來源: {article['source']})\n🔗 連結: {real_url}\n📑 新聞摘要: {summary}\n"
                return news_item
        except Exception as e:
            return f"Error processing {article['url']}: {e}\n"
        return ""