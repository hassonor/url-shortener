import asyncio
import logging
import random
import time

import pybreaker
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from infrastructure.config import settings
from infrastructure.metrics import (
    kafka_produce_failure,
    kafka_produce_latency,
    kafka_produce_success,
)

logger = logging.getLogger(__name__)

kafka_producer_breaker = pybreaker.CircuitBreaker(
    fail_max=3, reset_timeout=30, name="kafka_producer_circuit_breaker"
)


class KafkaClient:
    def __init__(self):
        self.producer = None
        self.consumer = None
        self.producer_connected = False
        self.consumer_connected = False
        self._closing = False

    async def connect_producer(self):
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            if self._closing:
                logger.info(
                    {
                        "action": "connect_producer",
                        "status": "aborted",
                        "message": "Shutdown in progress.",
                    }
                )
                return
            try:
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
                )
                await self.producer.start()
                self.producer_connected = True
                logger.info(
                    {
                        "action": "connect_producer",
                        "status": "connected",
                        "attempt": attempt,
                    }
                )
                return
            except Exception as e:
                logger.warning(
                    {
                        "action": "connect_producer",
                        "status": "failure",
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "error": str(e),
                    }
                )

                if attempt < max_retries:
                    delay = min(10, 2**attempt + random.uniform(0, 1))
                    logger.info(
                        {
                            "action": "connect_producer",
                            "status": "retrying",
                            "delay_seconds": delay,
                        }
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error({"action": "connect_producer", "status": "failed_all_retries"})
                    raise

    async def connect_consumer(self, topic: str, group_id: str = "url_shortener_group"):
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            if self._closing:
                logger.info({"action": "connect_consumer", "status": "aborted", "topic": topic})
                return
            try:
                self.consumer = AIOKafkaConsumer(
                    topic,
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    group_id=group_id,
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                )
                await self.consumer.start()
                self.consumer_connected = True
                logger.info(
                    {
                        "action": "connect_consumer",
                        "topic": topic,
                        "status": "connected",
                        "attempt": attempt,
                    }
                )
                return
            except Exception as e:
                logger.warning(
                    {
                        "action": "connect_consumer",
                        "topic": topic,
                        "status": "failure",
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "error": str(e),
                    }
                )
                if attempt < max_retries:
                    delay = min(10, 2**attempt + random.uniform(0, 1))
                    logger.info(
                        {
                            "action": "connect_consumer",
                            "topic": topic,
                            "status": "retrying",
                            "delay": delay,
                        }
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        {
                            "action": "connect_consumer",
                            "topic": topic,
                            "status": "failed_all_retries",
                        }
                    )
                    raise

    @kafka_producer_breaker
    async def _produce_with_breaker(self, topic: str, message: bytes):
        if not self.producer or not self.producer_connected:
            await self.connect_producer()
        start_time = time.time()
        await self.producer.send_and_wait(topic, message)
        elapsed = time.time() - start_time
        kafka_produce_latency.observe(elapsed)
        kafka_produce_success.inc()
        logger.debug({"action": "produce_message", "topic": topic, "status": "produced"})

    async def produce(self, topic: str, message: bytes):
        if self._closing:
            logger.warning(
                {
                    "action": "produce_message",
                    "topic": topic,
                    "status": "shutdown_in_progress",
                }
            )
            return
        try:
            await self._produce_with_breaker(topic, message)
        except pybreaker.CircuitBreakerError:
            logger.warning({"action": "produce_message", "topic": topic, "status": "circuit_open"})
            kafka_produce_failure.inc()
            # Optionally fallback to dead-letter if needed
            raise
        except Exception as e:
            kafka_produce_failure.inc()
            logger.exception(
                {
                    "action": "produce_message",
                    "topic": topic,
                    "status": "failure",
                    "error": str(e),
                }
            )
            # Optionally fallback here
            raise

    async def consume_forever(self, callback):
        if not self.consumer or not self.consumer_connected:
            logger.warning({"action": "consume_forever", "status": "no_consumer"})
            return
        try:
            async for msg in self.consumer:
                if self._closing:
                    logger.info({"action": "consume_forever", "status": "shutting_down"})
                    break
                await callback(msg.value)
        except asyncio.CancelledError:
            logger.info({"action": "consume_forever", "status": "cancelled"})
        except Exception as e:
            logger.exception({"action": "consume_forever", "status": "error", "error": str(e)})

    async def close(self):
        self._closing = True
        if self.producer and self.producer_connected:
            await self.producer.stop()
            self.producer_connected = False
            logger.info({"action": "close_producer", "status": "closed"})

        if self.consumer and self.consumer_connected:
            await self.consumer.stop()
            self.consumer_connected = False
            logger.info({"action": "close_consumer", "status": "closed"})


kafka_client = KafkaClient()
