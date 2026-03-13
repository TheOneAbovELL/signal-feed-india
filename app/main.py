from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import get_current_user, hash_password, issue_access_token, verify_password
from .config import settings
from .db import init_db
from .persistence import (
    create_alert_preference,
    create_saved_filter,
    create_user,
    create_watchlist,
    create_workspace,
    get_source_trust_report,
    get_user_by_email,
    latest_story_timestamp,
    list_alert_preferences,
    list_saved_filters,
    list_watchlists,
    list_workspaces,
    seed_sources,
    social_model_definition,
)
from .schemas import (
    AlertPreferenceRequest,
    LoginRequest,
    RegisterRequest,
    SavedFilterRequest,
    WatchlistRequest,
    WorkspaceRequest,
)
from .store import store


BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title=settings.app_name, version=settings.app_version)
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


async def snapshot_watcher() -> None:
    last_seen: datetime | None = None
    while True:
        latest = latest_story_timestamp()
        latest = latest.replace(tzinfo=timezone.utc) if latest and latest.tzinfo is None else latest
        if latest is not None and latest != last_seen:
            last_seen = latest
            await manager.broadcast({"type": "snapshot", "payload": await store.snapshot()})
        await asyncio.sleep(10)


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    seed_sources(settings.feeds)
    app.state.snapshot_watcher = asyncio.create_task(snapshot_watcher())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    task = app.state.snapshot_watcher
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name.lower().replace(" ", "-"), "mode": "api-only"}


@app.get("/api/snapshot")
async def api_snapshot() -> dict[str, object]:
    return await store.snapshot()


@app.get("/api/headlines")
async def api_headlines(
    topic: str | None = Query(default=None),
    region: str | None = Query(default=None),
    q: str | None = Query(default=None),
    sentiment: str | None = Query(default=None),
) -> dict[str, object]:
    snapshot = await store.snapshot()
    headlines = snapshot["headlines"]
    if topic:
        headlines = [item for item in headlines if topic in item["topics"]]
    if region:
        headlines = [item for item in headlines if region in item["regions"]]
    if sentiment:
        headlines = [item for item in headlines if item["sentiment"] == sentiment]
    if q:
        needle = q.lower()
        headlines = [item for item in headlines if needle in item["title"].lower() or needle in item["summary"].lower()]
    return {"items": headlines, "count": len(headlines)}


@app.get("/api/analytics/history")
async def analytics_history(window: str = Query(default="24h", pattern="^(1h|24h|7d)$")) -> dict[str, object]:
    snapshot = await store.snapshot()
    return {"window": window, "points": snapshot["history"][window]}


@app.get("/api/analytics/source-trust")
async def analytics_source_trust() -> dict[str, object]:
    return {"items": get_source_trust_report()}


@app.get("/api/analytics/social-model")
async def analytics_social_model() -> dict[str, object]:
    return social_model_definition()


@app.post("/api/auth/register")
async def auth_register(payload: RegisterRequest) -> dict[str, object]:
    try:
        user = create_user(payload.email, payload.full_name, hash_password(payload.password))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    token = issue_access_token(int(user["id"]))
    return {"user": user, **token}


@app.post("/api/auth/login")
async def auth_login(payload: LoginRequest) -> dict[str, object]:
    user = get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = issue_access_token(user.id)
    return {
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
        **token,
    }


@app.get("/api/auth/me")
async def auth_me(user=Depends(get_current_user)) -> dict[str, object]:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "workspaces": list_workspaces(user.id),
    }


@app.get("/api/user/workspaces")
async def user_workspaces(user=Depends(get_current_user)) -> dict[str, object]:
    return {"items": list_workspaces(user.id)}


@app.post("/api/user/workspaces")
async def user_workspace_create(payload: WorkspaceRequest, user=Depends(get_current_user)) -> dict[str, object]:
    return create_workspace(user.id, payload.name, payload.is_private)


@app.get("/api/user/saved-filters")
async def user_saved_filters(user=Depends(get_current_user)) -> dict[str, object]:
    return {"items": list_saved_filters(user.id)}


@app.post("/api/user/saved-filters")
async def user_saved_filter_create(payload: SavedFilterRequest, user=Depends(get_current_user)) -> dict[str, object]:
    return create_saved_filter(user.id, payload.model_dump())


@app.get("/api/user/watchlists")
async def user_watchlists(user=Depends(get_current_user)) -> dict[str, object]:
    return {"items": list_watchlists(user.id)}


@app.post("/api/user/watchlists")
async def user_watchlist_create(payload: WatchlistRequest, user=Depends(get_current_user)) -> dict[str, object]:
    return create_watchlist(user.id, payload.model_dump())


@app.get("/api/user/alerts")
async def user_alerts(user=Depends(get_current_user)) -> dict[str, object]:
    return {"items": list_alert_preferences(user.id)}


@app.post("/api/user/alerts")
async def user_alert_create(payload: AlertPreferenceRequest, user=Depends(get_current_user)) -> dict[str, object]:
    return create_alert_preference(user.id, payload.model_dump())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "snapshot", "payload": await store.snapshot()})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
