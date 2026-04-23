from novel_searah_mcp.frameworks import ALL_FRAMEWORKS, get_framework
from novel_searah_mcp.server import build_server
from novel_searah_mcp.tools.frameworks import list_frameworks


def test_list_frameworks_returns_all_mvp_five() -> None:
    result = list_frameworks()
    names = {f.name for f in result}
    assert names == {"3c", "stp", "4p", "swot", "persona"}


def test_list_frameworks_display_names_are_japanese() -> None:
    result = list_frameworks()
    for f in result:
        assert f.display_name
        assert f.description


def test_get_framework_lookup() -> None:
    cls = get_framework("3c")
    assert cls.name == "3c"
    assert cls in ALL_FRAMEWORKS


def test_server_builds_without_error() -> None:
    server = build_server()
    assert server.name == "novel-searah-mcp"
