from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class WorkspaceRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    is_private: bool = True


class SavedFilterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    workspace_id: int | None = None
    topic: str | None = None
    region: str | None = None
    query: str | None = None
    segment: str | None = None
    view_mode: str | None = None


class WatchlistRequest(BaseModel):
    label: str = Field(min_length=2, max_length=255)
    workspace_id: int | None = None
    query: str | None = None
    topic: str | None = None
    region: str | None = None
    source_name: str | None = None


class AlertPreferenceRequest(BaseModel):
    workspace_id: int | None = None
    topic: str | None = None
    region: str | None = None
    min_social_score: int = Field(default=70, ge=0, le=100)
    delivery_channel: str = Field(default="email", min_length=2, max_length=64)
    enabled: bool = True
