import json
import logging
import time

import pybreaker
import redis.asyncio as redis
from infrastructure.config import settings
from infrastructure.kafka_client import kafka_client
from infrastructure.metrics import (
    kafka_produce_failure,
    kafka_produce_latency,
    kafka_produce_success,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class KafkaPublishError(Exception):
    """Custom exception to signal transient failure in publishing to Kafka."""


# Circuit breaker for publishing events
publish_breaker = pybreaker.CircuitBreaker(
    fail_max=3, reset_timeout=30, name="publish_circuit_breaker"
)

# Redis client for fallback dead-letter queue
fallback_redis = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(KafkaPublishError),
)
async def publish_url_created(
    short_code: str, long_url: str, correlation_id: str = None
):
    """
    Publish a "URL_CREATED" event to Kafka with retries, circuit breaker, and fallback.
    """
    message = {"event": "URL_CREATED", "short_code": short_code, "long_url": long_url}
    if correlation_id:
        message["correlation_id"] = correlation_id

    message_bytes = json.dumps(message).encode("utf-8")
    topic = settings.URL_CREATED_TOPIC

    logger.debug(
        {
            "action": "publish_url_created",
            "topic": topic,
            "short_code": short_code,
            "long_url": long_url,
            "correlation_id": correlation_id,
            "status": "attempting",
        }
    )

    if publish_breaker.current_state == pybreaker.STATE_OPEN:
        logger.warning(
            {
                "action": "publish_url_created",
                "status": "circuit_open",
                "topic": topic,
                "short_code": short_code,
                "long_url": long_url,
                "correlation_id": correlation_id,
            }
        )
        await fallback_dead_letter(message)
        return

    start_time = time.time()
    try:

        @publish_breaker
        async def attempt_publish():
            await kafka_client.produce(topic, message_bytes)

        await attempt_publish()
        elapsed = time.time() - start_time
        kafka_produce_latency.observe(elapsed)
        kafka_produce_success.inc()
        logger.info(
            {
                "action": "publish_url_created",
                "status": "published",
                "topic": topic,
                "short_code": short_code,
                "long_url": long_url,
                "correlation_id": correlation_id,
            }
        )
    except pybreaker.CircuitBreakerError:
        logger.warning(
            {
                "action": "publish_url_created",
                "status": "circuit_open_during_attempt",
                "topic": topic,
                "short_code": short_code,
                "long_url": long_url,
                "correlation_id": correlation_id,
            }
        )
        kafka_produce_failure.inc()
        await fallback_dead_letter(message)
    except Exception as e:
        kafka_produce_failure.inc()
        logger.warning(
            {
                "action": "publish_url_created",
                "status": "transient_failure",
                "error": str(e),
                "topic": topic,
                "short_code": short_code,
                "long_url": long_url,
                "correlation_id": correlation_id,
            }
        )
        raise KafkaPublishError("Failed to publish to Kafka") from e


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
async def fallback_dead_letter(message: dict):
    """
    Store the failed event message in a dead-letter queue for later reprocessing.
    """
    try:
        msg_str = json.dumps(message)
        await fallback_redis.rpush("dead_letter_queue", msg_str)
        logger.error(
            {
                "action": "fallback_dead_letter",
                "status": "stored",
                "short_code": message.get("short_code"),
                "long_url": message.get("long_url"),
                "correlation_id": message.get("correlation_id"),
                "info": "Message stored in dead-letter queue",
            }
        )
    except Exception as e:
        logger.critical(
            {
                "action": "fallback_dead_letter",
                "status": "failed",
                "error": str(e),
                "short_code": message.get("short_code"),
                "long_url": message.get("long_url"),
                "correlation_id": message.get("correlation_id"),
                "info": "Could not store message in dead-letter queue",
            }
        )
        # After retries, if this fails, we have no further fallback.
        raise
