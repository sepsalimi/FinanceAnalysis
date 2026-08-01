"""Background Dramatiq actors for import and analytics work."""

import dramatiq

from app.workers.broker import redis_broker  # noqa: F401  # ensure broker is configured


@dramatiq.actor(max_retries=3)
def ping_worker() -> str:
    return "ok"


@dramatiq.actor(max_retries=3)
def enqueue_normalize(snapshot_id: str) -> str:
    """Placeholder actor hook; API currently runs normalize synchronously for reliability.

    Future work can move confirm_and_normalize into this actor once job status polling
    is wired end-to-end in the UI.
    """
    return snapshot_id
