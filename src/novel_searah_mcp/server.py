from __future__ import annotations

import httpx
from mcp.server.fastmcp import FastMCP

from .adapters.base import Adapter
from .adapters.kindle_jp import KindleJpAdapter
from .adapters.narou import NarouAdapter
from .cache import Cache
from .config import Config
from .frameworks import FrameworkOutput
from .frameworks.four_p import FourPInput
from .frameworks.persona import PersonaInput
from .frameworks.stp import STPInput
from .frameworks.swot import SWOTInput
from .frameworks.three_c import ThreeCInput
from .models import Work
from .tools.frameworks import FrameworkInfo, build_framework, list_frameworks
from .tools.search import get_ranking, search_works


def build_server() -> FastMCP:
    config = Config.load()
    cache = Cache(config.cache_dir)
    client = httpx.AsyncClient(
        headers={"User-Agent": config.user_agent},
        timeout=15.0,
    )
    adapters: dict[str, Adapter] = {
        "narou": NarouAdapter(client, cache, rps=1.0),
        "kindle_jp": KindleJpAdapter(client, cache, rps=0.5),
    }

    server: FastMCP = FastMCP(
        "novel-searah-mcp",
        instructions=(
            "日本のライトノベル／なろう系小説向け、"
            "ビジネス／マーケティング視点の企画支援MCPサーバー。"
        ),
    )

    @server.tool(
        name="list_frameworks",
        description="利用可能なビジネス／マーケティングフレームワークの一覧を返す。",
    )
    def _list_frameworks() -> list[FrameworkInfo]:
        return list_frameworks()

    @server.tool(
        name="search_works",
        description=(
            "作品をキーワード検索する。source は narou / kindle_jp。"
            "なろうは最大 limit=500、Kindle は公開ページ解析のため概ね数十件程度。"
        ),
    )
    async def _search_works(
        query: str,
        limit: int = 20,
        source: str = "narou",
    ) -> list[Work]:
        return await search_works(adapters, query=query, limit=limit, source=source)

    @server.tool(
        name="get_ranking",
        description=(
            "期間別ランキングを取得する。source は narou / kindle_jp。"
            "なろうは period で daily/weekly/monthly/quarterly/yearly/all を切替。"
            "Kindle は公開ページの性質上、現在のベストセラーのみで period は無視される。"
        ),
    )
    async def _get_ranking(
        period: str = "daily",
        limit: int = 20,
        source: str = "narou",
        category: str | None = None,
    ) -> list[Work]:
        return await get_ranking(
            adapters, period=period, limit=limit, source=source, category=category
        )

    @server.tool(
        name="build_3c",
        description="3C分析（Customer/Competitor/Company）の構造化レポートを生成する。",
    )
    def _build_3c(payload: ThreeCInput) -> FrameworkOutput:
        return build_framework("3c", payload.model_dump())

    @server.tool(
        name="build_stp",
        description="STP分析（Segmentation/Targeting/Positioning）の構造化レポートを生成する。",
    )
    def _build_stp(payload: STPInput) -> FrameworkOutput:
        return build_framework("stp", payload.model_dump())

    @server.tool(
        name="build_4p",
        description="4P分析（Product/Price/Place/Promotion）の構造化レポートを生成する。",
    )
    def _build_4p(payload: FourPInput) -> FrameworkOutput:
        return build_framework("4p", payload.model_dump())

    @server.tool(
        name="build_swot",
        description="SWOT分析＋クロスSWOTの構造化レポートを生成する。",
    )
    def _build_swot(payload: SWOTInput) -> FrameworkOutput:
        return build_framework("swot", payload.model_dump())

    @server.tool(
        name="build_persona",
        description="読者ペルソナの構造化シートを生成する。",
    )
    def _build_persona(payload: PersonaInput) -> FrameworkOutput:
        return build_framework("persona", payload.model_dump())

    return server


def main() -> None:
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
