from novel_searah_mcp import __version__
from novel_searah_mcp.models import Metrics, Work


def test_version() -> None:
    assert isinstance(__version__, str)


def test_work_minimal() -> None:
    w = Work(source="narou", source_id="n0000aa", title="テスト作品")
    assert w.title == "テスト作品"
    assert w.metrics == Metrics()
