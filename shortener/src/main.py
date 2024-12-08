import asyncio
import signal
import logging
from infrastructure.config import settings
from infrastructure.metrics import start_metrics_server
from infrastructure.database import database
from infrastructure.redis_client import redis_client
from infrastructure.kafka_client import kafka_client
from application.messaging.callbacks import message_callback
from application.server_runner import run_api_server
from application.shutdown import shutdown

logger = logging.getLogger(__name__)

async def main():
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
        [api_task, consumer_task],
        return_when=asyncio.FIRST_EXCEPTION
    )

    for task in pending:
        task.cancel()

    logger.info("Shutting down gracefully...")
    await redis_client.close()
    await database.close()
    await kafka_client.close()
    logger.info("Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())
