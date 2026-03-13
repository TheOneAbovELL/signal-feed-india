from __future__ import annotations

import calendar
import random
from datetime import datetime

import aiohttp

_LAST_SUCCESSFUL_PAYLOAD: dict[str, object] | None = None

REQUEST_HEADERS = {
    "User-Agent": "SignalFeed India/4.0 (daily history panel)",
}

WIKIPEDIA_ALL_ENDPOINT = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{month:02d}/{day:02d}"
DAY_IN_HISTORY_ENDPOINT = "https://api.dayinhistory.net/v1/date/{month:02d}/{day:02d}"

STATIC_HISTORY_FACTS = [
    {
        "year": 1879,
        "title": "Albert Einstein was born",
        "text": "Albert Einstein, whose work reshaped modern physics through the theory of relativity, was born on March 14, 1879.",
        "url": "https://en.wikipedia.org/wiki/Albert_Einstein",
    },
    {
        "year": 1883,
        "title": "Karl Marx died in London",
        "text": "Karl Marx died on March 14, 1883, leaving behind ideas that deeply influenced political thought, labor movements, and modern social theory.",
        "url": "https://en.wikipedia.org/wiki/Karl_Marx",
    },
    {
        "year": 1964,
        "title": "A jury found Jack Ruby guilty",
        "text": "On March 14, 1964, Jack Ruby was convicted for killing Lee Harvey Oswald, linking the case permanently to the story of John F. Kennedy's assassination.",
        "url": "https://en.wikipedia.org/wiki/Jack_Ruby",
    },
    {
        "year": 1995,
        "title": "Norman Thagard reached space aboard Mir 18",
        "text": "Norman Thagard launched toward the Russian space station Mir on March 14, 1995, becoming the first American to travel into space on a Russian launch vehicle.",
        "url": "https://en.wikipedia.org/wiki/Norman_Thagard",
    },
    {
        "year": 2018,
        "title": "Stephen Hawking died",
        "text": "Theoretical physicist Stephen Hawking died on March 14, 2018, remembered for making black hole physics and cosmology accessible to millions.",
        "url": "https://en.wikipedia.org/wiki/Stephen_Hawking",
    },
]


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _pick_page(entry: dict[str, object]) -> dict[str, object]:
    pages = entry.get("pages") or []
    if isinstance(pages, list):
        for page in pages:
            if isinstance(page, dict):
                return page
    return {}


def _extract_title(page: dict[str, object], fallback: str) -> str:
    titles = page.get("titles")
    if isinstance(titles, dict):
        for key in ("display", "normalized", "canonical"):
            value = titles.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return fallback


def _extract_url(page: dict[str, object], fallback: str) -> str:
    content_urls = page.get("content_urls")
    if isinstance(content_urls, dict):
        desktop = content_urls.get("desktop")
        if isinstance(desktop, dict):
            page_url = desktop.get("page")
            if isinstance(page_url, str) and page_url.strip():
                return page_url
    return fallback


def _format_payload(month: int, day: int, source_name: str, source_url: str, cards: list[dict[str, object]]) -> dict[str, object]:
    payload = {
        "available": True,
        "mode": "history",
        "date_label": f"{calendar.month_name[month]} {day}",
        "lead": cards[0],
        "items": cards[1:4],
        "source_name": source_name,
        "source_url": source_url,
    }
    return payload


async def _fetch_wikipedia(session: aiohttp.ClientSession, month: int, day: int) -> dict[str, object] | None:
    url = WIKIPEDIA_ALL_ENDPOINT.format(month=month, day=day)
    try:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            payload = await response.json()
    except (aiohttp.ClientError, TimeoutError):
        return None

    events = payload.get("selected") or payload.get("events") or []
    if not isinstance(events, list) or not events:
        return None

    pool = [entry for entry in events if isinstance(entry, dict) and isinstance(entry.get("text"), str) and entry.get("text")]
    random.shuffle(pool)
    cards = []
    for entry in pool:
        page = _pick_page(entry)
        text = _clean_text(entry["text"])
        cards.append(
            {
                "year": int(entry.get("year", 0) or 0),
                "title": _extract_title(page, text),
                "text": text,
                "url": _extract_url(page, url),
            }
        )
        if len(cards) >= 4:
            break
    if not cards:
        return None
    return _format_payload(month, day, "Wikipedia", url, cards)


async def _fetch_day_in_history(session: aiohttp.ClientSession, month: int, day: int) -> dict[str, object] | None:
    url = DAY_IN_HISTORY_ENDPOINT.format(month=month, day=day)
    try:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            payload = await response.json()
    except (aiohttp.ClientError, TimeoutError):
        return None

    events = payload.get("data") or payload.get("events") or []
    if not isinstance(events, list) or not events:
        return None

    pool = [entry for entry in events if isinstance(entry, dict)]
    random.shuffle(pool)
    cards = []
    for entry in pool:
        description = entry.get("description") or entry.get("text") or entry.get("event")
        title = entry.get("title") or entry.get("headline") or description
        if not isinstance(description, str) or not description.strip():
            continue
        if not isinstance(title, str) or not title.strip():
            title = description
        cards.append(
            {
                "year": int(entry.get("year", 0) or 0),
                "title": _clean_text(title),
                "text": _clean_text(description),
                "url": entry.get("url") if isinstance(entry.get("url"), str) else url,
            }
        )
        if len(cards) >= 4:
            break
    if not cards:
        return None
    return _format_payload(month, day, "Day in History", url, cards)


def _static_history_fallback(month: int, day: int) -> dict[str, object]:
    seeded = STATIC_HISTORY_FACTS[:]
    random.Random(month * 100 + day).shuffle(seeded)
    return _format_payload(month, day, "Built-in history fallback", "https://en.wikipedia.org/wiki/Main_Page", seeded[:4])


async def fetch_on_this_day() -> dict[str, object]:
    global _LAST_SUCCESSFUL_PAYLOAD

    now = datetime.now().astimezone()
    month = now.month
    day = now.day

    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout, headers=REQUEST_HEADERS) as session:
        providers = []
        wikipedia = await _fetch_wikipedia(session, month, day)
        day_in_history = await _fetch_day_in_history(session, month, day)
        if wikipedia:
            providers.append(wikipedia)
        if day_in_history:
            providers.append(day_in_history)

    if providers:
        payload = random.choice(providers)
        _LAST_SUCCESSFUL_PAYLOAD = payload
        return payload

    if _LAST_SUCCESSFUL_PAYLOAD is not None:
        return {
            **_LAST_SUCCESSFUL_PAYLOAD,
            "date_label": f"{calendar.month_name[month]} {day}",
            "source_name": f"{_LAST_SUCCESSFUL_PAYLOAD.get('source_name', 'History source')} (cached)",
        }

    return _static_history_fallback(month, day)
