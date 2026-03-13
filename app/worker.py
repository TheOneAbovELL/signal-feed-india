from __future__ import annotations

import asyncio
import logging

from .config import settings
from .db import init_db
from .persistence import seed_sources
from .tasks import start_scheduler


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("signal-feed-worker")


async def run_worker() -> None:
    init_db()
    seed_sources(settings.feeds)
    scheduler = start_scheduler()
    logger.info("Worker started with scheduler=%s redis=%s.", bool(scheduler), settings.enable_redis)
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(run_worker())
