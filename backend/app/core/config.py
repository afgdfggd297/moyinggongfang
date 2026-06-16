"""应用配置模块"""
from enum import Enum
from functools import lru_cache
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    DEV = "development"
    PROD = "production"
    TEST = "testing"


class Settings(BaseSettings):
    """应用配置"""

    ENVIRONMENT: Environment = Environment.DEV
    APP_NAME: str = "PPTGenerator"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # MiMo API
    MIMO_API_KEY: str = ""
    MIMO_BASE_URL: str = "https://token-plan-cn.xiaomimimo.com/v1"
    MIMO_LLM_MODEL: str = "mimo-v2.5-pro"

    # LLM 服务
    LLM_TOTAL_TIMEOUT: int = 120
    MAX_LLM_CALL_RETRIES: int = 3

    # Redis
    REDIS_URL: str = "redis://:deepresearch@127.0.0.1:6379/0"

    # 文件路径
    UPLOAD_DIR: str = "./uploads"
    STATIC_DIR: str = "./static"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]

    # ═══ PPT 导出 ═══
    PPT_SLIDE_W: float = 13.333          # 幻灯片宽度（英寸）
    PPT_SLIDE_H: float = 7.5             # 幻灯片高度（英寸）
    PPT_PX_W: int = 1280                 # 截图像素宽度
    PPT_PX_H: int = 720                  # 截图像素高度
    PPT_SCALE: int = 2                   # html2ppt 缩放倍数
    PPT_TIMEOUT: int = 60                # html2ppt 单页超时（秒）
    PPT_HTML2PPT_BIN: str = ""           # html2ppt 路径，留空自动查找
    PPT_BG_COLOR: str = "#ffffff"        # 幻灯片背景色

    # ═══ 搜索 ═══
    SEARCH_ENGINE_URL: str = "https://cn.bing.com/search"
    SEARCH_TIMEOUT: int = 10             # 搜索请求超时（秒）
    SEARCH_MAX_RESULTS: int = 5          # 单次搜索最大结果数
    SEARCH_QUERY_MAX_LEN: int = 80       # 搜索关键词最大长度

    # ═══ WebFetch ═══
    WEBFETCH_MAX_URL_LENGTH: int = 2000
    WEBFETCH_MAX_RESPONSE_MB: int = 10   # 最大响应体积（MB）
    WEBFETCH_CACHE_MAXSIZE: int = 100    # LRU 缓存条数
    WEBFETCH_CACHE_TTL: int = 900        # 缓存过期（秒）
    WEBFETCH_MAX_MARKDOWN_KB: int = 100  # Markdown 最大长度（KB）
    WEBFETCH_SUMMARY_MAX_CHARS: int = 8000  # 摘要输入截断字符数

    # ═══ WebFetch AI 摘要 ═══
    WEBFETCH_SUMMARY_TEMPERATURE: float = 0.4
    WEBFETCH_SUMMARY_MAX_TOKENS: int = 1500

    # ═══ LLM 温度 ═══
    LLM_PLAN_TEMPERATURE: float = 0.8     # 方案规划
    LLM_HTML_TEMPERATURE: float = 0.9     # HTML 生成
    LLM_STREAM_TEMPERATURE: float = 0.9   # 流式输出

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
