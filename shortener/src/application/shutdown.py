import asyncio
import logging

logger = logging.getLogger(__name__)


async def shutdown():
    """
    Gracefully shut down the service by cancelling all running tasks and waiting for them to finish.
    """
    logger.info(
        {
            "action": "shutdown",
            "message": "Shutdown signal received. Stopping service...",
        }
    )

    # Get all tasks except the current one
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    if not tasks:
        logger.info(
            {
                "action": "shutdown",
                "message": "No running tasks found. Shutdown complete.",
            }
        )
        return

    # Request cancellation
    for task in tasks:
        task.cancel()

    logger.info(
        {
            "action": "shutdown",
            "message": "Cancelled all running tasks. Waiting for them to finish...",
        }
    )

    # Wait briefly for tasks to finish
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.exception({"action": "shutdown", "error": str(e)})

    logger.info(
        {
            "action": "shutdown",
            "message": "All tasks completed or cancelled. Shutdown complete.",
        }
    )
