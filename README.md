# Signal Feed India

An India-first, full-stack live intelligence dashboard built with FastAPI and a realtime browser UI.

## What it does

- polls Indian and global RSS feeds asynchronously
- classifies stories into India-relevant topics like Governance, Startups, Cricket, Economy, and Infra
- derives region tags, hashtag suggestions, and a social pulse score for each story
- pushes live snapshots over WebSockets
- provides a product-style dashboard with search, topic filters, region filters, social buzz rankings, and live headlines

## Run

```powershell
python -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Test endpoints

- `GET /api/health`
- `GET /api/snapshot`
- `GET /api/headlines?topic=India`
- `GET /api/headlines?region=Delhi%20NCR`
- `GET /api/headlines?q=startup`

## Product notes

- Social media integration is currently modeled as a derived social-distribution layer, not direct posting or API ingestion.
- If you want true X/Reddit/YouTube ingestion next, the next step is adding provider-specific credentials, rate-limit handling, and normalized adapters.
- If live RSS is unavailable, the backend falls back to India-themed sample stories so the UI still renders.
