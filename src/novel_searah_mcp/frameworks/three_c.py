from __future__ import annotations

from .base import Framework, FrameworkInput, FrameworkOutput


class ThreeCFramework(Framework):
    name = "3c"
    display_name = "3C分析"
    description = "Customer / Competitor / Company の3軸で市場環境を整理する"

    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        raise NotImplementedError("3C build is not yet implemented")
