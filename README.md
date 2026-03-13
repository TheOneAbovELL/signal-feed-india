<div align="center">

# SignalFeed India

### Real-Time News Intelligence Dashboard for India-First and Global Monitoring

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![WebSockets](https://img.shields.io/badge/WebSockets-Realtime-1F6FEB?style=for-the-badge)](#)
[![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](#license)

SignalFeed India is a full-stack newsroom intelligence product that aggregates Indian and global news feeds, enriches stories with editorial and trust signals, and presents them in a polished live dashboard designed for fast scanning and deeper analysis when needed.

</div>

---

## Overview

SignalFeed India is built like a lightweight media-intelligence desk rather than a generic feed reader.

It combines:

- live RSS ingestion
- editorial topic and region classification
- source trust and social-pulse modelling
- narrative clustering and deduplication
- real-time dashboard updates over WebSockets
- a refined multi-view UI for overview, analytics, stream monitoring, and global coverage

The product is optimized to feel readable and professional for everyday users while still exposing richer intelligence features through the backend and the deeper dashboard views.

---

## What It Does

SignalFeed India continuously ingests stories from Indian and global publishers, normalizes them into a common structure, scores them for editorial and social relevance, and pushes live snapshots to the frontend.

It also adds product-oriented layers such as:

- source credibility and bias metadata
- compact trust radar panels
- social buzz ranking
- global deep-dive tracks
- historical “On this day” context
- story detail modals with related stories and source history

---

## Current Product Highlights

- India-first newsroom dashboard with dedicated global mode
- FastAPI backend with versioned APIs under `/api/v1`
- live updates via WebSockets
- async feed ingestion with a separate worker path
- SQLAlchemy-backed persistence layer
- Redis-aware caching support
- APScheduler-based background jobs
- source trust modelling with credibility, bias, and quality tier metadata
- social-pulse scoring with explainable factors
- heuristic + optional ML-assisted classification hooks
- narrative clustering and story deduplication
- historical context card for the current date
- polished light and dark themes

---

## Dashboard Views

### Overview

The default newsroom home for quick scanning.

It includes:

- lead story
- segment chips
- summary cards
- quick filters
- social buzz board
- live headlines
- compact right-side intelligence rail

### Analytics

A lighter interpretation layer for understanding the shape of the feed rather than only the stories themselves.

It focuses on:

- source movement
- tone and sentiment
- supporting dashboard signals

### Stream

A faster monitoring view for headline-first scanning.

Best for:

- quick headline review
- staying on the live feed
- filtering without the broader dashboard framing

### Global

A dedicated world-news desk separated from the India-first view.

It includes:

- global spotlight
- global summary cards
- global source and topic mix
- global trendboard
- separate global headlines stream
- deep-dive tracks for politics, markets, conflict, tech, and sports

---

## Core Features

### Real-Time Feed Ingestion

- concurrent RSS fetching using `aiohttp`
- feed parsing with `feedparser`
- worker-driven refresh support
- live snapshot broadcasting over WebSockets

### Story Enrichment

Each story can be enriched with:

- topic tags
- region tags
- source category
- sentiment
- hashtags
- source credibility and bias labels
- social pulse score
- social confidence band
- explanation factors for why the story was scored

### Source Trust Modelling

The dashboard includes trust-aware metadata for sources, including:

- credibility score
- bias label
- quality tier
- transparency note

This powers the `Trust radar` and the story detail experience.

### Narrative Intelligence

The backend includes:

- deduplication
- narrative clustering
- cluster payload generation
- history snapshots across multiple windows

### Historical Context

The right-side hero area includes a daily historical context card that pulls “On this day” facts and keeps the product feeling more editorial and alive.

### Story Detail Modal

Each story can open into a detail view with:

- source and trust metadata
- topic and region tags
- explanation of scoring/tagging
- related stories
- source history

---

## UI and Product Design

The frontend is intentionally designed to be:

- simpler for normal users
- richer in analysis without overwhelming the default view
- cleaner in space usage
- readable for longer sessions
- consistent across light and dark themes

Recent UI refinements include:

- a more professional header and hero
- refined typography and spacing
- compact intelligence rail
- improved lead-story hierarchy
- a subdued grey light theme
- a black/charcoal dark theme closer to modern premium productivity tools
- a modal style aligned with the core site theme

---

## Screenshots

### Overview Dashboard

![Overview Dashboard](docs/screenshots/overview-dashboard.png)

### Analytics Dashboard

![Analytics Dashboard](docs/screenshots/analytics-dashboard.png)

### Stream Dashboard

![Stream Dashboard](docs/screenshots/stream-dashboard.png)

### Global Dashboard

![Global Dashboard](docs/screenshots/global-dashboard.png)

### Global Deep Dive

![Global Deep Dive](docs/screenshots/deep-dive-global.png)

### Filters and Segments

![Filters and Segments](docs/screenshots/filters-and-segments.png)

---

## Architecture

SignalFeed India now has a fuller backend structure than the original starter dashboard.

### Backend

- FastAPI application server
- versioned routes and legacy compatibility routes
- WebSocket connection manager
- background scheduler for refresh jobs
- optional worker process for ingestion
- SQLAlchemy persistence layer
- Redis-aware cache abstraction

### Frontend

- server-rendered static shell
- vanilla JavaScript app
- live UI hydration from REST + WebSocket snapshots
- modal details and interactive filter chips

### Data Flow

1. feeds are fetched and normalized
2. stories are enriched with classification and source metadata
3. deduplication and clustering are applied
4. snapshot payloads are assembled
5. the UI fetches and receives live snapshot updates
6. users can drill into stories, filters, and global lanes

---

## Project Structure

```text
signal-feed-india/
├── app/
│   ├── auth.py            # Auth helpers and token flow
│   ├── cache.py           # Cache abstraction with Redis-aware support
│   ├── classifier.py      # Topic, sentiment, hashtag, and signal enrichment
│   ├── config.py          # Environment settings and feed definitions
│   ├── db.py              # Database engine/session setup
│   ├── feeds.py           # Async feed ingestion
│   ├── intelligence.py    # Deduplication and narrative clustering
│   ├── main.py            # FastAPI app, APIs, and websocket endpoint
│   ├── ml.py              # Optional ML-assisted classification helpers
│   ├── models.py          # Story and persistence models
│   ├── on_this_day.py     # Daily historical context provider
│   ├── persistence.py     # Story/source/user persistence functions
│   ├── schemas.py         # Request/response schemas
│   ├── store.py           # Snapshot builder
│   ├── tasks.py           # Scheduler tasks
│   └── worker.py          # Worker entry point
├── static/
│   ├── app.js             # Frontend logic
│   ├── index.html         # Main UI shell
│   └── styles.css         # Product styling and theme system
├── docs/
│   └── screenshots/       # README screenshots
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/TheOneAbovELL/signal-feed-india.git
cd signal-feed-india
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Optional environment file

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 4. Run the API

```bash
python -m uvicorn app.main:app --reload
```

Open: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 5. Run the worker in a second terminal

```bash
python -m app.worker
```

---

## Docker

You can also run the stack with containers:

```bash
docker-compose up --build
```

This is useful for a cleaner production-style setup and for consistent local environments.

---

## API Surface

### Health

```http
GET /api/v1/health
GET /api/health
```

### Snapshot

```http
GET /api/v1/snapshot
GET /api/snapshot
```

Returns dashboard state including:

- story count
- headlines
- topic totals
- source totals
- source categories
- sentiment totals
- region totals
- hashtags
- social leaders
- timeline
- summary cards
- source trust
- history windows
- clustering payload

### Headlines

```http
GET /api/v1/headlines?topic=India
GET /api/v1/headlines?region=Global
GET /api/v1/headlines?q=startup
GET /api/v1/headlines?sentiment=positive
```

### Story Details

```http
GET /api/v1/stories/{story_id}
```

### Analytics

```http
GET /api/v1/analytics/history?window=24h
GET /api/v1/analytics/source-trust
GET /api/v1/analytics/social-model
```

### Daily Historical Context

```http
GET /api/v1/on-this-day
GET /api/on-this-day
```

### Auth and User APIs

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me

GET  /api/v1/user/workspaces
POST /api/v1/user/workspaces
GET  /api/v1/user/saved-filters
POST /api/v1/user/saved-filters
GET  /api/v1/user/watchlists
POST /api/v1/user/watchlists
GET  /api/v1/user/alerts
POST /api/v1/user/alerts
```

### WebSocket

```http
GET /ws
```

---

## Dependencies

Current key dependencies from `requirements.txt`:

- `fastapi`
- `uvicorn`
- `aiohttp`
- `feedparser`
- `websockets`
- `sqlalchemy`
- `pydantic[email]`
- `redis`
- `apscheduler`
- `psycopg[binary]`
- `scikit-learn`

---

## Typical Workflow

### Run locally

```bash
python -m uvicorn app.main:app --reload
```

### Start worker

```bash
python -m app.worker
```

### Open the app

```text
http://127.0.0.1:8000
```

### Explore

- scan the lead story
- switch segments like India, Governance, Economy, or Global
- open a story modal for related coverage and trust metadata
- use Stream for fast headline monitoring
- use Global for dedicated world-news analysis
- check the right rail for trends, keywords, trust, and historical context

---

## Current Limitations

- direct social media APIs are not yet integrated
- frontend auth flows are not yet surfaced in the main UI
- some enrichment remains heuristic unless ML support is enabled
- local environments without internet access may rely on fallback content
- the daily history panel depends on available history providers or built-in fallback facts

---

## Roadmap

Strong next upgrades could include:

- direct X / Reddit / YouTube ingestion
- richer persistent user workspaces in the UI
- fully surfaced saved views and alert management
- better historical analytics visualizations
- multilingual support
- transformer-based ranking and classification
- deployment hardening and CI/CD

---

## License

This project is available under the **MIT License**.

---

## Author

**Omjee R Giri**
