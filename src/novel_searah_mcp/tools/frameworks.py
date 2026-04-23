from __future__ import annotations

from pydantic import BaseModel

from ..frameworks import ALL_FRAMEWORKS


class FrameworkInfo(BaseModel):
    name: str
    display_name: str
    description: str


def list_frameworks() -> list[FrameworkInfo]:
    """登録されているビジネスフレームワークの一覧を返す。"""
    return [
        FrameworkInfo(
            name=cls.name,
            display_name=cls.display_name,
            description=cls.description,
        )
        for cls in ALL_FRAMEWORKS
    ]
