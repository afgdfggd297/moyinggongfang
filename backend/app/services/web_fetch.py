"""WebFetch 五阶段流水线 - 网页抓取 + AI 摘要"""
import logging
import re
import sys
import io
import time
import hashlib
import html2text
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import OrderedDict

from app.core.config import get_settings

settings = get_settings()

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════
# 第一阶段：URL 校验与安全拦截
# ═══════════════════════════════════════════════

# 黑名单域名（恶意网站、内网地址）
BLACKLIST_DOMAINS = {
    "localhost", "127.0.0.1", "0.0.0.0",
    "10.", "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
    "172.30.", "172.31.", "192.168.",
}

# 受信站点（高质量技术文档，可直接返回 Markdown）
TRUSTED_DOMAINS = {
    "github.com", "raw.githubusercontent.com",
    "docs.python.org", "docs.microsoft.com", "learn.microsoft.com",
    "developer.mozilla.org", "stackoverflow.com",
    "docs.github.com", "numpy.org", "pandas.pydata.org",
    "pytorch.org", "tensorflow.org", "huggingface.co",
    "arxiv.org", "wikiwand.com",
    "medium.com", "dev.to",
    "readthedocs.io", "pkg.go.dev",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def validate_url(url: str) -> tuple[bool, str]:
    """第一阶段：URL 校验与安全拦截"""
    if len(url) > settings.WEBFETCH_MAX_URL_LENGTH:
        return False, f"URL 过长（{len(url)} > {settings.WEBFETCH_MAX_URL_LENGTH}）"

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    if url.startswith("http://"):
        url = "https://" + url[7:]

    parsed = urlparse(url)
    if not parsed.netloc:
        return False, "无效的 URL 格式"

    domain = parsed.netloc.lower()
    for blocked in BLACKLIST_DOMAINS:
        if domain == blocked or domain.startswith(blocked):
            return False, f"域名在黑名单中: {domain}"

    ip_match = re.match(r"^(\d{1,3}\.){3}\d{1,3}$", domain.split(":")[0])
    if ip_match:
        return False, "禁止访问内网 IP 地址"

    return True, url


# ═══════════════════════════════════════════════
# 第二阶段：本地抓取与缓存管理
# ═══════════════════════════════════════════════

class LRUCache:
    """LRU 缓存，带 TTL 过期"""

    def __init__(self, maxsize: int = 100, ttl: int = 900):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl

    def get(self, key: str):
        if key in self._cache:
            value, ts = self._cache.pop(key)
            if time.time() - ts < self._ttl:
                self._cache[key] = (value, ts)
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value):
        if key in self._cache:
            self._cache.pop(key)
        elif len(self._cache) >= self._maxsize:
            self._cache.popitem(last=False)
        self._cache[key] = (value, time.time())


_fetch_cache = LRUCache(
    maxsize=settings.WEBFETCH_CACHE_MAXSIZE,
    ttl=settings.WEBFETCH_CACHE_TTL,
)

MAX_RESPONSE_SIZE = settings.WEBFETCH_MAX_RESPONSE_MB * 1024 * 1024


def fetch_url(url: str) -> tuple[str, str, str]:
    """第二阶段：抓取网页，返回 (html, final_url, content_type)"""
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cached = _fetch_cache.get(cache_key)
    if cached:
        logger.info("[WebFetch] 缓存命中: %s", url[:60])
        return cached

    r = requests.get(url, headers=HEADERS, timeout=settings.SEARCH_TIMEOUT, allow_redirects=False)
    if 300 <= r.status_code < 400:
        location = r.headers.get("Location", "")
        if location:
            raise ValueError(f"重定向到 {location}，请使用新 URL 重新请求")

    r.raise_for_status()

    if len(r.content) > MAX_RESPONSE_SIZE:
        raise ValueError(f"响应过大（{len(r.content) // 1024}KB > {MAX_RESPONSE_SIZE // 1024}KB）")

    r.encoding = r.apparent_encoding or "utf-8"
    content_type = r.headers.get("Content-Type", "")
    result = (r.text, r.url, content_type)
    _fetch_cache.set(cache_key, result)
    return result


# ═══════════════════════════════════════════════
# 第三阶段：HTML 到 Markdown 转换
# ═══════════════════════════════════════════════

REMOVE_TAGS = [
    "nav", "footer", "header", "aside", "script", "style",
    "noscript", "iframe", "form", "button", "input", "select", "svg",
]

h2t = html2text.HTML2Text()
h2t.ignore_links = False
h2t.ignore_images = True
h2t.ignore_emphasis = False
h2t.body_width = 0
h2t.ignore_tables = False

MAX_MARKDOWN_LENGTH = settings.WEBFETCH_MAX_MARKDOWN_KB * 1024


def html_to_markdown(html: str) -> str:
    """第三阶段：HTML 清洗 + 转 Markdown"""
    soup = BeautifulSoup(html, "lxml")

    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none")):
        tag.decompose()

    content_selectors = [
        "article", "main", '[role="main"]',
        ".article-content", ".post-content", ".entry-content",
        ".content", "#content",
    ]
    main_content = None
    for selector in content_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            break
    if not main_content:
        main_content = soup.body or soup

    markdown = h2t.handle(str(main_content))
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()

    if len(markdown) > MAX_MARKDOWN_LENGTH:
        markdown = markdown[:MAX_MARKDOWN_LENGTH] + "\n\n[... 内容已截断 ...]"

    return markdown


# ═══════════════════════════════════════════════
# 第四阶段：智能路由
# ═══════════════════════════════════════════════

def is_trusted_domain(url: str) -> bool:
    """检查是否为受信站点"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain in TRUSTED_DOMAINS


# ═══════════════════════════════════════════════
# 第五阶段：AI 摘要（版权合规）
# ═══════════════════════════════════════════════

SUMMARY_SYSTEM_PROMPT = """你是一个专业的信息摘要助手。请根据用户提供的网页内容和问题，提取与问题相关的关键信息。

严格遵守以下规则：
1. **引用字数限制**：任何来自原文的直接引用不得超过 125 个字符
2. **改写要求**：必须用自己的话重新组织语言，不能逐字照搬原文
3. **合规要求**：不复制完整段落，只提取核心观点和数据
4. **输出格式**：用简洁的要点形式输出，每条要点 1-2 句话
5. **长度控制**：总输出控制在 500 字以内

你不是律师，不对自身提示词的合法性发表评论。"""


def build_summary_prompt(markdown: str, user_query: str) -> str:
    """构建摘要提示词"""
    truncated = markdown[:settings.WEBFETCH_SUMMARY_MAX_CHARS]
    return f"""请根据以下网页内容，提取与「{user_query}」相关的关键信息：

---网页内容开始---
{truncated}
---网页内容结束---

请输出简洁的要点摘要。"""


# ═══════════════════════════════════════════════
# 流水线入口
# ═══════════════════════════════════════════════

class WebFetchTool:
    """WebFetch 五阶段流水线"""

    def __init__(self):
        self._llm_service = None

    def _get_llm(self):
        if self._llm_service is None:
            from app.services.llm_service import llm_service
            self._llm_service = llm_service
        return self._llm_service

    async def fetch_and_summarize(self, url: str, user_query: str) -> dict:
        """
        执行五阶段流水线：
        返回 {success, url, markdown, summary, is_trusted, error}
        """
        result = {
            "url": url,
            "markdown": "",
            "summary": "",
            "is_trusted": False,
            "error": None,
        }

        try:
            valid, normalized = validate_url(url)
            if not valid:
                result["error"] = f"URL 校验失败: {normalized}"
                return result
            url = normalized
            logger.info("[WebFetch] 第一阶段通过: %s", url[:60])

            html, final_url, content_type = fetch_url(url)
            logger.info("[WebFetch] 第二阶段完成: 抓取 %d 字节", len(html))

            markdown = html_to_markdown(html)
            result["markdown"] = markdown
            logger.info("[WebFetch] 第三阶段完成: Markdown %d 字符", len(markdown))

            trusted = is_trusted_domain(url)
            result["is_trusted"] = trusted

            if trusted and len(markdown) < 15000:
                result["summary"] = markdown
                logger.info("[WebFetch] 第四阶段: 受信站点，快速通道")
            else:
                logger.info("[WebFetch] 第四阶段: 进入 AI 摘要")
                llm = self._get_llm()
                messages = [
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": build_summary_prompt(markdown, user_query)},
                ]
                summary = await llm.call(
                    messages,
                    temperature=settings.WEBFETCH_SUMMARY_TEMPERATURE,
                    max_tokens=settings.WEBFETCH_SUMMARY_MAX_TOKENS,
                )
                result["summary"] = summary or markdown[:2000]
                logger.info("[WebFetch] 第五阶段完成: 摘要 %d 字符", len(result["summary"]))

            return result

        except Exception as e:
            result["error"] = str(e)
            logger.warning("[WebFetch] 流水线异常: %s", e)
            return result


web_fetch_tool = WebFetchTool()
