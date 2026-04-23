from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import diskcache


class Cache:
    def __init__(self, directory: Path | str) -> None:
        self._cache = diskcache.Cache(str(directory))

    def get(self, key: str) -> Any:
        return self._cache.get(key)

    def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        self._cache.set(key, value, expire=ttl)

    def close(self) -> None:
        self._cache.close()

    @staticmethod
    def make_key(adapter: str, method: str, **params: Any) -> str:
        """`<adapter>:<method>:<hash>` の形でキャッシュキーを生成する。

        paramsは sorted key でJSON化してハッシュ化するため、呼び出し順序に依存しない。
        """
        normalized = json.dumps(params, sort_keys=True, ensure_ascii=False, default=str)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        return f"{adapter}:{method}:{digest}"
