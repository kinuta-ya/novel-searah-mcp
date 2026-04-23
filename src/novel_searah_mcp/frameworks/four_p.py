from __future__ import annotations

from .base import Framework, FrameworkInput, FrameworkOutput


class FourPFramework(Framework):
    name = "4p"
    display_name = "4P分析"
    description = "Product / Price / Place / Promotion のマーケティングミックスを整理する"

    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        raise NotImplementedError("4P build is not yet implemented")
