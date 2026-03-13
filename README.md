<div align="center">

# Signal Feed India

### Real-Time News Intelligence Dashboard for India and Global News Monitoring

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![WebSockets](https://img.shields.io/badge/WebSockets-Realtime-1F6FEB?style=for-the-badge)](#)
[![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](#license)

Signal Feed India is a full-stack live news intelligence platform that aggregates Indian and global RSS feeds, enriches stories with editorial and social signals, and presents them through a polished multi-view dashboard.

</div>

---

## Overview

Signal Feed India is built as a newsroom-style command center rather than a simple feed reader.

It continuously ingests stories from Indian and global sources, classifies them into useful editorial segments, assigns derived momentum signals, and streams live updates to the browser in real time.

The platform is designed for fast scanning, trend discovery, segment switching, and global deep-dive monitoring.

---

## Highlights

- India-first live dashboard with dedicated global analysis mode
- real-time updates using WebSockets
- asynchronous RSS ingestion pipeline
- editorial topic classification and region-aware tagging
- social pulse scoring and hashtag radar
- multiple dashboard modes: `Overview`, `Analytics`, `Stream`, `Global`
- interactive segment switching for India, Governance, Economy, Startups, Cricket, and Global
- deep-dive cards for Politics, Markets, Conflict, Tech, and Sports
- graceful fallback sample stories for demo or offline rendering

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

## Core Features

### 1. Real-Time Feed Ingestion

- Fetches multiple Indian and global RSS feeds concurrently using `aiohttp`
- Parses structured feed data using `feedparser`
- refreshes snapshots at regular intervals
- pushes live updates to the frontend over WebSockets

### 2. Story Enrichment Pipeline

Each story is enhanced with:

- topic tags
- region tags
- source category labels
- sentiment classification
- derived hashtag suggestions
- social pulse score
- recommended social distribution platforms

### 3. India-First Editorial Segments

The dashboard is optimized for India-relevant monitoring with segments such as:

- India
- Governance
- Economy
- Startups
- Cricket
- AI & Tech
- Geopolitics
- Climate
- Infra & Mobility
- Culture
- Science

### 4. Global Analysis Desk

The dedicated Global mode includes:

- a world-news spotlight card
- global summary cards
- global topic mix
- global source mix
- global keyword trendboard
- separate global headline stream
- deep-dive cards for:
  - Politics
  - Markets
  - Conflict
  - Tech
  - Sports

### 5. Product-Style UI

Users can:

- switch between dashboard modes
- search live headlines
- filter by topic and region
- use segment chips for faster navigation
- inspect social buzz rankings
- explore global news separately from India-focused reporting

---

## How It Works

Signal Feed India follows a lightweight real-time intelligence pipeline:

1. RSS feeds are fetched asynchronously from Indian and global publishers.
2. Story fields are normalized into a shared structure.
3. NLP-style heuristic enrichment assigns:
   - topics
   - region relevance
   - sentiment
   - hashtags
   - social pulse score
4. Stories are stored in an in-memory dashboard store.
5. Snapshot payloads are exposed through REST APIs.
6. The browser receives live updates through WebSockets.
7. The UI renders stories across overview, analytics, stream, and global views.

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.13+ | Core backend language |
| FastAPI | Web framework |
| Uvicorn | ASGI server |
| aiohttp | Async RSS fetching |
| feedparser | RSS parsing |
| WebSockets | Realtime updates |
| Vanilla JavaScript | Frontend logic |
| HTML/CSS | Dashboard UI |

---

## Project Structure

```text
signal-feed-india/
+-- app/
¦   +-- __init__.py
¦   +-- classifier.py        # Topic, sentiment, hashtag, and region logic
¦   +-- config.py            # Feed configuration and dashboard settings
¦   +-- feeds.py             # Async RSS ingestion and story creation
¦   +-- main.py              # FastAPI app, routes, and websocket server
¦   +-- models.py            # Story data model
¦   +-- store.py             # In-memory dashboard store and snapshot builder
+-- static/
¦   +-- app.js               # Frontend dashboard logic
¦   +-- index.html           # Main app UI
¦   +-- styles.css           # Product styling
+-- docs/
¦   +-- screenshots/         # README image assets
+-- requirements.txt
+-- README.md
+-- .gitignore
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/TheOneAbovELL/signal-feed-india.git
cd signal-feed-india
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python -m uvicorn app.main:app --reload
```

Open: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## API Endpoints

### Health Check
```http
GET /api/health
```

### Full Dashboard Snapshot
```http
GET /api/snapshot
```

Returns live dashboard payloads including:

- story count
- headlines
- topic totals
- source totals
- source categories
- region totals
- sentiment totals
- hashtags
- social leaders
- timeline
- summary cards

### Filtered Headlines
```http
GET /api/headlines?topic=India
GET /api/headlines?region=Delhi%20NCR
GET /api/headlines?q=startup
```

### WebSocket Feed
```http
GET /ws
```

---

## Dashboard Modes

### Overview
A balanced editorial command center with:
- spotlight story
- segment chips
- summary cards
- narrative timeline
- social buzz board
- live headlines

### Analytics
A signal-heavy mode for:
- topic velocity
- region heatmap
- source activity
- sentiment mix
- keyword trends
- hashtag radar

### Stream
A faster monitoring mode focused on:
- filters
- search
- rapid headline scanning
- segment-driven navigation

### Global
A dedicated world-news workspace featuring:
- global spotlight story
- global summary cards
- global topic and source mix
- trendboard
- deep-dive global tracks
- separate global story stream

---

## Example Use Cases

Signal Feed India is useful for:

- editorial monitoring
- journalism projects
- news product prototypes
- media intelligence dashboards
- research demos
- trend analysis across Indian and global news streams

---

## Fallback Behavior

If live RSS feeds fail or are temporarily unreachable, the dashboard loads themed sample stories so the UI remains testable and visually complete.

This makes the project useful for:

- demos
- local development
- screenshot generation
- UI testing
- offline presentation

---

## Current Limitations

- social media integration is currently modeled, not directly API-powered
- stories are stored in-memory rather than in a database
- classification uses heuristic rules rather than transformer models
- there are no user accounts, saved dashboards, or persistent watchlists yet

---

## Future Improvements

Potential next upgrades include:

- direct X / Reddit / YouTube integrations
- persistent storage and historical trend analysis
- saved watchlists and custom editorial lanes
- clickable deep-dive cards that filter stories in place
- richer article detail drawers or modal views
- alerting for high-momentum stories
- multilingual support
- transformer-based story enrichment

---

## License

This project is available under the **MIT License**.

---

## Author

**Omjee R Giri**
