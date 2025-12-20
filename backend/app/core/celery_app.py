# app/core/celery_app.py - Celery application configuration

from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "bc_legal_tech",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.document_processing",
        "app.tasks.feedback_tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    task_acks_late=True,  # Acknowledge task after completion
    worker_prefetch_multiplier=1,  # Take one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
)

# Task routing (can add more queues later for priority)
celery_app.conf.task_routes = {
    "app.tasks.document_processing.*": {"queue": "document_processing"},
}

# Optional: Configure retry behavior
celery_app.conf.task_default_retry_delay = 60  # Retry after 60 seconds
celery_app.conf.task_max_retries = 3  # Max 3 retries

# Celery Beat schedule for periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Check feedback alert thresholds every 15 minutes
    "check-feedback-alerts-every-15-min": {
        "task": "check_feedback_alert_thresholds",
        "schedule": crontab(minute="*/15"),
    },
    # Compute feedback aggregates every hour
    "compute-feedback-aggregates-hourly": {
        "task": "compute_feedback_aggregates",
        "schedule": crontab(minute=0),  # At the start of each hour
    },
    # Resolve stale alerts every hour
    "resolve-stale-alerts-hourly": {
        "task": "resolve_stale_alerts",
        "schedule": crontab(minute=30),  # 30 minutes past each hour
    },
}
