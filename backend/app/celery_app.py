"""
FileForge – Celery application factory
Imported by both the backend (for task dispatch) and the worker container.
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "fileforge",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_RESULT_URL,
    include=["app.tasks.process_file"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS,
    # Result expiry matches file TTL
    result_expires=settings.FILE_TTL_SECONDS,
    # Retry on connection errors
    broker_connection_retry_on_startup=True,
)
