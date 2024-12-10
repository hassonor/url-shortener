import logging

import pybreaker
import redis.asyncio as redis
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from infrastructure.config import settings

logger = logging.getLogger(__name__)

redis_breaker = pybreaker.CircuitBreaker(
    fail_max=3, reset_timeout=30, name="redis_circuit_breaker"
)


class RedisClient:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        self._closing = False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def connect(self):
        if self._closing:
            logger.info({"action": "connect_redis", "status": "aborted"})
            return
        try:
            await self.redis.ping()
            logger.info({"action": "connect_redis", "status": "connected"})
        except Exception as e:
            logger.exception({"action": "connect_redis", "status": "failed", "error": str(e)})
            raise

    @redis_breaker
    async def cache_short_code(self, short_code: str, long_url: str):
        if self._closing:
            logger.info(
                {
                    "action": "cache_short_code",
                    "short_code": short_code,
                    "status": "shutting_down",
                }
            )
            return
        key = f"url:{short_code}"
        logger.debug(
            {
                "action": "cache_short_code",
                "short_code": short_code,
                "long_url": long_url,
            }
        )
        try:
            await self.redis.set(key, long_url, ex=3600)
            logger.info(
                {
                    "action": "cache_short_code",
                    "short_code": short_code,
                    "status": "cached",
                }
            )
        except Exception as e:
            logger.warning(
                {
                    "action": "cache_short_code",
                    "short_code": short_code,
                    "long_url": long_url,
                    "status": "transient_failure",
                    "error": str(e),
                }
            )
            raise

    @redis_breaker
    async def get_long_url(self, short_code: str):
        if self._closing:
            logger.info(
                {
                    "action": "get_long_url_redis",
                    "short_code": short_code,
                    "status": "shutting_down",
                }
            )
            return None
        key = f"url:{short_code}"
        logger.debug({"action": "get_long_url_redis", "short_code": short_code})
        try:
            val = await self.redis.get(key)
            status = "found" if val else "not_found"
            logger.debug(
                {
                    "action": "get_long_url_redis",
                    "short_code": short_code,
                    "status": status,
                }
            )
            return val
        except Exception as e:
            logger.warning(
                {
                    "action": "get_long_url_redis",
                    "short_code": short_code,
                    "status": "transient_failure",
                    "error": str(e),
                }
            )
            raise

    async def close(self):
        self._closing = True
        await self.redis.close()
        logger.info({"action": "close_redis", "status": "closed"})


redis_client = RedisClient()
