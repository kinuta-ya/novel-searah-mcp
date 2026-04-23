from __future__ import annotations

from typing import Any

import httpx
import pytest

from novel_searah_mcp.adapters.base import (
    NotFoundError,
    RateLimitedError,
    SourceUnavailableError,
)
from novel_searah_mcp.adapters.kindle_jp import KindleJpAdapter
from novel_searah_mcp.cache import Cache

SEARCH_HTML = """
<html><body>
  <div data-component-type="s-search-result" data-asin="B0ABCD1234">
    <h2><a href="/dp/B0ABCD1234"><span>テスト電子書籍</span></a></h2>
    <div class="a-row">
      <span class="a-size-base">by</span>
      <span class="a-size-base">テスト著者</span>
    </div>
  </div>
  <div data-component-type="s-search-result" data-asin="B0EFGH5678">
    <h2><a href="/dp/B0EFGH5678"><span>もう一冊</span></a></h2>
  </div>
  <div data-component-type="s-search-result" data-asin="">
    <h2><a><span>無視されるべきデータなしの行</span></a></h2>
  </div>
</body></html>
"""

RANKING_HTML = """
<html><body>
  <div id="zg-ordered-list">
    <div class="zg-grid-general-faceout">
      <a class="a-link-normal" href="/dp/B0RANK00001/ref=foo">
        <div>1位の本</div>
      </a>
    </div>
    <div class="zg-grid-general-faceout">
      <a class="a-link-normal" href="/dp/B0RANK00002">
        <div>2位の本</div>
      </a>
    </div>
    <div class="zg-grid-general-faceout">
      <!-- リンクなしは無視される -->
      <span>broken</span>
    </div>
  </div>
</body></html>
"""

DETAIL_HTML = """
<html><body>
  <span id="productTitle">  商品タイトル  </span>
  <div id="bylineInfo">
    <span class="author">
      <a class="a-link-normal" href="/...">著者名</a>
    </span>
  </div>
</body></html>
"""


def make_adapter(handler: Any, tmp_path: Any) -> KindleJpAdapter:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return KindleJpAdapter(client, Cache(tmp_path), rps=1000.0)


async def test_search_parses_results(tmp_path: Any) -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, text=SEARCH_HTML)

    adapter = make_adapter(handler, tmp_path)
    works = await adapter.search("ラノベ", limit=10)

    assert "amazon.co.jp/s" in captured["url"]
    assert captured["params"]["k"] == "ラノベ"
    assert captured["params"]["i"] == "digital-text"

    assert len(works) == 2
    assert works[0].source == "kindle_jp"
    assert works[0].source_id == "B0ABCD1234"
    assert works[0].title == "テスト電子書籍"
    assert works[0].author == "テスト著者"
    assert str(works[0].url) == "https://www.amazon.co.jp/dp/B0ABCD1234"


async def test_ranking_extracts_asin_and_rank(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/gp/bestsellers/digital-text" in str(request.url)
        return httpx.Response(200, text=RANKING_HTML)

    adapter = make_adapter(handler, tmp_path)
    works = await adapter.ranking(period="daily", limit=10)

    assert len(works) == 2
    assert works[0].source_id == "B0RANK00001"
    assert works[0].title == "1位の本"
    assert works[0].metrics.sales_rank == 1
    assert works[1].metrics.sales_rank == 2


async def test_ranking_with_category_appends_path(tmp_path: Any) -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return httpx.Response(200, text=RANKING_HTML)

    adapter = make_adapter(handler, tmp_path)
    await adapter.ranking(category="2293143051")
    assert captured["path"].endswith("/digital-text/2293143051")


async def test_detail_returns_work(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/dp/B0DETAIL00" in str(request.url)
        return httpx.Response(200, text=DETAIL_HTML)

    adapter = make_adapter(handler, tmp_path)
    work = await adapter.detail("B0DETAIL00")
    assert work.title == "商品タイトル"
    assert work.author == "著者名"


async def test_detail_unparseable_raises_not_found(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>nothing here</body></html>")

    adapter = make_adapter(handler, tmp_path)
    with pytest.raises(NotFoundError):
        await adapter.detail("B0NONE00000")


async def test_429_maps_to_rate_limited(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    adapter = make_adapter(handler, tmp_path)
    with pytest.raises(RateLimitedError):
        await adapter.search("q")


async def test_5xx_maps_to_unavailable(tmp_path: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    adapter = make_adapter(handler, tmp_path)
    with pytest.raises(SourceUnavailableError):
        await adapter.search("q")


async def test_cache_hits_on_second_request(tmp_path: Any) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, text=SEARCH_HTML)

    adapter = make_adapter(handler, tmp_path)
    await adapter.search("ラノベ")
    await adapter.search("ラノベ")
    assert calls == 1


async def test_extract_asin_handles_various_url_forms() -> None:
    assert KindleJpAdapter._extract_asin("/dp/B0ABCD1234") == "B0ABCD1234"
    assert KindleJpAdapter._extract_asin("/dp/B0ABCD1234/ref=foo") == "B0ABCD1234"
    assert KindleJpAdapter._extract_asin("/dp/B0ABCD1234?ref=foo") == "B0ABCD1234"
    assert KindleJpAdapter._extract_asin("/no-dp-here") is None
    assert KindleJpAdapter._extract_asin("") is None
