from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel, Field


class FrameworkInput(BaseModel):
    title: str
    genre: str | None = None
    logline: str | None = None
    target_reader: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class FrameworkOutput(BaseModel):
    framework: str
    data: dict[str, Any]
    markdown: str
    missing_inputs: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)


class Framework(ABC):
    name: ClassVar[str]
    display_name: ClassVar[str]
    description: ClassVar[str]
    InputModel: ClassVar[type[FrameworkInput]] = FrameworkInput

    @abstractmethod
    def build(self, payload: FrameworkInput) -> FrameworkOutput: ...

    def render_markdown(self, data: dict[str, Any]) -> str:
        lines = [f"## {self.display_name}", ""]
        for key, value in data.items():
            lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)
