from typing import Any

from celery import Celery
from celery.signals import setup_logging

from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()

celery_app = Celery("samvid", include=["app.workers.tasks"])
celery_app.conf.update(
    broker_url=settings.redis_url.get_secret_value(),
    # Results aren't stored: a task's return value could carry data nobody means to keep in Redis.
    task_ignore_result=True,
    # JSON only. Celery's pickle support would turn anything able to write to the broker into code
    # execution on the workers.
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=60,
    task_time_limit=90,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
    # Filled in as the jobs arrive: SLA scan in 5.1, authorisation outbox in 3.1.
    beat_schedule={},
)


@setup_logging.connect  # type: ignore[untyped-decorator]
def _use_phi_safe_logging(**_: Any) -> None:
    configure_logging(settings.log_level)
