"""Dramatiq broker configuration.

Dramatiq was chosen over Celery for a simpler Redis-backed actor model with
retries, while remaining strong enough for multi-stage import jobs.
"""

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import AgeLimit, Callbacks, Retries, TimeLimit

from app.core.config import get_settings

settings = get_settings()
redis_broker = RedisBroker(url=settings.redis_url)
redis_broker.add_middleware(AgeLimit())
redis_broker.add_middleware(TimeLimit())
redis_broker.add_middleware(Callbacks())
redis_broker.add_middleware(Retries(max_retries=3))
dramatiq.set_broker(redis_broker)
