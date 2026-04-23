from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl

SourceName = Literal[
    "narou",
    "kindle_jp",
    "kobo_jp",
    "booklive",
    "kakuyomu",
    "alphapolis",
    "publishers",
    "google_trends",
    "bookwalker",
    "novelup",
    "twitter",
]


class Metrics(BaseModel):
    bookmarks: int | None = None
    points: int | None = None
    reviews: int | None = None
    rating: float | None = None
    rank: int | None = None
    sales_rank: int | None = None
    word_count: int | None = None


class Work(BaseModel):
    source: SourceName
    source_id: str
    title: str
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    synopsis: str | None = None
    genre: str | None = None
    url: HttpUrl | None = None
    metrics: Metrics = Field(default_factory=Metrics)
    published_at: datetime | None = None
    updated_at: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict, exclude=True)


class HealthStatus(BaseModel):
    name: str
    ok: bool
    latency_ms: float | None = None
    message: str | None = None
