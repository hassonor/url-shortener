import asyncio

from infrastructure.config import settings
from pybloom_live import BloomFilter

bloom_filter = BloomFilter(
    capacity=settings.BLOOM_EXPECTED_ITEMS, error_rate=settings.BLOOM_ERROR_RATE
)
bloom_lock = asyncio.Lock()
