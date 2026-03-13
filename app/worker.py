from __future__ import annotations

import asyncio
import logging

from .config import settings
from .db import init_db
from .feeds import ingest_once
from .persistence import seed_sources


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("signal-feed-worker")


async def run_worker() -> None:
    init_db()
    seed_sources(settings.feeds)
    logger.info("Worker started. Polling %s feeds every %s seconds.", len(settings.feeds), settings.poll_interval_seconds)
    while True:
        added = await ingest_once(settings.feeds)
        logger.info("Ingestion cycle complete. Added %s new stories.", len(added))
        await asyncio.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run_worker())
