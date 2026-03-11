from __future__ import annotations

import asyncio
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from .classifier import extract_keywords
from .config import settings
from .models import Story


class DashboardStore:
    def __init__(self) -> None:
        self._stories: list[Story] = []
        self._seen_ids: set[str] = set()
        self._lock = asyncio.Lock()

    async def add_stories(self, stories: list[Story]) -> list[Story]:
        added: list[Story] = []
        async with self._lock:
            for story in sorted(stories, key=lambda item: item.published_at, reverse=True):
                if story.id in self._seen_ids:
                    continue
                self._seen_ids.add(story.id)
                self._stories.insert(0, story)
                added.append(story)
            self._stories = sorted(self._stories, key=lambda item: item.published_at, reverse=True)[: settings.max_headlines]
            self._seen_ids = {story.id for story in self._stories}
        return added

    async def snapshot(self) -> dict[str, object]:
        async with self._lock:
            stories = list(self._stories)

        now = datetime.now(timezone.utc)
        topics = Counter(topic for story in stories for topic in story.topics)
        sources = Counter(story.source for story in stories)
        sentiments = Counter(story.sentiment for story in stories)
        regions = Counter(region for story in stories for region in story.regions)
        hashtags = Counter(tag for story in stories for tag in story.hashtags)
        source_categories = Counter(story.source_category for story in stories)
        timeline = self._timeline(stories, now)
        trending = extract_keywords([f"{story.title} {story.summary}" for story in stories[:80]], limit=18)
        social_leaders = sorted(stories, key=lambda story: (story.social_score, story.published_at), reverse=True)[:8]

        return {
            "generated_at": now.isoformat(),
            "story_count": len(stories),
            "headlines": [story.to_dict() for story in stories[:30]],
            "topic_totals": dict(topics),
            "source_totals": dict(sources),
            "source_categories": dict(source_categories),
            "sentiment_totals": dict(sentiments),
            "region_totals": dict(regions),
            "hashtags": [{"tag": tag, "count": count} for tag, count in hashtags.most_common(14)],
            "social_leaders": [story.to_dict() for story in social_leaders],
            "trending": trending,
            "timeline": timeline,
            "summary_cards": self._summary_cards(stories, topics, regions, hashtags),
        }

    def _summary_cards(
        self,
        stories: list[Story],
        topics: Counter[str],
        regions: Counter[str],
        hashtags: Counter[str],
    ) -> list[dict[str, str | int]]:
        lead_story = max(stories, key=lambda story: story.social_score, default=None)
        cards = [
            {
                "label": "Top India Region",
                "value": next(iter(regions.keys()), "Global"),
                "subtext": f"{next(iter(regions.values()), 0)} live mentions",
            },
            {
                "label": "Hottest Topic",
                "value": next(iter(topics.keys()), "General"),
                "subtext": f"{next(iter(topics.values()), 0)} matching stories",
            },
            {
                "label": "Top Hashtag",
                "value": next(iter(hashtags.keys()), "#SignalFeed"),
                "subtext": "Derived social conversation cue",
            },
            {
                "label": "Lead Alert",
                "value": str(lead_story.social_score) if lead_story else "0",
                "subtext": lead_story.title[:60] + ("..." if lead_story and len(lead_story.title) > 60 else "") if lead_story else "No live story yet",
            },
        ]
        return cards

    def _timeline(self, stories: list[Story], now: datetime) -> list[dict[str, object]]:
        buckets: dict[str, dict[str, int]] = defaultdict(dict)
        for minute_offset in range(settings.trend_window_minutes - 1, -1, -1):
            stamp = (now - timedelta(minutes=minute_offset)).replace(second=0, microsecond=0)
            buckets[stamp.isoformat()] = {"total": 0}

        for story in stories:
            bucket = story.published_at.replace(second=0, microsecond=0).isoformat()
            if bucket not in buckets:
                continue
            buckets[bucket]["total"] = buckets[bucket].get("total", 0) + 1
            for topic in story.topics:
                buckets[bucket][topic] = buckets[bucket].get(topic, 0) + 1

        return [{"minute": minute, **values} for minute, values in buckets.items()]


store = DashboardStore()
