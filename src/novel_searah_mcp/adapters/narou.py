from __future__ import annotations

from typing import Any, ClassVar

import httpx
from pydantic import HttpUrl

from ..cache import Cache
from ..models import Metrics, SourceName, Work
from .base import (
    Adapter,
    AdapterError,
    NotFoundError,
    RateLimitedError,
    SourceUnavailableError,
)


class NarouAdapter(Adapter):
    """小説家になろう公式API（https://api.syosetu.com/novelapi/api/）用アダプター。"""

    name: ClassVar[SourceName] = "narou"
    BASE_URL: ClassVar[str] = "https://api.syosetu.com/novelapi/api/"

    _PERIOD_TO_ORDER: ClassVar[dict[str, str]] = {
        "daily": "dailypoint",
        "weekly": "weeklypoint",
        "monthly": "monthlypoint",
        "quarterly": "quarterpoint",
        "yearly": "yearlypoint",
        "all": "hyoka",
    }

    async def search(self, query: str, limit: int = 20) -> list[Work]:
        return await self._query(
            method="search",
            params={"word": query, "lim": min(max(limit, 1), 500)},
        )

    async def ranking(
        self,
        category: str | None = None,
        period: str = "daily",
        limit: int = 20,
    ) -> list[Work]:
        order = self._PERIOD_TO_ORDER.get(period, "dailypoint")
        params: dict[str, Any] = {"order": order, "lim": min(max(limit, 1), 500)}
        if category:
            params["genre"] = category
        return await self._query(method="ranking", params=params)

    async def detail(self, source_id: str) -> Work:
        works = await self._query(
            method="detail",
            params={"ncode": source_id},
        )
        if not works:
            raise NotFoundError(f"ncode not found: {source_id}")
        return works[0]

    async def _query(self, *, method: str, params: dict[str, Any]) -> list[Work]:
        cache_key = Cache.make_key(self.name, method, **params)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return [Work.model_validate(w) for w in cached]

        await self._throttle()
        request_params = {**params, "out": "json"}

        try:
            response = await self.client.get(self.BASE_URL, params=request_params)
        except httpx.RequestError as e:
            raise SourceUnavailableError(f"narou request failed: {e}") from e

        if response.status_code == 429:
            raise RateLimitedError("narou API returned 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"narou API {response.status_code}")
        if response.status_code >= 400:
            raise AdapterError(f"narou API {response.status_code}: {response.text[:200]}")

        data = response.json()
        if not isinstance(data, list) or not data:
            raise AdapterError("narou API: unexpected response format")

        items = [x for x in data[1:] if isinstance(x, dict)]
        works = [self._to_work(item) for item in items]

        self.cache.set(
            cache_key,
            [w.model_dump(mode="json") for w in works],
            ttl=self.default_ttl,
        )
        return works

    def _to_work(self, item: dict[str, Any]) -> Work:
        ncode = str(item.get("ncode", ""))
        keyword = item.get("keyword") or ""
        tags = [t for t in keyword.split() if t]

        genre_raw = item.get("genre")
        genre = str(genre_raw) if genre_raw is not None else None

        url = HttpUrl(f"https://ncode.syosetu.com/{ncode.lower()}/") if ncode else None

        return Work(
            source=self.name,
            source_id=ncode,
            title=str(item.get("title") or ""),
            author=item.get("writer"),
            tags=tags,
            synopsis=item.get("story"),
            genre=genre,
            url=url,
            metrics=Metrics(
                bookmarks=item.get("fav_novel_cnt"),
                points=item.get("all_point"),
                reviews=item.get("review_cnt"),
                word_count=item.get("length"),
            ),
            raw=item,
        )
