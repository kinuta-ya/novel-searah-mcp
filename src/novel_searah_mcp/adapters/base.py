from __future__ import annotations

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
        try:
            await self.search("テスト", limit=1)
            return HealthStatus(name=self.name, ok=True)
        except Exception as e:
            return HealthStatus(name=self.name, ok=False, message=str(e))
