import logging
import redis.asyncio as redis
from infrastructure.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    async def connect(self):
        try:
            await self.redis.ping()
            logger.info("Connected to Redis.")
        except Exception as e:
            logger.exception("Failed to connect to Redis: %s", e)
            raise

    async def cache_short_code(self, short_code: str, long_url: str):
        key = f"url:{short_code}"
        await self.redis.set(key, long_url, ex=3600)  # Cache for 1h

    async def get_long_url(self, short_code: str):
        key = f"url:{short_code}"
        return await self.redis.get(key)

    async def close(self):
        await self.redis.close()
        logger.info("Redis connection closed.")

redis_client = RedisClient()
