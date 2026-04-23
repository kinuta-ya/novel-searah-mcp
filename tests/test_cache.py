from novel_searah_mcp.cache import Cache


def test_make_key_is_deterministic() -> None:
    a = Cache.make_key("narou", "search", query="異世界", limit=10)
    b = Cache.make_key("narou", "search", limit=10, query="異世界")
    assert a == b


def test_make_key_includes_adapter_and_method() -> None:
    key = Cache.make_key("kindle_jp", "ranking", category="ranobe")
    assert key.startswith("kindle_jp:ranking:")


def test_make_key_changes_with_params() -> None:
    a = Cache.make_key("narou", "search", query="A")
    b = Cache.make_key("narou", "search", query="B")
    assert a != b


def test_get_set(tmp_path) -> None:
    cache = Cache(tmp_path)
    cache.set("k", {"x": 1})
    assert cache.get("k") == {"x": 1}
    cache.close()
