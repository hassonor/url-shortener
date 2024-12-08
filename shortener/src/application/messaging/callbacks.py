import logging
import json

logger = logging.getLogger(__name__)

async def message_callback(raw_message: bytes):
    """
    Process incoming URL shortener events for analytics or other processes.
    """
    try:
        data = json.loads(raw_message.decode())
        event = data.get("event")
        if event == "URL_CREATED":
            short_code = data.get("short_code")
            long_url = data.get("long_url")
            logger.info("Analytics: URL Created short_code=%s, long_url=%s", short_code, long_url)
        else:
            logger.debug("Unknown event: %s", data)
    except Exception as e:
        logger.exception("Failed to process incoming message: %s", e)
