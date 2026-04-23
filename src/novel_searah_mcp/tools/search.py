from __future__ import annotations

from ..adapters.narou import NarouAdapter
from ..models import Work


async def search_works(adapter: NarouAdapter, query: str, limit: int = 20) -> list[Work]:
    """作品をキーワード検索する。現状ソースは「なろう」のみ。"""
    return await adapter.search(query, limit=limit)


async def get_ranking(
    adapter: NarouAdapter,
    period: str = "daily",
    limit: int = 20,
    category: str | None = None,
) -> list[Work]:
    """期間別ランキングを取得する。period は daily/weekly/monthly/quarterly/yearly/all。"""
    return await adapter.ranking(category=category, period=period, limit=limit)
