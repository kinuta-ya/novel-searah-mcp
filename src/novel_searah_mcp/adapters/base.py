from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import ClassVar

import httpx

from ..cache import Cache
from ..models import HealthStatus, SourceName, Work


class AdapterError(Exception):
    pass


class RateLimitedError(AdapterError):
    pass


class NotFoundError(AdapterError):
    pass


class SourceUnavailableError(AdapterError):
    pass


class Adapter(ABC):
    name: ClassVar[SourceName]
    default_ttl: ClassVar[int] = 3600

    def __init__(self, client: httpx.AsyncClient, cache: Cache, *, rps: float = 1.0) -> None:
        self.client = client
        self.cache = cache
        self._min_interval = 1.0 / rps
        self._last_call_at: float = 0.0
        self._throttle_lock: asyncio.Lock | None = None

    async def _throttle(self) -> None:
        """直前呼び出しから `_min_interval` 秒経過するまで待つ。"""
        if self._throttle_lock is None:
            self._throttle_lock = asyncio.Lock()
        async with self._throttle_lock:
            elapsed = time.monotonic() - self._last_call_at
            wait = self._min_interval - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call_at = time.monotonic()

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[Work]: ...

    @abstractmethod
    async def ranking(
        self,
        category: str | None = None,
        period: str = "daily",
        limit: int = 20,
    ) -> list[Work]: ...

    @abstractmethod
    async def detail(self, source_id: str) -> Work: ...

    async def health(self) -> HealthStatus:
        """デフォルトは副作用なしで ok=True を返す。本当の疎通確認は子で上書きする。"""
        return HealthStatus(
            name=self.name,
            ok=True,
            message="default health (override in subclass for real check)",
        )
