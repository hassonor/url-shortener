# interface/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from domain.url_shortener_service import URLShortenerService
from infrastructure.database import database
from infrastructure.redis_client import redis_client
from application.messaging.publishers import publish_url_created
from infrastructure.config import settings
from infrastructure.bloom import bloom_filter, bloom_lock
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="URL Shortener API", version="1.0.0")

class ShortenRequest(BaseModel):
    longUrl: str

@app.on_event("startup")
async def startup():
    app.state.bloom_filter = bloom_filter
    app.state.bloom_lock = bloom_lock

@app.post("/shorten")
async def shorten(request: ShortenRequest):
    service = URLShortenerService(database, redis_client, app.state.bloom_filter, app.state.bloom_lock)
    short_code, newly_created = await service.shorten_url(request.longUrl)
    if not short_code:
        raise HTTPException(status_code=400, detail="Invalid URL")

    if newly_created:
        await publish_url_created(short_code, request.longUrl)

    return {"shortUrl": f"{settings.BASE_URL}/{short_code}"}

@app.get("/{short_code}")
async def redirect_short_code(short_code: str):
    service = URLShortenerService(database, redis_client, app.state.bloom_filter, app.state.bloom_lock)
    long_url = await service.get_long_url(short_code)
    if not long_url:
        raise HTTPException(status_code=404, detail="Not Found")
    # Return a real redirect
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=long_url, status_code=301)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "url_shortener"}

@app.get("/metrics")
async def metrics():
    # Expose prometheus metrics
    from starlette.responses import Response
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
