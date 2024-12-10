import logging

from prometheus_client import Counter, Histogram, start_http_server

logger = logging.getLogger(__name__)

# Existing metrics from your code
url_created = Counter("url_shortener_created_total", "Number of URLs shortened")
url_lookup_latency = Histogram(
    "url_lookup_latency_seconds", "Time to lookup long URL by short code"
)

# New Kafka metrics
kafka_produce_success = Counter(
    "kafka_produce_success_total", "Count of successful Kafka message produces"
)
kafka_produce_failure = Counter(
    "kafka_produce_failure_total", "Count of failed Kafka message produces"
)
kafka_produce_latency = Histogram(
    "kafka_produce_latency_seconds", "Latency of producing messages to Kafka"
)

# New Database metrics
db_operations_success = Counter(
    "db_operations_success_total", "Count of successful DB operations"
)
db_operations_failure = Counter(
    "db_operations_failure_total", "Count of failed DB operations"
)
db_query_latency = Histogram("db_query_latency_seconds", "Latency of DB queries")


def start_metrics_server(port: int = 8000):
    """
    Start the Prometheus metrics server on the given port.

    This function should be called once at application startup.
    After calling it, any registered metrics will be exposed at /metrics.
    """
    try:
        start_http_server(port)
        logger.info(
            {
                "action": "start_metrics_server",
                "status": "started",
                "port": port,
                "message": f"Prometheus metrics server started on port {port}",
            }
        )
    except Exception as e:
        logger.exception(
            {
                "action": "start_metrics_server",
                "status": "failed",
                "error": str(e),
                "message": "Failed to start metrics server",
            }
        )
        raise
