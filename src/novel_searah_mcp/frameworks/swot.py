from __future__ import annotations

from .base import Framework, FrameworkInput, FrameworkOutput


class SWOTFramework(Framework):
    name = "swot"
    display_name = "SWOT分析"
    description = "強み・弱み・機会・脅威を洗い出し、クロスSWOTで戦略を導く"

    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        raise NotImplementedError("SWOT build is not yet implemented")
