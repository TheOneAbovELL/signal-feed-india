from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str
    color: str
    category: str


@dataclass(frozen=True)
class Settings:
    poll_interval_seconds: int = 45
    trend_window_minutes: int = 24
    max_headlines: int = 120
    feeds: list[FeedSource] = field(
        default_factory=lambda: [
            FeedSource("The Hindu", "https://www.thehindu.com/news/national/feeder/default.rss", "#ff6b00", "India"),
            FeedSource("Indian Express", "https://indianexpress.com/section/india/feed/", "#00d4ff", "India"),
            FeedSource("NDTV", "https://feeds.feedburner.com/ndtvnews-top-stories", "#00c853", "India"),
            FeedSource("Hindustan Times", "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml", "#f43f5e", "India"),
            FeedSource("Moneycontrol", "https://www.moneycontrol.com/rss/business.xml", "#ffd166", "Business"),
            FeedSource("LiveMint", "https://www.livemint.com/rss/news", "#7c3aed", "Business"),
            FeedSource("ESPN Cricinfo", "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "#00bcd4", "Sports"),
            FeedSource("TechCrunch", "https://techcrunch.com/feed/", "#94d82d", "Tech"),
            FeedSource("BBC News", "https://feeds.bbci.co.uk/news/rss.xml", "#ff4040", "Global"),
            FeedSource("Reuters", "https://feeds.reuters.com/reuters/topNews", "#0091ea", "Global"),
        ]
    )


settings = Settings()
