from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str
    color: str
    category: str
    credibility_score: float
    bias_label: str
    quality_tier: str
    transparency_note: str


def _default_feeds() -> list[FeedSource]:
    return [
        FeedSource("The Hindu", "https://www.thehindu.com/news/national/feeder/default.rss", "#ff6b00", "India", 0.92, "Center", "Tier 1", "Strong editorial standards and transparent corrections policy."),
        FeedSource("Indian Express", "https://indianexpress.com/section/india/feed/", "#00d4ff", "India", 0.9, "Center", "Tier 1", "High newsroom transparency with broad national coverage."),
        FeedSource("NDTV", "https://feeds.feedburner.com/ndtvnews-top-stories", "#00c853", "India", 0.86, "Center", "Tier 1", "Established broadcast brand with mixed original and syndicated reporting."),
        FeedSource("Hindustan Times", "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml", "#f43f5e", "India", 0.85, "Center", "Tier 1", "Large national publisher with strong beat coverage."),
        FeedSource("Moneycontrol", "https://www.moneycontrol.com/rss/business.xml", "#ffd166", "Business", 0.88, "Center", "Tier 1", "High-frequency financial reporting with market-specific expertise."),
        FeedSource("LiveMint", "https://www.livemint.com/rss/news", "#7c3aed", "Business", 0.89, "Center", "Tier 1", "Strong business desk and explanatory reporting."),
        FeedSource("ESPN Cricinfo", "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "#00bcd4", "Sports", 0.9, "Center", "Tier 1", "Specialist sports reporting with deep cricket coverage."),
        FeedSource("TechCrunch", "https://techcrunch.com/feed/", "#94d82d", "Tech", 0.82, "Center", "Tier 2", "Strong startup and tech reporting with fast-moving publishing cadence."),
        FeedSource("BBC News", "https://feeds.bbci.co.uk/news/rss.xml", "#ff4040", "Global", 0.95, "Center", "Tier 1", "Global public-service newsroom with rigorous editorial process."),
        FeedSource("Reuters", "https://feeds.reuters.com/reuters/topNews", "#0091ea", "Global", 0.97, "Center", "Tier 1", "Wire service with high credibility and strong sourcing discipline."),
    ]


def _load_env_file() -> None:
    env_path = os.getenv("SIGNAL_FEED_ENV_FILE", ".env")
    if not os.path.exists(env_path):
        return
    for line in open(env_path, encoding="utf-8"):
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()


def _load_feeds() -> list[FeedSource]:
    raw = os.getenv("SIGNAL_FEEDS_JSON")
    if not raw:
        return _default_feeds()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return _default_feeds()
    feeds: list[FeedSource] = []
    for item in payload:
        feeds.append(FeedSource(**item))
    return feeds or _default_feeds()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Signal Feed India")
    app_version: str = os.getenv("APP_VERSION", "4.0.0")
    environment: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./signal_feed.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    secret_key: str = os.getenv("SIGNAL_FEED_SECRET", "change-me-in-production")
    access_token_hours: int = int(os.getenv("ACCESS_TOKEN_HOURS", "12"))
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "45"))
    trend_window_minutes: int = int(os.getenv("TREND_WINDOW_MINUTES", "24"))
    max_headlines: int = int(os.getenv("MAX_HEADLINES", "120"))
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "30"))
    enable_redis: bool = os.getenv("ENABLE_REDIS", "false").lower() == "true"
    enable_scheduler: bool = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
    enable_alerting: bool = os.getenv("ENABLE_ALERTING", "true").lower() == "true"
    enable_ml_classification: bool = os.getenv("ENABLE_ML_CLASSIFICATION", "false").lower() == "true"
    enable_story_clustering: bool = os.getenv("ENABLE_STORY_CLUSTERING", "true").lower() == "true"
    feeds: list[FeedSource] = field(default_factory=_load_feeds)


settings = Settings()
