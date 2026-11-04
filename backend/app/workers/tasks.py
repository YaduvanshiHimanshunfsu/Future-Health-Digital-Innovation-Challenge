from app.workers.celery_app import celery_app


@celery_app.task(name="samvid.ping")  # type: ignore[untyped-decorator]
def ping() -> str:
    return "pong"
