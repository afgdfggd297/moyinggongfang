"""搜索服务 - 基于 WebFetch 五阶段流水线"""
import logging
import requests
from bs4 import BeautifulSoup

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class SearchService:
    """Bing 搜索"""

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Bing 搜索，返回 [{title, url}]"""
        try:
            r = self._session.get(
                settings.SEARCH_ENGINE_URL,
                params={"q": query},
                timeout=settings.SEARCH_TIMEOUT,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

            results = []
            for item in soup.select(".b_algo")[:max_results]:
                h2 = item.select_one("h2")
                if not h2:
                    continue
                a = h2.find("a")
                title = h2.get_text().strip()
                url = a["href"] if a and a.get("href") else ""
                if title and url and url.startswith("http"):
                    results.append({"title": title, "url": url})

            logger.info("[Search] 搜索 '%s' 返回 %d 条", query, len(results))
            return results

        except Exception as e:
            logger.warning("[Search] 搜索失败: %s", e)
            return []

    def search_for_plan(self, user_text: str) -> str:
        """搜索并返回参考 URL 列表（由 WebFetch 流水线处理）"""
        query = user_text[:settings.SEARCH_QUERY_MAX_LEN].strip()
        if not query:
            return "", []

        results = self.search(query, max_results=settings.SEARCH_MAX_RESULTS)
        if not results:
            return "", []

        urls = [r["url"] for r in results]
        titles = [r["title"] for r in results]
        return titles, urls


search_service = SearchService()
