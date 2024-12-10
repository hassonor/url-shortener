import json
import logging

logger = logging.getLogger(__name__)


async def message_callback(raw_message: bytes):
    """
    Process incoming URL shortener events for analytics or other processes.
    """
    try:
        data = json.loads(raw_message.decode())
        event = data.get("event")
        correlation_id = data.get("correlation_id")
        if event == "URL_CREATED":
            short_code = data.get("short_code")
            long_url = data.get("long_url")
            logger.info(
                {
                    "action": "message_callback",
                    "event": event,
                    "short_code": short_code,
                    "long_url": long_url,
                    "correlation_id": correlation_id,
                    "status": "processed",
                }
            )
        else:
            logger.debug(
                {"action": "message_callback", "status": "unknown_event", "event_data": data}
            )
    except Exception as e:
        logger.exception(
            {
                "action": "message_callback",
                "status": "failed",
                "error": str(e),
                "raw_message": raw_message.decode(errors="replace"),
            }
        )
