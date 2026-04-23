from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .tools.frameworks import FrameworkInfo, list_frameworks


def build_server() -> FastMCP:
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

    return server


def main() -> None:
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
