"""
FileForge – Application Configuration
All settings are read from environment variables (with sane defaults).
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:80",
        "http://localhost",
        "http://frontend:3000",
    ]

    # ── Redis / Celery ───────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_RESULT_URL: str = "redis://redis:6379/1"
    CELERY_TASK_SOFT_TIME_LIMIT: int = 270
    CELERY_TASK_TIME_LIMIT: int = 300
    CELERY_WORKER_MAX_TASKS: int = 200

    # ── Storage ──────────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "/app/storage/uploads"
    OUTPUT_DIR: str = "/app/storage/outputs"
    TEMP_DIR: str = "/app/storage/temp"
    FILE_TTL_SECONDS: int = 3600
    MAX_UPLOAD_MB: int = 500

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:////app/storage/fileforge.db"

    # ── Rate limiting ────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Flower ───────────────────────────────────────────────────────────────
    FLOWER_USER: str = "admin"
    FLOWER_PASSWORD: str = "fileforge"

    # ── Optional integrations ────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "us-east-1"
    SENTRY_DSN: str = ""

    @property
    def MAX_UPLOAD_BYTES(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
