import json
import logging
from infrastructure.config import settings
from infrastructure.kafka_client import kafka_client

logger = logging.getLogger(__name__)

async def publish_url_created(short_code: str, long_url: str):
    """Publish an event when a new URL is created."""
    message = {
        "event": "URL_CREATED",
        "short_code": short_code,
        "long_url": long_url
    }
    try:
        await kafka_client.produce(settings.URL_CREATED_TOPIC, json.dumps(message).encode())
        logger.info("Published URL_CREATED event for short_code: %s", short_code)
    except Exception as e:
        logger.exception("Failed to publish URL_CREATED event: %s", e)
