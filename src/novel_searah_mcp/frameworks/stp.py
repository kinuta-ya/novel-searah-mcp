from __future__ import annotations

from .base import Framework, FrameworkInput, FrameworkOutput


class STPFramework(Framework):
    name = "stp"
    display_name = "STP分析"
    description = "セグメンテーション・ターゲティング・ポジショニングで読者戦略を設計する"

    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        raise NotImplementedError("STP build is not yet implemented")
