"""Celery application configuration."""

from celery import Celery

from backend.settings import settings

celery_app = Celery(
    "erp",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks from all modules
celery_app.autodiscover_tasks(["backend.workers.tasks"])
