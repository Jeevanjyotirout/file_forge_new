"""
FileForge – Health check endpoints
"""
import logging
import time

import redis as redis_lib
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings

router  = APIRouter()
logger  = logging.getLogger(__name__)
_start  = time.time()


@router.get("/health", summary="Health check")
async def health():
    uptime = round(time.time() - _start, 1)

    # Test Redis connectivity
    redis_ok = False
    try:
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        redis_ok = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")

    status = "ok" if redis_ok else "degraded"
    return JSONResponse(
        status_code=200 if redis_ok else 503,
        content={
            "status":   status,
            "uptime_s": uptime,
            "redis":    "ok" if redis_ok else "unreachable",
            "version":  "1.0.0",
        },
    )


@router.get("/health/ping", summary="Simple ping")
async def ping():
    return {"pong": True}
