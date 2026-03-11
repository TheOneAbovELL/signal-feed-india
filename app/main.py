from __future__ import annotations

import asyncio
from contextlib import suppress
from pathlib import Path

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .feeds import ingest_once
from .store import store


BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title="Signal Feed India", version="2.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, payload: dict[str, object]) -> None:
        async with self._lock:
            sockets = list(self._connections)
        for socket in sockets:
            try:
                await socket.send_json(payload)
            except RuntimeError:
                await self.disconnect(socket)


manager = ConnectionManager()


async def poller() -> None:
    while True:
        added = await ingest_once(settings.feeds)
        if added:
            await manager.broadcast({"type": "snapshot", "payload": await store.snapshot()})
        await asyncio.sleep(settings.poll_interval_seconds)


@app.on_event("startup")
async def startup_event() -> None:
    await ingest_once(settings.feeds)
    app.state.poller = asyncio.create_task(poller())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    task = app.state.poller
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "signal-feed-india"}


@app.get("/api/snapshot")
async def api_snapshot() -> dict[str, object]:
    return await store.snapshot()


@app.get("/api/headlines")
async def api_headlines(
    topic: str | None = Query(default=None),
    region: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> dict[str, object]:
    snapshot = await store.snapshot()
    headlines = snapshot["headlines"]
    if topic:
        headlines = [item for item in headlines if topic in item["topics"]]
    if region:
        headlines = [item for item in headlines if region in item["regions"]]
    if q:
        needle = q.lower()
        headlines = [item for item in headlines if needle in item["title"].lower() or needle in item["summary"].lower()]
    return {"items": headlines, "count": len(headlines)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "snapshot", "payload": await store.snapshot()})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
