import logging
import asyncio
import random
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from infrastructure.config import settings

logger = logging.getLogger(__name__)

class KafkaClient:
    def __init__(self):
        self.producer = None
        self.consumer = None
        self.producer_connected = False
        self.consumer_connected = False

    async def connect_producer(self):
        max_retries = 5
        base_delay = 5
        for attempt in range(1, max_retries + 1):
            try:
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
                )
                await self.producer.start()
                self.producer_connected = True
                logger.info("Kafka producer connected.")
                return
            except Exception as e:
                logger.warning("Failed to connect Kafka Producer (attempt %d): %s", attempt, e)
                if attempt < max_retries:
                    delay = base_delay * attempt + random.uniform(0, 1)
                    logger.info("Retrying in %.2f seconds...", delay)
                    await asyncio.sleep(delay)
                else:
                    logger.error("Could not connect to Kafka Producer after %d attempts.", max_retries)
                    raise

    async def connect_consumer(self, topic: str, group_id: str = "url_shortener_group"):
        max_retries = 5
        base_delay = 5
        for attempt in range(1, max_retries + 1):
            try:
                self.consumer = AIOKafkaConsumer(
                    topic,
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    group_id=group_id,
                    auto_offset_reset='earliest',
                    enable_auto_commit=True
                )
                await self.consumer.start()
                self.consumer_connected = True
                logger.info("Kafka consumer connected to topic %s.", topic)
                return
            except Exception as e:
                logger.warning("Failed to connect Kafka Consumer (attempt %d): %s", attempt, e)
                if attempt < max_retries:
                    delay = base_delay * attempt + random.uniform(0, 1)
                    logger.info("Retrying in %.2f seconds...", delay)
                    await asyncio.sleep(delay)
                else:
                    logger.error("Could not connect to Kafka Consumer after %d attempts.", max_retries)
                    raise

    async def produce(self, topic: str, message: bytes):
        if not self.producer or not self.producer_connected:
            await self.connect_producer()
        await self.producer.send_and_wait(topic, message)

    async def consume_forever(self, callback):
        if not self.consumer or not self.consumer_connected:
            return  # or wait until connected
        try:
            async for msg in self.consumer:
                await callback(msg.value)
        except asyncio.CancelledError:
            logger.info("Kafka consumer cancelled.")
        except Exception as e:
            logger.exception("Error in consume_forever: %s", e)

    async def close(self):
        if self.producer and self.producer_connected:
            await self.producer.stop()
            self.producer_connected = False
            logger.info("Kafka producer closed gracefully.")

        if self.consumer and self.consumer_connected:
            await self.consumer.stop()
            self.consumer_connected = False
            logger.info("Kafka consumer closed gracefully.")

kafka_client = KafkaClient()
