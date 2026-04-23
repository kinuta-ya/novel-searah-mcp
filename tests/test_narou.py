from __future__ import annotations

from typing import Any

import httpx
import pytest

from novel_searah_mcp.adapters.base import (
    AdapterError,
    NotFoundError,
    RateLimitedError,
    SourceUnavailableError,
)
from novel_searah_mcp.adapters.narou import NarouAdapter
from novel_searah_mcp.cache import Cache


def sample_response() -> list[dict[str, Any]]:
    return [
        {"allcount": 2},
        {
            "ncode": "N0001AA",
            "title": "テスト異世界転生",
            "writer": "テスト著者",
            "story": "異世界に飛ばされた主人公の物語。",
            "keyword": "異世界 転生 チート",
            "genre": 101,
            "fav_novel_cnt": 12345,
            "all_point": 54321,
            "review_cnt": 42,
            "length": 100000,
        },
        {
            "ncode": "N0002BB",
            "title": "もう一つの作品",
            "writer": "作者2",
            "story": None,
            "keyword": "",
            "genre": 102,
        },
    ]


def make_adapter(handler: Any, tmp_path: Any, rps: float = 1000.0) -> NarouAdapter:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return NarouAdapter(client, Cache(tmp_path), rps=rps)


async def test_search_parses_all_fields(tmp_path: Any) -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json=sample_response())

    adapter = make_adapter(handler, tmp_path)
    works = await adapter.search("異世界", limit=5)

    assert captured["url"].startswith("https://api.syosetu.com/novelapi/api/")
    assert captured["params"]["word"] == "異世界"
    assert captured["params"]["lim"] == "5"
    assert captured["params"]["out"] == "json"

    assert len(works) == 2
    first = works[0]
    assert first.source == "narou"
    assert first.source_id == "N0001AA"
    assert first.title == "テスト異世界転生"
    assert first.author == "テスト著者"
    assert first.tags == ["異世界", "転生", "チート"]
    assert first.genre == "101"
    assert first.metrics.bookmarks == 12345
    assert first.metrics.points == 54321
    assert first.metrics.word_count == 100000
    assert str(first.url) == "https://ncode.syosetu.com/n0001aa/"


async def test_ranking_maps_period_to_order(tmp_path: Any) -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json=sample_response())

    adapter = make_adapter(handler, tmp_path)
    await adapter.ranking(period="weekly", limit=10)

    assert captured["params"]["order"] == "weeklypoint"
    assert captured["params"]["lim"] == "10"


async def test_limit_clamped_to_api_max(tmp_path: Any) -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json=[{"allcount": 0}])

    adapter = make_adapter(handler, tmp_path)
    await adapter.search("q", limit=9999)
    assert captured["params"]["lim"] == "500"


async def test_cache_avoids_second_request(tmp_path: Any) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=sample_response())

    adapter = make_adapter(handler, tmp_path)
    r1 = await adapter.search("異世界")
    r2 = await adapter.search("異世界")
    assert calls == 1
    assert [w.source_id for w in r1] == [w.source_id for w in r2]


async def test_detail_raises_not_found(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"allcount": 0}])

    adapter = make_adapter(handler, tmp_path)
    with pytest.raises(NotFoundError):
        await adapter.detail("N9999ZZ")


async def test_rate_limit_maps_to_exception(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    adapter = make_adapter(handler, tmp_path)
    with pytest.raises(RateLimitedError):
        await adapter.search("q")


async def test_server_error_maps_to_unavailable(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    adapter = make_adapter(handler, tmp_path)
    with pytest.raises(SourceUnavailableError):
        await adapter.search("q")


async def test_client_error_maps_to_adapter_error(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="bad param")

    adapter = make_adapter(handler, tmp_path)
    with pytest.raises(AdapterError):
        await adapter.search("q")


async def test_network_failure_maps_to_unavailable(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    adapter = make_adapter(handler, tmp_path)
    with pytest.raises(SourceUnavailableError):
        await adapter.search("q")


async def test_empty_keyword_yields_empty_tags(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=sample_response())

    adapter = make_adapter(handler, tmp_path)
    works = await adapter.search("q")
    assert works[1].tags == []
