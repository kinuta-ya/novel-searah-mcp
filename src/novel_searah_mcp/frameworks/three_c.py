from __future__ import annotations

from pydantic import Field

from .base import Framework, FrameworkInput, FrameworkOutput

_PLACEHOLDER = "（要追記）"


class ThreeCInput(FrameworkInput):
    competitors: list[str] = Field(default_factory=list)
    company_strengths: str | None = None
    customer_needs: str | None = None


class ThreeCFramework(Framework):
    name = "3c"
    display_name = "3C分析"
    description = "Customer / Competitor / Company の3軸で市場環境を整理する"
    InputModel = ThreeCInput

    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        p = ThreeCInput.model_validate(payload.model_dump())

        missing: list[str] = []
        questions: list[str] = []
        if not p.target_reader:
            missing.append("target_reader")
            questions.append("想定する読者層はどんな人ですか？（年齢層・性別・趣味嗜好など）")
        if not p.competitors:
            missing.append("competitors")
            questions.append("ベンチマークしたい競合作品を3〜5本挙げてください。")
        if not p.customer_needs:
            missing.append("customer_needs")
            questions.append("読者がこの作品に求めるものは何ですか？")
        if not p.company_strengths:
            missing.append("company_strengths")
            questions.append("自分／作品の強みは何ですか？（執筆ペース・経験・人脈など）")

        data = {
            "customer": {
                "target_reader": p.target_reader or _PLACEHOLDER,
                "needs": p.customer_needs or _PLACEHOLDER,
            },
            "competitor": {
                "works": p.competitors,
                "differentiation": _PLACEHOLDER,
            },
            "company": {
                "title": p.title,
                "genre": p.genre or _PLACEHOLDER,
                "logline": p.logline or _PLACEHOLDER,
                "strengths": p.company_strengths or _PLACEHOLDER,
            },
        }

        markdown = self._render(p, data)

        return FrameworkOutput(
            framework=self.name,
            data=data,
            markdown=markdown,
            missing_inputs=missing,
            follow_up_questions=questions,
        )

    def _render(self, p: ThreeCInput, data: dict[str, object]) -> str:
        lines = [
            f"## 3C分析: {p.title}",
            "",
            "### Customer（顧客／読者）",
            f"- 想定読者: {p.target_reader or _PLACEHOLDER}",
            f"- ニーズ: {p.customer_needs or _PLACEHOLDER}",
            "",
            "### Competitor（競合）",
        ]
        if p.competitors:
            lines.extend(f"- {c}" for c in p.competitors)
        else:
            lines.append(f"- {_PLACEHOLDER}")
        lines.append("- 差別化ポイント: " + _PLACEHOLDER)
        lines.extend(
            [
                "",
                "### Company（自社／自分）",
                f"- 作品: {p.title}",
                f"- ジャンル: {p.genre or _PLACEHOLDER}",
                f"- ログライン: {p.logline or _PLACEHOLDER}",
                f"- 強み: {p.company_strengths or _PLACEHOLDER}",
            ]
        )
        return "\n".join(lines)
