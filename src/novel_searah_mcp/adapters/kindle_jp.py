from __future__ import annotations

from typing import Any, ClassVar

import httpx
from pydantic import HttpUrl
from selectolax.parser import HTMLParser, Node

from ..cache import Cache
from ..models import Metrics, SourceName, Work
from .base import (
    Adapter,
    AdapterError,
    NotFoundError,
    RateLimitedError,
    SourceUnavailableError,
)


class KindleJpAdapter(Adapter):
    """amazon.co.jp の Kindle 公開ページを解析するアダプター（実験的）。

    PA-APIを使わず公開HTMLを解析するため、Amazon側の構造変更で壊れやすい。
    period（daily/weekly/...）は API としては受け付けるが、Amazon の公開ページは
    現在のベストセラーのみ提供するため period 値は無視される。
    """

    name: ClassVar[SourceName] = "kindle_jp"
    default_ttl: ClassVar[int] = 3600  # ランキングは時間単位で更新されるため短め

    BASE_URL: ClassVar[str] = "https://www.amazon.co.jp"
    SEARCH_PATH: ClassVar[str] = "/s"
    RANKING_PATH: ClassVar[str] = "/gp/bestsellers/digital-text"

    async def search(self, query: str, limit: int = 20) -> list[Work]:
        html = await self._fetch_html(
            url=f"{self.BASE_URL}{self.SEARCH_PATH}",
            params={"k": query, "i": "digital-text"},
            method="search",
        )
        return self._parse_search(html)[:limit]

    async def ranking(
        self,
        category: str | None = None,
        period: str = "daily",
        limit: int = 20,
    ) -> list[Work]:
        path = self.RANKING_PATH
        if category:
            path = f"{path}/{category}"
        html = await self._fetch_html(
            url=f"{self.BASE_URL}{path}",
            params=None,
            method="ranking",
        )
        return self._parse_ranking(html)[:limit]

    async def detail(self, source_id: str) -> Work:
        html = await self._fetch_html(
            url=f"{self.BASE_URL}/dp/{source_id}",
            params=None,
            method="detail",
        )
        work = self._parse_detail(html, source_id)
        if work is None:
            raise NotFoundError(f"asin not found or unparseable: {source_id}")
        return work

    async def _fetch_html(
        self,
        *,
        url: str,
        params: dict[str, Any] | None,
        method: str,
    ) -> str:
        cache_payload: dict[str, Any] = {"url": url, **(params or {})}
        cache_key = Cache.make_key(self.name, method, **cache_payload)
        cached = self.cache.get(cache_key)
        if isinstance(cached, str):
            return cached

        await self._throttle()
        try:
            response = await self.client.get(url, params=params)
        except httpx.RequestError as e:
            raise SourceUnavailableError(f"kindle_jp request failed: {e}") from e

        if response.status_code == 429:
            raise RateLimitedError("kindle_jp returned 429")
        if response.status_code == 404:
            raise NotFoundError(f"kindle_jp 404: {url}")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"kindle_jp {response.status_code}")
        if response.status_code >= 400:
            raise AdapterError(f"kindle_jp {response.status_code}")

        html = response.text
        self.cache.set(cache_key, html, ttl=self.default_ttl)
        return html

    def _parse_search(self, html: str) -> list[Work]:
        parser = HTMLParser(html)
        works: list[Work] = []
        for el in parser.css('div[data-component-type="s-search-result"]'):
            asin = (el.attributes.get("data-asin") or "").strip()
            if not asin:
                continue
            title_el = el.css_first("h2 span")
            if title_el is None:
                continue
            title = title_el.text(strip=True)
            if not title:
                continue
            author = self._extract_author(el)
            works.append(self._make_work(asin=asin, title=title, author=author))
        return works

    def _parse_ranking(self, html: str) -> list[Work]:
        parser = HTMLParser(html)
        works: list[Work] = []
        rank = 0
        for el in parser.css(".zg-grid-general-faceout, [id^='gridItemRoot']"):
            link = el.css_first("a.a-link-normal[href*='/dp/']")
            if link is None:
                continue
            asin = self._extract_asin(link.attributes.get("href") or "")
            if not asin:
                continue
            title_el = link.css_first("div") or link.css_first("span")
            if title_el is None:
                continue
            title = title_el.text(strip=True)
            if not title:
                continue
            rank += 1
            works.append(
                self._make_work(asin=asin, title=title, author=None, sales_rank=rank)
            )
        return works

    def _parse_detail(self, html: str, asin: str) -> Work | None:
        parser = HTMLParser(html)
        title_el = parser.css_first("#productTitle")
        if title_el is None:
            return None
        title = title_el.text(strip=True)
        if not title:
            return None
        author_el = parser.css_first("#bylineInfo .author .a-link-normal") or parser.css_first(
            ".author .a-link-normal"
        )
        author = author_el.text(strip=True) if author_el else None
        return self._make_work(asin=asin, title=title, author=author)

    @staticmethod
    def _extract_asin(href: str) -> str | None:
        if "/dp/" not in href:
            return None
        tail = href.split("/dp/", 1)[1]
        asin = tail.split("/", 1)[0].split("?", 1)[0]
        return asin or None

    @staticmethod
    def _extract_author(card: Node) -> str | None:
        # 「by 著者名」形式を期待し、`a-size-base` 系の text を順に拾って
        # by 等の接続詞を弾いた最初の有意なテキストを返す。
        ignore = {"by", "—", "/", ",", "："}
        for sel in [".a-row .a-size-base", ".a-row a.a-size-base"]:
            for el in card.css(sel):
                text = el.text(strip=True)
                if text and text not in ignore:
                    return text
        return None

    def _make_work(
        self,
        *,
        asin: str,
        title: str,
        author: str | None,
        sales_rank: int | None = None,
    ) -> Work:
        return Work(
            source=self.name,
            source_id=asin,
            title=title,
            author=author,
            url=HttpUrl(f"{self.BASE_URL}/dp/{asin}"),
            metrics=Metrics(sales_rank=sales_rank),
        )
