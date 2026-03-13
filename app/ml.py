from __future__ import annotations

import logging
from functools import lru_cache

from .config import settings


logger = logging.getLogger("signal-feed-ml")


TRAINING_SAMPLES = {
    "India": [
        "India parliament session in Delhi focuses on policy reforms",
        "Mumbai and Bengaluru lead new India growth story",
        "National infrastructure push expands across Indian cities",
    ],
    "Governance": [
        "Cabinet clears new government policy package",
        "Parliament debate intensifies over minister response",
        "State assembly passes governance reform bill",
    ],
    "Politics": [
        "Election campaign enters decisive final phase",
        "Prime minister and opposition trade attacks over policy",
        "Presidential race reshapes coalition politics",
    ],
    "Startups": [
        "Startup founder raises new venture funding round",
        "Fintech unicorn expands product suite after seed round",
        "SaaS startup hiring accelerates amid investor interest",
    ],
    "Economy": [
        "Markets react to inflation and central bank outlook",
        "Sensex and Nifty rise as trade data improves",
        "Rupee volatility drives business and banking caution",
    ],
    "Climate": [
        "Monsoon shifts raise climate and flood risks",
        "Solar and wind investments grow amid emissions targets",
        "Heatwave and drought concerns deepen climate debate",
    ],
    "Infra & Mobility": [
        "Metro corridor expansion boosts urban mobility",
        "Highway and railway upgrades improve logistics links",
        "Electric vehicle infrastructure rollout gathers pace",
    ],
    "AI & Tech": [
        "AI platform launches new data and cloud tooling",
        "Chip makers race to supply software and machine learning demand",
        "Cybersecurity and cloud infrastructure dominate tech agenda",
    ],
    "Geopolitics": [
        "Border tensions drive diplomatic summit talks",
        "Sanctions and military buildup reshape geopolitics",
        "Foreign policy focus sharpens during regional conflict",
    ],
    "Science": [
        "Research study reveals new space science breakthrough",
        "ISRO mission boosts astronomy and discovery agenda",
        "Vaccine and gene research advances in new trial",
    ],
    "Cricket": [
        "IPL match swings after late wicket burst",
        "BCCI confirms new cricket schedule for T20 series",
        "Test match innings puts captain under pressure",
    ],
    "Sports": [
        "League table changes after tournament upset",
        "Olympic qualification hopes rise with new medal push",
        "Football club secures dramatic cup victory",
    ],
    "Culture": [
        "Film festival spotlights new music and art releases",
        "Bollywood award season drives fashion conversation",
        "Book launch and movie premiere fuel culture desk coverage",
    ],
}


@lru_cache(maxsize=1)
def _load_pipeline():
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.multiclass import OneVsRestClassifier
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import MultiLabelBinarizer
    except Exception as exc:
        logger.warning("ML classification unavailable; using heuristic fallback: %s", exc)
        return None

    texts: list[str] = []
    labels: list[list[str]] = []
    for topic, samples in TRAINING_SAMPLES.items():
        for sample in samples:
            texts.append(sample)
            labels.append([topic])

    if len(texts) < 10:
        return None

    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(labels)
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", OneVsRestClassifier(LogisticRegression(max_iter=400))),
        ]
    )
    pipeline.fit(texts, y)
    return pipeline, mlb


def predict_topics(text: str) -> list[str] | None:
    if not settings.enable_ml_classification:
        return None
    bundle = _load_pipeline()
    if bundle is None:
        return None

    pipeline, mlb = bundle
    probabilities = pipeline.predict_proba([text])[0]
    ranked = sorted(
        zip(mlb.classes_, probabilities),
        key=lambda item: float(item[1]),
        reverse=True,
    )
    selected = [label for label, score in ranked if float(score) >= 0.24][:3]
    return selected or [ranked[0][0]] if ranked else None
