"""
logging_config.py

Configures logging for the URL shortener service.
"""

import logging
import sys
from shortener.src.infrastructure.config import settings

def setup_logging() -> logging.Logger:
    """
    Configure logging based on environment settings.
    """
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        stream=sys.stdout
    )
    logger = logging.getLogger("url_shortener_service")
    logger.debug("Logging configured at level: %s", settings.LOG_LEVEL)
    return logger

logger = setup_logging()
