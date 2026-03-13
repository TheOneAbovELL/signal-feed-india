from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import get_current_user, hash_password, issue_access_token, verify_password
from .cache import cache
from .config import settings
from .db import init_db
from .feeds import ingest_once
from .on_this_day import fetch_on_this_day
from .persistence import (
    create_alert_preference,
    create_saved_filter,
    create_user,
    create_watchlist,
    create_workspace,
    get_source_trust_report,
    get_story_detail_payload,
    get_user_by_email,
    latest_story_timestamp,
    list_alert_preferences,
    list_saved_filters,
    list_watchlists,
    list_workspaces,
    seed_sources,
    social_model_definition,
)
from .schemas import AlertPreferenceRequest, LoginRequest, RegisterRequest, SavedFilterRequest, WatchlistRequest, WorkspaceRequest
from .store import store
from .tasks import start_scheduler, stop_scheduler


BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title=settings.app_name, version=settings.app_version)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
api_v1 = APIRouter(prefix="/api/v1")
legacy_api = APIRouter(prefix="/api")


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
            cache.invalidate("snapshot:latest")
            payload = await store.snapshot()
            cache.publish("snapshot_updates", {"generated_at": payload["generated_at"]})
            await manager.broadcast({"type": "snapshot", "payload": payload})
        await asyncio.sleep(10)


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    seed_sources(settings.feeds)
    initial_snapshot = await store.snapshot()
    if initial_snapshot["story_count"] == 0:
        await ingest_once(settings.feeds)
        cache.invalidate("snapshot:latest")
    app.state.snapshot_watcher = asyncio.create_task(snapshot_watcher())
    app.state.scheduler = start_scheduler()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    stop_scheduler()
    task = app.state.snapshot_watcher
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


async def _snapshot() -> dict[str, object]:
    return await store.snapshot()


@api_v1.get("/health")
async def health_v1() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name.lower().replace(" ", "-"),
        "mode": "api-only",
        "environment": settings.environment,
    }


@api_v1.get("/snapshot")
async def snapshot_v1() -> dict[str, object]:
    return await _snapshot()


@api_v1.get("/on-this-day")
async def on_this_day_v1() -> dict[str, object]:
    return await fetch_on_this_day()


@api_v1.get("/headlines")
async def headlines_v1(
    topic: str | None = Query(default=None),
    region: str | None = Query(default=None),
    q: str | None = Query(default=None),
    sentiment: str | None = Query(default=None),
) -> dict[str, object]:
    snapshot = await _snapshot()
    headlines = snapshot["headlines"]
    if topic:
        headlines = [item for item in headlines if topic in item["topics"]]
    if region:
        headlines = [item for item in headlines if region in item["regions"]]
    if sentiment:
        headlines = [item for item in headlines if item["sentiment"] == sentiment]
    if q:
        needle = q.lower()
        headlines = [item for item in headlines if needle in item["title"].lower() or needle in item["summary"].lower() or needle in item["source"].lower()]
    return {"items": headlines, "count": len(headlines)}


@api_v1.get("/stories/{story_id}")
async def story_detail_v1(story_id: str) -> dict[str, object]:
    payload = get_story_detail_payload(story_id)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return payload


@api_v1.get("/analytics/history")
async def analytics_history(window: str = Query(default="24h", pattern="^(1h|24h|7d)$")) -> dict[str, object]:
    snapshot = await _snapshot()
    return {"window": window, "points": snapshot["history"][window]}


@api_v1.get("/analytics/source-trust")
async def analytics_source_trust() -> dict[str, object]:
    return {"items": get_source_trust_report()}


@api_v1.get("/analytics/social-model")
async def analytics_social_model() -> dict[str, object]:
    return social_model_definition()


@api_v1.post("/auth/register")
async def auth_register(payload: RegisterRequest) -> dict[str, object]:
    try:
        user = create_user(payload.email, payload.full_name, hash_password(payload.password))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    token = issue_access_token(int(user["id"]))
    return {"user": user, **token}


@api_v1.post("/auth/login")
async def auth_login(payload: LoginRequest) -> dict[str, object]:
    user = get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = issue_access_token(user.id)
    return {"user": {"id": user.id, "email": user.email, "full_name": user.full_name}, **token}


@api_v1.get("/auth/me")
async def auth_me(user=Depends(get_current_user)) -> dict[str, object]:
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "workspaces": list_workspaces(user.id)}


@api_v1.get("/user/workspaces")
async def user_workspaces(user=Depends(get_current_user)) -> dict[str, object]:
    return {"items": list_workspaces(user.id)}


@api_v1.post("/user/workspaces")
async def user_workspace_create(payload: WorkspaceRequest, user=Depends(get_current_user)) -> dict[str, object]:
    return create_workspace(user.id, payload.name, payload.is_private)


@api_v1.get("/user/saved-filters")
async def user_saved_filters(user=Depends(get_current_user)) -> dict[str, object]:
    return {"items": list_saved_filters(user.id)}


@api_v1.post("/user/saved-filters")
async def user_saved_filter_create(payload: SavedFilterRequest, user=Depends(get_current_user)) -> dict[str, object]:
    return create_saved_filter(user.id, payload.model_dump())


@api_v1.get("/user/watchlists")
async def user_watchlists(user=Depends(get_current_user)) -> dict[str, object]:
    return {"items": list_watchlists(user.id)}


@api_v1.post("/user/watchlists")
async def user_watchlist_create(payload: WatchlistRequest, user=Depends(get_current_user)) -> dict[str, object]:
    return create_watchlist(user.id, payload.model_dump())


@api_v1.get("/user/alerts")
async def user_alerts(user=Depends(get_current_user)) -> dict[str, object]:
    return {"items": list_alert_preferences(user.id)}


@api_v1.post("/user/alerts")
async def user_alert_create(payload: AlertPreferenceRequest, user=Depends(get_current_user)) -> dict[str, object]:
    return create_alert_preference(user.id, payload.model_dump())


for route_path, route_handler in [
    ("/health", health_v1),
    ("/snapshot", snapshot_v1),
    ("/on-this-day", on_this_day_v1),
    ("/headlines", headlines_v1),
    ("/stories/{story_id}", story_detail_v1),
    ("/analytics/history", analytics_history),
    ("/analytics/source-trust", analytics_source_trust),
    ("/analytics/social-model", analytics_social_model),
]:
    methods = ["GET"]
    legacy_api.add_api_route(route_path, route_handler, methods=methods)

legacy_api.add_api_route("/auth/register", auth_register, methods=["POST"])
legacy_api.add_api_route("/auth/login", auth_login, methods=["POST"])
legacy_api.add_api_route("/auth/me", auth_me, methods=["GET"])
legacy_api.add_api_route("/user/workspaces", user_workspaces, methods=["GET"])
legacy_api.add_api_route("/user/workspaces", user_workspace_create, methods=["POST"])
legacy_api.add_api_route("/user/saved-filters", user_saved_filters, methods=["GET"])
legacy_api.add_api_route("/user/saved-filters", user_saved_filter_create, methods=["POST"])
legacy_api.add_api_route("/user/watchlists", user_watchlists, methods=["GET"])
legacy_api.add_api_route("/user/watchlists", user_watchlist_create, methods=["POST"])
legacy_api.add_api_route("/user/alerts", user_alerts, methods=["GET"])
legacy_api.add_api_route("/user/alerts", user_alert_create, methods=["POST"])

app.include_router(api_v1)
app.include_router(legacy_api)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "snapshot", "payload": await _snapshot()})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


