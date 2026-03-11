from __future__ import annotations

from collections import Counter
import re


TOPIC_KEYWORDS = {
    "India": ["india", "indian", "delhi", "mumbai", "bengaluru", "bangalore", "chennai", "kolkata", "hyderabad", "pune"],
    "Governance": ["parliament", "cabinet", "minister", "government", "bjp", "congress", "assembly", "lok sabha", "rajya sabha"],
    "Startups": ["startup", "founder", "funding", "venture", "saas", "fintech", "unicorn", "incubator"],
    "Economy": ["market", "stock", "gdp", "inflation", "bank", "trade", "economy", "rupee", "sensex", "nifty"],
    "Climate": ["climate", "emission", "solar", "wind", "flood", "drought", "wildfire", "temperature", "monsoon"],
    "Infra & Mobility": ["railway", "metro", "airport", "highway", "ev", "mobility", "infrastructure", "transport"],
    "AI & Tech": ["ai", "machine learning", "gpt", "robot", "tech", "software", "data", "cyber", "chip"],
    "Geopolitics": ["war", "conflict", "nato", "diplomacy", "sanction", "military", "summit", "border"],
    "Science": ["research", "study", "discovery", "nasa", "space", "gene", "vaccine", "physics", "astronomy", "isro"],
    "Cricket": ["ipl", "bcci", "cricket", "odi", "test match", "t20", "wicket", "innings"],
    "Sports": ["football", "soccer", "nba", "nfl", "olympic", "league", "tournament", "medal"],
    "Culture": ["film", "movie", "music", "art", "book", "award", "fashion", "festival", "bollywood"],
}

POSITIVE = {"breakthrough", "success", "grow", "rise", "win", "peace", "recover", "surge", "record", "launch", "funding"}
NEGATIVE = {"war", "crisis", "crash", "fail", "attack", "death", "collapse", "threat", "disaster", "violence", "layoffs"}
STOP_WORDS = {
    "about", "which", "their", "there", "these", "those", "could", "would", "should", "being",
    "after", "before", "since", "until", "while", "where", "every", "other", "first", "second",
    "third", "under", "above", "across", "within", "between", "news", "live", "world", "india",
    "indian", "says", "amid", "today", "latest", "watch", "from",
}
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9'-]{2,}")
HASHTAG_RE = re.compile(r"[^a-zA-Z0-9]+")

INDIA_REGIONS = {
    "Delhi NCR": ["delhi", "ncr", "gurugram", "noida"],
    "Maharashtra": ["mumbai", "maharashtra", "pune", "nagpur"],
    "Karnataka": ["bengaluru", "bangalore", "karnataka", "mysuru"],
    "Tamil Nadu": ["chennai", "tamil nadu", "coimbatore"],
    "West Bengal": ["kolkata", "west bengal"],
    "Telangana": ["hyderabad", "telangana"],
    "Gujarat": ["gujarat", "ahmedabad"],
    "National": ["india", "parliament", "supreme court", "union budget"],
}


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def classify_topics(text: str) -> list[str]:
    lower = text.lower()
    matches = [topic for topic, keywords in TOPIC_KEYWORDS.items() if any(keyword in lower for keyword in keywords)]
    return matches or ["General"]


def score_sentiment(text: str) -> str:
    lower = text.lower()
    positive = sum(1 for token in POSITIVE if token in lower)
    negative = sum(1 for token in NEGATIVE if token in lower)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"


def extract_keywords(texts: list[str], limit: int = 12) -> list[dict[str, int | str]]:
    counts = Counter(
        token
        for text in texts
        for token in _tokens(text)
        if len(token) > 4 and token not in STOP_WORDS
    )
    return [{"word": word, "count": count} for word, count in counts.most_common(limit)]


def extract_hashtags(text: str, limit: int = 3) -> list[str]:
    keywords = extract_keywords([text], limit=limit + 3)
    hashtags: list[str] = []
    for item in keywords:
        word = str(item["word"]).title()
        compact = HASHTAG_RE.sub("", word)
        if len(compact) < 4:
            continue
        hashtags.append(f"#{compact}")
        if len(hashtags) == limit:
            break
    return hashtags or ["#Breaking", "#SignalFeed"]


def detect_regions(text: str) -> list[str]:
    lower = text.lower()
    regions = [region for region, aliases in INDIA_REGIONS.items() if any(alias in lower for alias in aliases)]
    return regions or ["Global"]


def estimate_social_score(text: str, source: str, topics: list[str]) -> int:
    lower = text.lower()
    score = 38 + min(len(text) // 10, 24)
    if any(topic in {"India", "Governance", "Cricket", "Startups", "Economy"} for topic in topics):
        score += 16
    if any(word in lower for word in ("breaking", "viral", "budget", "ipl", "election", "startup", "delhi", "mumbai")):
        score += 14
    if source in {"The Hindu", "Indian Express", "NDTV", "Moneycontrol"}:
        score += 10
    return min(score, 100)


def recommended_platforms(topics: list[str], regions: list[str]) -> list[str]:
    platforms = ["X", "YouTube"]
    if any(topic in {"Startups", "AI & Tech", "Economy"} for topic in topics):
        platforms.append("LinkedIn")
    if any(topic in {"Culture", "Cricket", "Sports"} for topic in topics):
        platforms.append("Instagram")
    if regions != ["Global"]:
        platforms.append("WhatsApp")
    return platforms[:4]
