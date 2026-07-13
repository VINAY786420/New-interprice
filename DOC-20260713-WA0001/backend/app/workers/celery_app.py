"""Celery application configuration."""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "social_data_vault",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-records": {
        "task": "app.workers.tasks.cleanup_old_records",
        "schedule": 86400.0,  # Daily
    },
    "update-proxy-health": {
        "task": "app.workers.tasks.update_proxy_health",
        "schedule": 300.0,  # Every 5 minutes
    },
    "generate-daily-reports": {
        "task": "app.workers.tasks.generate_daily_reports",
        "schedule": 86400.0,
    },
}
