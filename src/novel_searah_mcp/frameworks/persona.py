from __future__ import annotations

from .base import Framework, FrameworkInput, FrameworkOutput


class PersonaFramework(Framework):
    name = "persona"
    display_name = "ペルソナ設計"
    description = "想定読者を具体的な1人の人物像として記述するためのテンプレを生成する"

    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        raise NotImplementedError("Persona build is not yet implemented")
