from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .cache import cache
from .config import settings
from .feeds import ingest_once
from .persistence import list_all_alert_preferences
from .store import store


logger = logging.getLogger("signal-feed-tasks")


async def ingest_job() -> None:
    added = await ingest_once(settings.feeds)
    if added:
        cache.invalidate("snapshot:latest")
        cache.publish("snapshot_updates", {"added": len(added)})
    logger.info("Scheduled ingest complete. Added %s stories.", len(added))


async def alert_job() -> None:
    if not settings.enable_alerting:
        return

    snapshot = await store.snapshot()
    alerts = []
    for preference in list_all_alert_preferences():
        if not preference["enabled"]:
            continue

        matches = []
        for story in snapshot["headlines"]:
            if story["social_score"] < preference["min_social_score"]:
                continue
            if preference["topic"] and preference["topic"] not in story["topics"]:
                continue
            if preference["region"] and preference["region"] not in story["regions"]:
                continue
            matches.append(story)

        if matches:
            alerts.append(
                {
                    "preference_id": preference["id"],
                    "user_id": preference["user_id"],
                    "delivery_channel": preference["delivery_channel"],
                    "matches": len(matches),
                    "top_story_id": matches[0]["id"],
                    "top_story_title": matches[0]["title"],
                }
            )

    if alerts:
        cache.publish("alerts", alerts)
        logger.info("Alert evaluation emitted %s alert groups.", len(alerts))


scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler | None:
    global scheduler
    if not settings.enable_scheduler:
        return None
    if scheduler is not None:
        return scheduler
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(ingest_job, "interval", seconds=settings.poll_interval_seconds, id="ingest_job")
    scheduler.add_job(alert_job, "interval", seconds=max(settings.poll_interval_seconds, 60), id="alert_job")
    scheduler.start()
    return scheduler


def stop_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
