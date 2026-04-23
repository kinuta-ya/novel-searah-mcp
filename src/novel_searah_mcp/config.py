from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from . import __version__


@dataclass(frozen=True)
class Config:
    cache_dir: Path
    user_agent: str
    log_level: str

    @classmethod
    def load(cls) -> Config:
        return cls(
            cache_dir=Path(
                os.environ.get(
                    "NOVEL_SEARAH_CACHE_DIR",
                    str(Path.home() / ".cache" / "novel-searah-mcp"),
                )
            ),
            user_agent=os.environ.get(
                "NOVEL_SEARAH_USER_AGENT",
                f"novel-searah-mcp/{__version__}",
            ),
            log_level=os.environ.get("NOVEL_SEARAH_LOG_LEVEL", "INFO"),
        )
