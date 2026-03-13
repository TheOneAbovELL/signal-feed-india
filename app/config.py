from __future__ import annotations

from dataclasses import dataclass, field
import os


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


@dataclass(frozen=True)
class Settings:
    app_name: str = "Signal Feed India"
    app_version: str = "3.0.0"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./signal_feed.db")
    secret_key: str = os.getenv("SIGNAL_FEED_SECRET", "change-me-in-production")
    access_token_hours: int = int(os.getenv("ACCESS_TOKEN_HOURS", "12"))
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "45"))
    trend_window_minutes: int = int(os.getenv("TREND_WINDOW_MINUTES", "24"))
    max_headlines: int = int(os.getenv("MAX_HEADLINES", "120"))
    feeds: list[FeedSource] = field(
        default_factory=lambda: [
            FeedSource(
                "The Hindu",
                "https://www.thehindu.com/news/national/feeder/default.rss",
                "#ff6b00",
                "India",
                0.92,
                "Center",
                "Tier 1",
                "Strong editorial standards and transparent corrections policy.",
            ),
            FeedSource(
                "Indian Express",
                "https://indianexpress.com/section/india/feed/",
                "#00d4ff",
                "India",
                0.9,
                "Center",
                "Tier 1",
                "High newsroom transparency with broad national coverage.",
            ),
            FeedSource(
                "NDTV",
                "https://feeds.feedburner.com/ndtvnews-top-stories",
                "#00c853",
                "India",
                0.86,
                "Center",
                "Tier 1",
                "Established broadcast brand with mixed original and syndicated reporting.",
            ),
            FeedSource(
                "Hindustan Times",
                "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
                "#f43f5e",
                "India",
                0.85,
                "Center",
                "Tier 1",
                "Large national publisher with strong beat coverage.",
            ),
            FeedSource(
                "Moneycontrol",
                "https://www.moneycontrol.com/rss/business.xml",
                "#ffd166",
                "Business",
                0.88,
                "Center",
                "Tier 1",
                "High-frequency financial reporting with market-specific expertise.",
            ),
            FeedSource(
                "LiveMint",
                "https://www.livemint.com/rss/news",
                "#7c3aed",
                "Business",
                0.89,
                "Center",
                "Tier 1",
                "Strong business desk and explanatory reporting.",
            ),
            FeedSource(
                "ESPN Cricinfo",
                "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
                "#00bcd4",
                "Sports",
                0.9,
                "Center",
                "Tier 1",
                "Specialist sports reporting with deep cricket coverage.",
            ),
            FeedSource(
                "TechCrunch",
                "https://techcrunch.com/feed/",
                "#94d82d",
                "Tech",
                0.82,
                "Center",
                "Tier 2",
                "Strong startup and tech reporting with fast-moving publishing cadence.",
            ),
            FeedSource(
                "BBC News",
                "https://feeds.bbci.co.uk/news/rss.xml",
                "#ff4040",
                "Global",
                0.95,
                "Center",
                "Tier 1",
                "Global public-service newsroom with rigorous editorial process.",
            ),
            FeedSource(
                "Reuters",
                "https://feeds.reuters.com/reuters/topNews",
                "#0091ea",
                "Global",
                0.97,
                "Center",
                "Tier 1",
                "Wire service with high credibility and strong sourcing discipline.",
            ),
        ]
    )


settings = Settings()
