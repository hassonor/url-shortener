import logging
import uuid

from application.messaging.publishers import publish_url_created
from domain.url_shortener_service import URLShortenerService
from fastapi import FastAPI, HTTPException, Request
from infrastructure.bloom import bloom_filter, bloom_lock
from infrastructure.config import settings
from infrastructure.database import database
from infrastructure.kafka_client import kafka_client
from infrastructure.redis_client import redis_client
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="URL Shortener API", version="1.0.0")


class ShortenRequest(BaseModel):
    longUrl: str


@app.on_event("startup")
async def startup():
    app.state.bloom_filter = bloom_filter
    app.state.bloom_lock = bloom_lock


def get_correlation_id(request: Request) -> str:
    # Try to extract correlation_id from headers, else generate one
    return request.headers.get("X-Correlation-Id", str(uuid.uuid4()))


@app.post("/shorten")
async def shorten(request: ShortenRequest, req: Request):
    correlation_id = get_correlation_id(req)

    service = URLShortenerService(
        database, redis_client, app.state.bloom_filter, app.state.bloom_lock
    )
    short_code, newly_created = await service.shorten_url(
        request.longUrl, correlation_id=correlation_id
    )
    if not short_code:
        logger.warning(
            {
                "action": "shorten",
                "status": "invalid_url",
                "long_url": request.longUrl,
                "correlation_id": correlation_id,
            }
        )
        raise HTTPException(status_code=400, detail="Invalid URL")

    if newly_created:
        await publish_url_created(
            short_code, request.longUrl, correlation_id=correlation_id
        )

    logger.info(
        {
            "action": "shorten",
            "status": "success",
            "short_code": short_code,
            "long_url": request.longUrl,
            "correlation_id": correlation_id,
        }
    )
    return {"shortUrl": f"{settings.BASE_URL}/{short_code}"}


@app.get("/health")
async def health_check():
    # Basic liveness check
    return {"status": "ok", "service": "url_shortener"}


@app.get("/ready")
async def readiness_check():
    # Attempt simple checks to ensure Kafka and DB are ready
    # For DB, simple query or rely on database connect
    # For Kafka, ensure producer is connected
    if not database.pool:
        return {"status": "not_ready", "reason": "database_not_connected"}, 503
    if not kafka_client.producer_connected:
        return {"status": "not_ready", "reason": "kafka_producer_not_connected"}, 503

    return {"status": "ready"}


@app.get("/metrics")
async def metrics():
    # Expose prometheus metrics
    from starlette.responses import Response

    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/{short_code}")
async def redirect_short_code(short_code: str, req: Request):
    correlation_id = get_correlation_id(req)
    service = URLShortenerService(
        database, redis_client, app.state.bloom_filter, app.state.bloom_lock
    )
    long_url = await service.get_long_url(short_code, correlation_id=correlation_id)
    if not long_url:
        logger.warning(
            {
                "action": "redirect",
                "status": "not_found",
                "short_code": short_code,
                "correlation_id": correlation_id,
            }
        )
        raise HTTPException(status_code=404, detail="Not Found")

    logger.info(
        {
            "action": "redirect",
            "status": "found",
            "short_code": short_code,
            "long_url": long_url,
            "correlation_id": correlation_id,
        }
    )

    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=long_url, status_code=301)
