from __future__ import annotations

from pydantic import Field

from .base import Framework, FrameworkInput, FrameworkOutput

_PLACEHOLDER = "（要追記）"


class SWOTInput(FrameworkInput):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)
    market_trends: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)


class SWOTFramework(Framework):
    name = "swot"
    display_name = "SWOT分析"
    description = "強み・弱み・機会・脅威を洗い出し、クロスSWOTで戦略を導く"
    InputModel = SWOTInput

    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        p = SWOTInput.model_validate(payload.model_dump())

        missing: list[str] = []
        questions: list[str] = []
        for axis, label in [
            (p.strengths, "Strengths（強み）"),
            (p.weaknesses, "Weaknesses（弱み）"),
            (p.opportunities, "Opportunities（機会）"),
            (p.threats, "Threats（脅威）"),
        ]:
            if not axis:
                key = label.split("（")[0].strip().lower()
                missing.append(key)
                questions.append(f"{label} を3つほど挙げてください。")

        cross = self._cross_swot(p)

        data = {
            "swot": {
                "strengths": p.strengths,
                "weaknesses": p.weaknesses,
                "opportunities": p.opportunities,
                "threats": p.threats,
            },
            "context": {
                "market_trends": p.market_trends,
                "competitors": p.competitors,
            },
            "cross_swot": cross,
        }

        markdown = self._render(p, cross)

        return FrameworkOutput(
            framework=self.name,
            data=data,
            markdown=markdown,
            missing_inputs=missing,
            follow_up_questions=questions,
        )

    def _cross_swot(self, p: SWOTInput) -> dict[str, str]:
        s = "強み" if p.strengths else _PLACEHOLDER
        w = "弱み" if p.weaknesses else _PLACEHOLDER
        o = "機会" if p.opportunities else _PLACEHOLDER
        t = "脅威" if p.threats else _PLACEHOLDER
        return {
            "SO_aggressive": f"{s}を活かして{o}を取りに行く積極戦略（要追記）",
            "WO_improvement": f"{w}を補強して{o}を逃さない改善戦略（要追記）",
            "ST_differentiation": f"{s}で{t}に対抗する差別化戦略（要追記）",
            "WT_defensive": f"{w}と{t}の重なりを避ける防衛戦略（要追記）",
        }

    def _render(self, p: SWOTInput, cross: dict[str, str]) -> str:
        def section(title: str, items: list[str]) -> list[str]:
            out = [f"### {title}"]
            if items:
                out.extend(f"- {x}" for x in items)
            else:
                out.append(f"- {_PLACEHOLDER}")
            out.append("")
            return out

        lines = [f"## SWOT分析: {p.title}", ""]
        lines += section("Strengths（強み）", p.strengths)
        lines += section("Weaknesses（弱み）", p.weaknesses)
        lines += section("Opportunities（機会）", p.opportunities)
        lines += section("Threats（脅威）", p.threats)
        lines += [
            "### クロスSWOT（戦略導出）",
            f"- SO（積極）: {cross['SO_aggressive']}",
            f"- WO（改善）: {cross['WO_improvement']}",
            f"- ST（差別化）: {cross['ST_differentiation']}",
            f"- WT（防衛）: {cross['WT_defensive']}",
        ]
        return "\n".join(lines)
