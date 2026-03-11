from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from typing import Any

import aiohttp
import feedparser

from .classifier import (
    classify_topics,
    detect_regions,
    estimate_social_score,
    extract_hashtags,
    recommended_platforms,
    score_sentiment,
)
from .config import FeedSource
from .models import Story
from .store import store


SAMPLE_STORIES = [
    {
        "source": "Demo Wire India",
        "source_color": "#00d4ff",
        "source_category": "India",
        "title": "Bengaluru AI startups see fresh funding as enterprise demand rises",
        "summary": "Investors back applied AI and SaaS companies as Indian software exports strengthen.",
        "link": "https://example.com/bengaluru-startups",
    },
    {
        "source": "Demo Wire India",
        "source_color": "#00c853",
        "source_category": "Climate",
        "title": "Mumbai flood alerts widen after heavy rain hits key commuter corridors",
        "summary": "Emergency teams prepare for disruption as monsoon pressure intensifies across Maharashtra.",
        "link": "https://example.com/mumbai-rain",
    },
    {
        "source": "Demo Wire India",
        "source_color": "#ffd166",
        "source_category": "Business",
        "title": "Policy and budget buzz lifts banking and infrastructure counters",
        "summary": "Market watchers rotate into public capex and logistics themes across Dalal Street.",
        "link": "https://example.com/budget-buzz",
    },
    {
        "source": "Demo Wire India",
        "source_color": "#ff4d6d",
        "source_category": "Sports",
        "title": "IPL chatter spikes as franchise strategy and player fitness dominate previews",
        "summary": "Fans and analysts track form, auction value, and opening combinations before the next matchday.",
        "link": "https://example.com/ipl-chatter",
    },
]


def _published(entry: Any) -> datetime:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return datetime.now(timezone.utc)
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _story_id(source: str, title: str, link: str) -> str:
    return hashlib.sha1(f"{source}|{title}|{link}".encode("utf-8")).hexdigest()


def _build_story(
    source: str,
    source_color: str,
    source_category: str,
    title: str,
    summary: str,
    link: str,
    published_at: datetime,
) -> Story:
    combined = f"{title} {summary}"
    topics = classify_topics(combined)
    regions = detect_regions(combined)
    return Story(
        id=_story_id(source, title, link),
        source=source,
        source_color=source_color,
        source_category=source_category,
        title=title,
        link=link,
        summary=summary,
        published_at=published_at,
        topics=topics,
        sentiment=score_sentiment(combined),
        regions=regions,
        hashtags=extract_hashtags(combined),
        social_score=estimate_social_score(combined, source, topics),
        social_platforms=recommended_platforms(topics, regions),
    )


async def fetch_feed(session: aiohttp.ClientSession, feed: FeedSource) -> list[Story]:
    async with session.get(feed.url, timeout=aiohttp.ClientTimeout(total=15)) as response:
        response.raise_for_status()
        body = await response.text()
    parsed = feedparser.parse(body)
    stories: list[Story] = []
    for entry in parsed.entries[:12]:
        stories.append(
            _build_story(
                source=feed.name,
                source_color=feed.color,
                source_category=feed.category,
                title=entry.get("title", "Untitled"),
                summary=entry.get("summary", ""),
                link=entry.get("link", "#"),
                published_at=_published(entry),
            )
        )
    return stories


async def fetch_all_feeds(feeds: list[FeedSource]) -> list[Story]:
    headers = {"User-Agent": "SignalFeedIndia/2.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [fetch_feed(session, feed) for feed in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    stories: list[Story] = []
    for result in results:
        if isinstance(result, Exception):
            continue
        stories.extend(result)

    if stories:
        stories.sort(key=lambda story: story.published_at, reverse=True)
        return stories

    now = datetime.now(timezone.utc)
    return [
        _build_story(
            item["source"],
            item["source_color"],
            item["source_category"],
            item["title"],
            item["summary"],
            item["link"],
            now,
        )
        for item in SAMPLE_STORIES
    ]


async def ingest_once(feeds: list[FeedSource]) -> list[Story]:
    return await store.add_stories(await fetch_all_feeds(feeds))
