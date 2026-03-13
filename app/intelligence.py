from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from .classifier import extract_keywords
from .config import settings
from .models import Story


@dataclass(slots=True)
class Cluster:
    id: str
    label: str
    stories: list[Story]
    summary: str
    momentum_score: int


def _normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


def _title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _normalize_title(left), _normalize_title(right)).ratio()


def deduplicate_stories(stories: list[Story], similarity_threshold: float = 0.84) -> list[Story]:
    unique: list[Story] = []
    seen_links: set[str] = set()
    for story in sorted(stories, key=lambda item: (item.published_at, item.social_score), reverse=True):
        if story.link in seen_links:
            continue
        if any(_title_similarity(story.title, existing.title) >= similarity_threshold for existing in unique):
            continue
        unique.append(story)
        seen_links.add(story.link)
    return unique


def cluster_stories(stories: list[Story]) -> list[Cluster]:
    if not settings.enable_story_clustering:
        return []

    groups: dict[str, list[Story]] = defaultdict(list)
    for story in stories:
        topic = story.topics[0] if story.topics else "General"
        region = story.regions[0] if story.regions else "Global"
        groups[f"{topic}::{region}"].append(story)

    clusters: list[Cluster] = []
    for index, items in enumerate(groups.values(), start=1):
        items = sorted(items, key=lambda item: (item.social_score, item.published_at), reverse=True)
        lead = items[0]
        keywords = extract_keywords([f"{story.title} {story.summary}" for story in items], limit=4)
        summary = summarize_cluster(items, [str(item["word"]) for item in keywords])
        avg_score = int(sum(story.social_score for story in items) / max(len(items), 1))
        clusters.append(
            Cluster(
                id=f"cluster-{index}",
                label=f"{lead.topics[0] if lead.topics else 'General'} / {lead.regions[0] if lead.regions else 'Global'}",
                stories=items,
                summary=summary,
                momentum_score=min(100, avg_score + min(len(items) * 3, 15)),
            )
        )

    return sorted(clusters, key=lambda cluster: cluster.momentum_score, reverse=True)


def summarize_cluster(stories: list[Story], keywords: list[str] | None = None) -> str:
    if not stories:
        return "No narrative summary available."

    lead = stories[0]
    topic = lead.topics[0] if lead.topics else "General"
    region = lead.regions[0] if lead.regions else "Global"
    phrase = ", ".join(keywords[:2]) if keywords else (lead.hashtags[0] if lead.hashtags else "live coverage")
    source_count = len({story.source for story in stories})
    return f"{len(stories)} related stories across {source_count} sources are converging around {topic.lower()} in {region}. Key signals include {phrase}."


def cluster_payload(clusters: list[Cluster]) -> list[dict[str, Any]]:
    return [
        {
            "id": cluster.id,
            "label": cluster.label,
            "summary": cluster.summary,
            "momentum_score": cluster.momentum_score,
            "story_count": len(cluster.stories),
            "lead_story": cluster.stories[0].to_dict() if cluster.stories else None,
        }
        for cluster in clusters
    ]
