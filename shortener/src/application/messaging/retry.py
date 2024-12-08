import asyncio
import logging

logger = logging.getLogger(__name__)

async def retry_connection(connect_coro, max_retries=5, delay=5, name="service"):
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Connecting to %s (attempt %d/%d)...", name, attempt, max_retries)
            await connect_coro()
            logger.info("Connected to %s.", name)
            return
        except Exception as e:
            logger.warning("Failed to connect to %s: %s", name, e)
            if attempt < max_retries:
                logger.info("Retrying in %d seconds...", delay)
                await asyncio.sleep(delay)
    logger.error("Could not connect to %s after %d attempts.", name, max_retries)
    raise ConnectionError(f"Failed to connect to {name}")
