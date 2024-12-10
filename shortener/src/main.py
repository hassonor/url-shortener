import asyncio
import logging
import signal

from application.messaging.callbacks import message_callback
from application.server_runner import run_api_server
from application.shutdown import shutdown
from infrastructure.config import settings
from infrastructure.database import database
from infrastructure.kafka_client import kafka_client
from infrastructure.metrics import start_metrics_server
from infrastructure.redis_client import redis_client

logger = logging.getLogger(__name__)


async def main():
    logger.info({"action": "startup", "message": "Starting application"})

    await database.connect()
    await redis_client.connect()
    await kafka_client.connect_producer()
    await kafka_client.connect_consumer(settings.URL_CREATED_TOPIC)

    start_metrics_server(port=settings.METRICS_PORT)

    api_task = asyncio.create_task(run_api_server(host="0.0.0.0", port=8001))
    consumer_task = asyncio.create_task(kafka_client.consume_forever(message_callback))

    loop = asyncio.get_event_loop()
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, lambda: asyncio.create_task(shutdown()))

    done, pending = await asyncio.wait(
        [api_task, consumer_task], return_when=asyncio.FIRST_EXCEPTION
    )

    for task in pending:
        task.cancel()

    logger.info({"action": "shutdown", "message": "Shutting down gracefully..."})
    await redis_client.close()
    await database.close()
    await kafka_client.close()
    logger.info({"action": "shutdown", "message": "Shutdown complete."})


if __name__ == "__main__":
    # Ensure logging is set up if not already done in logging_config.py
    from infrastructure.logging_config import setup_logging

    setup_logging()

    asyncio.run(main())
