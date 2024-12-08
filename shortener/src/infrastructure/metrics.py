from prometheus_client import Counter, Histogram, start_http_server
import logging

logger = logging.getLogger(__name__)

url_created = Counter('url_shortener_created_total', 'Number of URLs shortened')
url_lookup_latency = Histogram('url_lookup_latency_seconds', 'Time to lookup long URL by short code')

def start_metrics_server(port: int = 8000):
    try:
        start_http_server(port)
        logger.info("Prometheus metrics server started on port %d", port)
    except Exception as e:
        logger.exception("Failed to start metrics server: %s", e)
        raise
