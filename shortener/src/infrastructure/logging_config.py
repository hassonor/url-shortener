import logging
import sys
from infrastructure.config import settings

def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        stream=sys.stdout
    )
    logger = logging.getLogger("url_shortener_service")
    logger.debug("Logging configured at level: %s", settings.LOG_LEVEL)
    return logger

logger = setup_logging()
