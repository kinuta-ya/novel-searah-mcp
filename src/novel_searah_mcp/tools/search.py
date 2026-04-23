from __future__ import annotations

from collections.abc import Mapping

from ..adapters.base import Adapter
from ..models import Work


class UnknownSourceError(ValueError):
    pass


async def search_works(
    adapters: Mapping[str, Adapter],
    query: str,
    limit: int = 20,
    source: str = "narou",
) -> list[Work]:
    """指定ソースで作品をキーワード検索する。"""
    adapter = _resolve(adapters, source)
    return await adapter.search(query, limit=limit)


async def get_ranking(
    adapters: Mapping[str, Adapter],
    period: str = "daily",
    limit: int = 20,
    source: str = "narou",
    category: str | None = None,
) -> list[Work]:
    """指定ソースの期間別ランキングを取得する。"""
    adapter = _resolve(adapters, source)
    return await adapter.ranking(category=category, period=period, limit=limit)


def _resolve(adapters: Mapping[str, Adapter], source: str) -> Adapter:
    if source not in adapters:
        raise UnknownSourceError(
            f"unknown source '{source}'. available: {sorted(adapters.keys())}"
        )
    return adapters[source]
