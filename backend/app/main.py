"""
FileForge – FastAPI Application Entry Point
"""
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import files, jobs, health

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 FileForge backend starting …")
    # Ensure storage directories exist
    for d in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
        os.makedirs(d, exist_ok=True)
        logger.info(f"  ✔ storage dir ready: {d}")
    # Initialise SQLite database
    init_db()
    logger.info("  ✔ database initialised")
    yield
    logger.info("🛑 FileForge backend shutting down …")


# ── App factory ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FileForge API",
    description="File conversion & processing service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ──────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = round((time.time() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    logger.debug(f"{request.method} {request.url.path} → {response.status_code} ({elapsed}ms)")
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(files.router,  prefix="/api/files", tags=["Files"])
app.include_router(jobs.router,   prefix="/api/jobs",  tags=["Jobs"])


# ── Static storage (outputs download) ─────────────────────────────────────────
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
app.mount("/storage/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "FileForge API", "version": "1.0.0", "docs": "/api/docs"}
