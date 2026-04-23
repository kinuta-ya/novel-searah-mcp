import time

import httpx
import pytest

from novel_searah_mcp.adapters.base import Adapter
from novel_searah_mcp.cache import Cache
from novel_searah_mcp.models import HealthStatus, Work


class DummyAdapter(Adapter):
    name = "narou"

    async def search(self, query: str, limit: int = 20) -> list[Work]:
        return []

    async def ranking(
        self,
        category: str | None = None,
        period: str = "daily",
        limit: int = 20,
    ) -> list[Work]:
        return []

    async def detail(self, source_id: str) -> Work:
        return Work(source="narou", source_id=source_id, title="stub")


@pytest.fixture
def adapter(tmp_path) -> DummyAdapter:
    return DummyAdapter(httpx.AsyncClient(), Cache(tmp_path), rps=10.0)


async def test_throttle_enforces_interval(adapter: DummyAdapter) -> None:
    start = time.monotonic()
    await adapter._throttle()
    await adapter._throttle()
    await adapter._throttle()
    elapsed = time.monotonic() - start
    # rps=10 → 最小インターバル=0.1秒。3回で少なくとも0.2秒は経過する
    assert elapsed >= 0.2


async def test_default_health_is_ok(adapter: DummyAdapter) -> None:
    status = await adapter.health()
    assert isinstance(status, HealthStatus)
    assert status.ok is True
    assert status.name == "narou"
