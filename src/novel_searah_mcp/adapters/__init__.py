from __future__ import annotations

from .base import (
    Adapter,
    AdapterError,
    NotFoundError,
    RateLimitedError,
    SourceUnavailableError,
)
from .kindle_jp import KindleJpAdapter
from .narou import NarouAdapter

__all__ = [
    "Adapter",
    "AdapterError",
    "KindleJpAdapter",
    "NarouAdapter",
    "NotFoundError",
    "RateLimitedError",
    "SourceUnavailableError",
]
