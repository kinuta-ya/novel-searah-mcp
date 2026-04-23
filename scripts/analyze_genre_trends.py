"""なろうのジャンル別ランキングからタグ頻度・ブクマ中央値などを集計する。

ローカルで実行:
    uv run python scripts/analyze_genre_trends.py --period weekly --limit 30

オプション:
    --period    daily / weekly / monthly / quarterly / yearly / all (default: weekly)
    --limit     ジャンルごとの上位何件を集計するか (default: 30, max 500)
    --genres    カンマ区切りのジャンルコード（未指定なら下表のデフォルト）

Narou のジャンルコード抜粋:
    101 異世界〔恋愛〕  102 現実世界〔恋愛〕
    201 ハイファンタジー 202 ローファンタジー
    301 純文学  302 ヒューマンドラマ  303 歴史  304 推理  305 ホラー
    306 アクション  307 コメディー
    401 VRゲーム  402 宇宙  403 空想科学  404 パニック
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from statistics import median

import httpx

from novel_searah_mcp.adapters.narou import NarouAdapter
from novel_searah_mcp.cache import Cache
from novel_searah_mcp.config import Config
from novel_searah_mcp.models import Work

DEFAULT_GENRES: dict[str, str] = {
    "101": "異世界恋愛",
    "102": "現代恋愛",
    "201": "ハイファンタジー",
    "202": "ローファンタジー",
    "303": "歴史",
    "304": "推理",
    "307": "コメディー",
}


async def fetch_genre(
    adapter: NarouAdapter, genre_code: str, period: str, limit: int
) -> list[Work]:
    return await adapter.ranking(category=genre_code, period=period, limit=limit)


def summarize(works: list[Work]) -> dict[str, object]:
    tags: Counter[str] = Counter()
    bookmarks: list[int] = []
    points: list[int] = []
    lengths: list[int] = []
    for w in works:
        tags.update(w.tags)
        if w.metrics.bookmarks is not None:
            bookmarks.append(w.metrics.bookmarks)
        if w.metrics.points is not None:
            points.append(w.metrics.points)
        if w.metrics.word_count is not None:
            lengths.append(w.metrics.word_count)
    return {
        "count": len(works),
        "top_tags": tags.most_common(10),
        "bookmark_median": int(median(bookmarks)) if bookmarks else None,
        "bookmark_max": max(bookmarks) if bookmarks else None,
        "point_median": int(median(points)) if points else None,
        "length_median": int(median(lengths)) if lengths else None,
        "top_titles": [(w.title, w.metrics.bookmarks) for w in works[:5]],
    }


def render_report(
    period: str, genres: dict[str, str], summaries: dict[str, dict[str, object]]
) -> str:
    lines = [f"# ジャンル動向サマリ（{period}、なろう公式API）", ""]
    for code, label in genres.items():
        s = summaries.get(code)
        if s is None:
            continue
        lines.append(f"## {label} (genre={code})")
        lines.append(f"- 件数: {s['count']}")
        lines.append(f"- ブクマ中央値: {s['bookmark_median']}（最大 {s['bookmark_max']}）")
        lines.append(f"- ポイント中央値: {s['point_median']}")
        lines.append(f"- 文字数中央値: {s['length_median']}")
        lines.append("- 頻出タグ TOP10:")
        for tag, n in s["top_tags"]:  # type: ignore[union-attr]
            lines.append(f"  - {tag} × {n}")
        lines.append("- 上位5件:")
        for title, fav in s["top_titles"]:  # type: ignore[union-attr]
            lines.append(f"  - {title}（ブクマ {fav}）")
        lines.append("")
    return "\n".join(lines)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", default="weekly")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--genres", default=None, help="comma-separated genre codes")
    args = parser.parse_args()

    genres = DEFAULT_GENRES
    if args.genres:
        codes = [c.strip() for c in args.genres.split(",") if c.strip()]
        genres = {c: DEFAULT_GENRES.get(c, c) for c in codes}

    config = Config.load()
    cache = Cache(config.cache_dir)
    async with httpx.AsyncClient(
        headers={"User-Agent": config.user_agent},
        timeout=15.0,
    ) as client:
        adapter = NarouAdapter(client, cache, rps=1.0)
        summaries: dict[str, dict[str, object]] = {}
        for code, label in genres.items():
            print(f"[fetch] {label} (genre={code}) ...", flush=True)
            works = await fetch_genre(adapter, code, args.period, args.limit)
            summaries[code] = summarize(works)

    print()
    print(render_report(args.period, genres, summaries))


if __name__ == "__main__":
    asyncio.run(main())
