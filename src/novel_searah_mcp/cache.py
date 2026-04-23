from __future__ import annotations

from pathlib import Path
from typing import Any

import diskcache


class Cache:
    def __init__(self, directory: Path | str) -> None:
        self._cache = diskcache.Cache(str(directory))

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        self._cache.set(key, value, expire=ttl)

    def close(self) -> None:
        self._cache.close()
