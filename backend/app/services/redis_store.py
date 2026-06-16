"""Redis 存储服务 - 替代内存存储"""
import json
import logging
import redis

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Redis key 前缀
PREFIX = "ppt:plan:"


class PlanStore:
    """方案存储，使用 Redis"""

    def __init__(self):
        self._client: redis.Redis | None = None

    def init(self):
        """初始化 Redis 连接"""
        try:
            self._client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            self._client.ping()
            logger.info("[Redis] 连接成功: %s", settings.REDIS_URL.split("@")[-1])
        except Exception as e:
            logger.error("[Redis] 连接失败: %s", str(e))
            self._client = None

    def _get_client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis 未连接")
        return self._client

    def save(self, plan_id: str, data: dict):
        """保存方案数据"""
        client = self._get_client()
        key = PREFIX + plan_id
        client.set(key, json.dumps(data, ensure_ascii=False), ex=86400)  # 24小时过期
        logger.info("[Redis] 保存方案: %s", plan_id)

    def get(self, plan_id: str) -> dict | None:
        """获取方案数据"""
        client = self._get_client()
        key = PREFIX + plan_id
        raw = client.get(key)
        if raw is None:
            logger.warning("[Redis] 方案不存在: %s", plan_id)
            return None
        return json.loads(raw)

    def delete(self, plan_id: str):
        """删除方案数据"""
        client = self._get_client()
        key = PREFIX + plan_id
        client.delete(key)
        logger.info("[Redis] 删除方案: %s", plan_id)

    def exists(self, plan_id: str) -> bool:
        """检查方案是否存在"""
        client = self._get_client()
        key = PREFIX + plan_id
        return client.exists(key) > 0


# 单例
plan_store = PlanStore()
