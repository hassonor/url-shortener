import asyncio
import logging

logger = logging.getLogger(__name__)

def shutdown():
    logger.info("Shutdown signal received. Stopping service...")
    for task in asyncio.all_tasks():
        task.cancel()
