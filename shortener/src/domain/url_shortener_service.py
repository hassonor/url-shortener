import asyncio
import hashlib
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

from asyncpg import UniqueViolationError
from infrastructure.database import Database
from infrastructure.metrics import url_created, url_lookup_latency
from infrastructure.redis_client import RedisClient
from pybloom_live import BloomFilter

logger = logging.getLogger(__name__)


class URLShortenerService:
    """
    Efficient URL shortener logic with bloom filter to minimize DB lookups.
    """

    def __init__(
        self,
        database: Database,
        redis_client: RedisClient,
        bloom: BloomFilter,
        lock: asyncio.Lock,
    ):
        self.database = database
        self.redis_client = redis_client
        self.bloom = bloom
        self.lock = lock

    async def shorten_url(
        self, long_url: str, correlation_id: Optional[str] = None
    ) -> Tuple[Optional[str], bool]:
        """
        Returns (short_code, newly_created).
        Only newly_created=True if a new record is inserted.
        """
        if not self.is_valid_url(long_url):
            logger.warning(
                {
                    "action": "shorten_url",
                    "long_url": long_url,
                    "status": "invalid_url",
                    "correlation_id": correlation_id,
                }
            )
            return None, False

        async with self.lock:
            if long_url in self.bloom:
                existing_code = await self.find_existing_short_code(long_url)
                if existing_code:
                    logger.debug(
                        {
                            "action": "shorten_url",
                            "long_url": long_url,
                            "short_code": existing_code,
                            "status": "already_known",
                            "correlation_id": correlation_id,
                        }
                    )
                    return existing_code, False

        short_code = self.generate_short_code(long_url)
        try:
            await self.database.insert_url_mapping(short_code, long_url)
            url_created.inc()
            await self.redis_client.cache_short_code(short_code, long_url)

            async with self.lock:
                self.bloom.add(long_url)

            logger.info(
                {
                    "action": "shorten_url",
                    "long_url": long_url,
                    "short_code": short_code,
                    "status": "created",
                    "correlation_id": correlation_id,
                }
            )
            return short_code, True
        except UniqueViolationError:
            existing_code = await self.find_existing_short_code(long_url)
            logger.info(
                {
                    "action": "shorten_url",
                    "long_url": long_url,
                    "short_code": existing_code,
                    "status": "already_exists",
                    "correlation_id": correlation_id,
                }
            )
            return existing_code, False
        except Exception as e:
            logger.exception(
                {
                    "action": "shorten_url",
                    "long_url": long_url,
                    "status": "failure",
                    "error": str(e),
                    "correlation_id": correlation_id,
                }
            )
            return None, False

    async def get_long_url(
        self, short_code: str, correlation_id: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve via Redis cache, fallback to DB."""
        start = asyncio.get_event_loop().time()
        cached_url = await self.redis_client.get_long_url(short_code)
        if cached_url:
            url_lookup_latency.observe(asyncio.get_event_loop().time() - start)
            logger.debug(
                {
                    "action": "get_long_url",
                    "short_code": short_code,
                    "status": "cache_hit",
                    "correlation_id": correlation_id,
                }
            )
            return cached_url

        long_url = await self.database.get_long_url(short_code)
        duration = asyncio.get_event_loop().time() - start
        url_lookup_latency.observe(duration)

        status = "found" if long_url else "not_found"
        logger.debug(
            {
                "action": "get_long_url",
                "short_code": short_code,
                "status": status,
                "correlation_id": correlation_id,
            }
        )

        if long_url:
            await self.redis_client.cache_short_code(short_code, long_url)
        return long_url

    async def find_existing_short_code(self, long_url: str) -> Optional[str]:
        return await self.database.get_short_code_by_long_url(long_url)

    @staticmethod
    def is_valid_url(url: str) -> bool:
        parsed = urlparse(url)
        return all([parsed.scheme in ("http", "https"), parsed.netloc])

    @staticmethod
    def generate_short_code(url: str) -> str:
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:7]
        return url_hash
