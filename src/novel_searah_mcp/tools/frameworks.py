from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ..frameworks import ALL_FRAMEWORKS, FrameworkOutput, get_framework


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


def build_framework(name: str, payload: dict[str, Any]) -> FrameworkOutput:
    """指定されたフレームワークを構築する。`name` は list_frameworks の name と一致。"""
    cls = get_framework(name)
    instance = cls()
    input_obj = cls.InputModel.model_validate(payload)
    return instance.build(input_obj)
