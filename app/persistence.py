from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
from typing import Any

from sqlalchemy import Select, delete, func, select
from sqlalchemy.orm import joinedload

from .config import FeedSource, settings
from .db import (
    AlertPreferenceRecord,
    AuthTokenRecord,
    SavedFilterRecord,
    SourceRecord,
    StoryRecord,
    UserRecord,
    WatchlistRecord,
    WorkspaceRecord,
    session_scope,
)
from .models import Story


def _dump(value: Any) -> str:
    return json.dumps(value)


def _load(value: str) -> Any:
    return json.loads(value)


def story_from_record(record: StoryRecord) -> Story:
    source = record.source
    return Story(
        id=record.story_id,
        source=source.name,
        source_color=source.color,
        source_category=source.category,
        source_bias_label=source.bias_label,
        source_quality_tier=source.quality_tier,
        source_credibility_score=source.credibility_score,
        title=record.title,
        link=record.link,
        summary=record.summary,
        published_at=record.published_at.replace(tzinfo=timezone.utc) if record.published_at.tzinfo is None else record.published_at.astimezone(timezone.utc),
        topics=_load(record.topic_json),
        sentiment=record.sentiment,
        regions=_load(record.region_json),
        hashtags=_load(record.hashtag_json),
        social_score=record.social_score,
        social_confidence_band=record.social_confidence_band,
        social_explanation=_load(record.social_explanation_json),
        social_platforms=_load(record.platform_json),
    )


def seed_sources(feeds: list[FeedSource]) -> None:
    with session_scope() as session:
        for feed in feeds:
            source = session.scalar(select(SourceRecord).where(SourceRecord.name == feed.name))
            if source is None:
                source = SourceRecord(
                    name=feed.name,
                    url=feed.url,
                    color=feed.color,
                    category=feed.category,
                    credibility_score=feed.credibility_score,
                    bias_label=feed.bias_label,
                    quality_tier=feed.quality_tier,
                    transparency_note=feed.transparency_note,
                    active=True,
                )
                session.add(source)
            else:
                source.url = feed.url
                source.color = feed.color
                source.category = feed.category
                source.credibility_score = feed.credibility_score
                source.bias_label = feed.bias_label
                source.quality_tier = feed.quality_tier
                source.transparency_note = feed.transparency_note
                source.active = True


def persist_stories(stories: list[Story]) -> list[Story]:
    added: list[Story] = []
    with session_scope() as session:
        for story in sorted(stories, key=lambda item: item.published_at, reverse=True):
            exists = session.scalar(select(StoryRecord.id).where(StoryRecord.story_id == story.id))
            if exists:
                continue
            source = session.scalar(select(SourceRecord).where(SourceRecord.name == story.source))
            if source is None:
                continue
            session.add(
                StoryRecord(
                    story_id=story.id,
                    source_id=source.id,
                    title=story.title,
                    link=story.link,
                    summary=story.summary,
                    published_at=story.published_at.replace(tzinfo=None),
                    topic_json=_dump(story.topics),
                    region_json=_dump(story.regions),
                    hashtag_json=_dump(story.hashtags),
                    platform_json=_dump(story.social_platforms),
                    sentiment=story.sentiment,
                    social_score=story.social_score,
                    social_confidence_band=story.social_confidence_band,
                    social_explanation_json=_dump(story.social_explanation),
                )
            )
            added.append(story)

        # keep the dataset bounded for local/dev use
        all_ids = list(session.scalars(select(StoryRecord.id).order_by(StoryRecord.published_at.desc())))
        if len(all_ids) > settings.max_headlines * 8:
            stale_ids = all_ids[settings.max_headlines * 8 :]
            session.execute(delete(StoryRecord).where(StoryRecord.id.in_(stale_ids)))
    return added


def get_recent_stories(limit: int | None = None) -> list[Story]:
    query: Select[tuple[StoryRecord]] = select(StoryRecord).options(joinedload(StoryRecord.source)).order_by(StoryRecord.published_at.desc())
    if limit is not None:
        query = query.limit(limit)
    with session_scope() as session:
        records = list(session.scalars(query))
    return [story_from_record(record) for record in records]


def get_history(window: str) -> list[dict[str, object]]:
    now = datetime.now(timezone.utc)
    if window == "1h":
        start = now - timedelta(hours=1)
        bucket_minutes = 5
    elif window == "24h":
        start = now - timedelta(hours=24)
        bucket_minutes = 60
    else:
        start = now - timedelta(days=7)
        bucket_minutes = 24 * 60

    stories = [story for story in get_recent_stories(limit=settings.max_headlines * 8) if story.published_at >= start]
    buckets: dict[datetime, Counter[str]] = defaultdict(Counter)
    for story in stories:
        bucket = story.published_at.replace(second=0, microsecond=0)
        if bucket_minutes >= 60:
            bucket = bucket.replace(minute=(bucket.minute // bucket_minutes) * bucket_minutes if bucket_minutes < 1440 else 0)
        else:
            bucket = bucket.replace(minute=(bucket.minute // bucket_minutes) * bucket_minutes)
        if bucket_minutes == 1440:
            bucket = bucket.replace(hour=0, minute=0)
        buckets[bucket]["total"] += 1
        for topic in story.topics:
            buckets[bucket][topic] += 1

    return [
        {"bucket": bucket.isoformat(), **dict(counter)}
        for bucket, counter in sorted(buckets.items())
    ]


def get_source_trust_report() -> list[dict[str, object]]:
    stories = get_recent_stories(limit=settings.max_headlines * 4)
    volume = Counter(story.source for story in stories)
    report: list[dict[str, object]] = []
    with session_scope() as session:
        sources = list(session.scalars(select(SourceRecord).order_by(SourceRecord.credibility_score.desc(), SourceRecord.name.asc())))
    for source in sources:
        report.append(
            {
                "name": source.name,
                "category": source.category,
                "credibility_score": source.credibility_score,
                "bias_label": source.bias_label,
                "quality_tier": source.quality_tier,
                "transparency_note": source.transparency_note,
                "recent_story_count": volume.get(source.name, 0),
            }
        )
    return report


def social_model_definition() -> dict[str, object]:
    return {
        "name": "social-pulse-v2",
        "description": "Weighted heuristic scoring model for estimating likely downstream story pickup.",
        "factors": [
            {"factor": "base_activity", "weight": 28, "description": "Baseline live news visibility"},
            {"factor": "urgency_keywords", "weight_cap": 20, "description": "High-attention phrasing such as breaking, war, election, or viral"},
            {"factor": "topic_relevance", "weight": "up to 22", "description": "Editorial categories historically associated with stronger sharing"},
            {"factor": "regional_relevance", "weight": "3-6", "description": "Regional specificity increases audience forwarding behaviour"},
            {"factor": "source_trust", "weight": "up to 22", "description": "High-trust sources improve confidence in continued pickup"},
        ],
        "confidence_bands": {
            "High": "78-100",
            "Medium": "58-77",
            "Low": "0-57",
        },
    }


def create_user(email: str, full_name: str, password_hash: str) -> dict[str, object]:
    with session_scope() as session:
        existing = session.scalar(select(UserRecord).where(UserRecord.email == email))
        if existing:
            raise ValueError("User already exists")
        user = UserRecord(email=email, full_name=full_name, password_hash=password_hash)
        session.add(user)
        session.flush()
        workspace = WorkspaceRecord(owner_id=user.id, name="My Workspace", is_private=True)
        session.add(workspace)
        session.flush()
        return {"id": user.id, "email": user.email, "full_name": user.full_name, "workspace_id": workspace.id}


def get_user_by_email(email: str) -> UserRecord | None:
    with session_scope() as session:
        user = session.scalar(select(UserRecord).where(UserRecord.email == email))
        if user is None:
            return None
        session.expunge(user)
        return user


def get_user_by_id(user_id: int) -> UserRecord | None:
    with session_scope() as session:
        user = session.scalar(select(UserRecord).where(UserRecord.id == user_id))
        if user is None:
            return None
        session.expunge(user)
        return user


def create_token_record(user_id: int, token_hash: str, expires_at: datetime) -> None:
    with session_scope() as session:
        session.add(AuthTokenRecord(user_id=user_id, token_hash=token_hash, expires_at=expires_at.replace(tzinfo=None)))


def get_user_for_token(token_hash: str) -> UserRecord | None:
    with session_scope() as session:
        record = session.scalar(
            select(AuthTokenRecord).where(
                AuthTokenRecord.token_hash == token_hash,
                AuthTokenRecord.expires_at >= datetime.utcnow(),
            )
        )
        if record is None:
            return None
        user = session.scalar(select(UserRecord).where(UserRecord.id == record.user_id))
        if user is None:
            return None
        session.expunge(user)
        return user


def list_workspaces(user_id: int) -> list[dict[str, object]]:
    with session_scope() as session:
        items = list(session.scalars(select(WorkspaceRecord).where(WorkspaceRecord.owner_id == user_id).order_by(WorkspaceRecord.created_at.desc())))
    return [{"id": item.id, "name": item.name, "is_private": item.is_private} for item in items]


def create_workspace(user_id: int, name: str, is_private: bool) -> dict[str, object]:
    with session_scope() as session:
        item = WorkspaceRecord(owner_id=user_id, name=name, is_private=is_private)
        session.add(item)
        session.flush()
        return {"id": item.id, "name": item.name, "is_private": item.is_private}


def list_saved_filters(user_id: int) -> list[dict[str, object]]:
    with session_scope() as session:
        items = list(session.scalars(select(SavedFilterRecord).where(SavedFilterRecord.user_id == user_id).order_by(SavedFilterRecord.created_at.desc())))
    return [
        {
            "id": item.id,
            "name": item.name,
            "workspace_id": item.workspace_id,
            "topic": item.topic,
            "region": item.region,
            "query": item.query,
            "segment": item.segment,
            "view_mode": item.view_mode,
        }
        for item in items
    ]


def create_saved_filter(user_id: int, payload: dict[str, object]) -> dict[str, object]:
    with session_scope() as session:
        item = SavedFilterRecord(user_id=user_id, **payload)
        session.add(item)
        session.flush()
        return {
            "id": item.id,
            "name": item.name,
            "workspace_id": item.workspace_id,
            "topic": item.topic,
            "region": item.region,
            "query": item.query,
            "segment": item.segment,
            "view_mode": item.view_mode,
        }


def list_watchlists(user_id: int) -> list[dict[str, object]]:
    with session_scope() as session:
        items = list(session.scalars(select(WatchlistRecord).where(WatchlistRecord.user_id == user_id).order_by(WatchlistRecord.created_at.desc())))
    return [
        {
            "id": item.id,
            "workspace_id": item.workspace_id,
            "label": item.label,
            "query": item.query,
            "topic": item.topic,
            "region": item.region,
            "source_name": item.source_name,
        }
        for item in items
    ]


def create_watchlist(user_id: int, payload: dict[str, object]) -> dict[str, object]:
    with session_scope() as session:
        item = WatchlistRecord(user_id=user_id, **payload)
        session.add(item)
        session.flush()
        return {
            "id": item.id,
            "workspace_id": item.workspace_id,
            "label": item.label,
            "query": item.query,
            "topic": item.topic,
            "region": item.region,
            "source_name": item.source_name,
        }


def list_alert_preferences(user_id: int) -> list[dict[str, object]]:
    with session_scope() as session:
        items = list(session.scalars(select(AlertPreferenceRecord).where(AlertPreferenceRecord.user_id == user_id).order_by(AlertPreferenceRecord.created_at.desc())))
    return [
        {
            "id": item.id,
            "workspace_id": item.workspace_id,
            "topic": item.topic,
            "region": item.region,
            "min_social_score": item.min_social_score,
            "delivery_channel": item.delivery_channel,
            "enabled": item.enabled,
        }
        for item in items
    ]


def create_alert_preference(user_id: int, payload: dict[str, object]) -> dict[str, object]:
    with session_scope() as session:
        item = AlertPreferenceRecord(user_id=user_id, **payload)
        session.add(item)
        session.flush()
        return {
            "id": item.id,
            "workspace_id": item.workspace_id,
            "topic": item.topic,
            "region": item.region,
            "min_social_score": item.min_social_score,
            "delivery_channel": item.delivery_channel,
            "enabled": item.enabled,
        }

def latest_story_timestamp() -> datetime | None:
    with session_scope() as session:
        return session.scalar(select(func.max(StoryRecord.published_at)))
