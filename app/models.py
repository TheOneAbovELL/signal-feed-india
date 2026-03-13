from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Story:
    id: str
    source: str
    source_color: str
    source_category: str
    source_bias_label: str
    source_quality_tier: str
    source_credibility_score: float
    title: str
    link: str
    summary: str
    published_at: datetime
    topics: list[str]
    sentiment: str
    regions: list[str]
    hashtags: list[str]
    social_score: int
    social_confidence_band: str
    social_explanation: list[dict[str, Any]]
    social_platforms: list[str]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["published_at"] = self.published_at.isoformat()
        return payload
