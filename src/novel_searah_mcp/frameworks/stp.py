from __future__ import annotations

from pydantic import Field

from .base import Framework, FrameworkInput, FrameworkOutput

_PLACEHOLDER = "（要追記）"


class STPInput(FrameworkInput):
    segments: list[str] = Field(default_factory=list)
    primary_target: str | None = None
    positioning_statement: str | None = None


class STPFramework(Framework):
    name = "stp"
    display_name = "STP分析"
    description = "セグメンテーション・ターゲティング・ポジショニングで読者戦略を設計する"
    InputModel = STPInput

    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        p = STPInput.model_validate(payload.model_dump())

        missing: list[str] = []
        questions: list[str] = []
        if not p.segments:
            missing.append("segments")
            questions.append(
                "想定する読者セグメントを3〜5個挙げてください。"
                "（例: 中高生女子、社会人ラノベ層、なろう系ヘビーリーダーなど）"
            )
        if not p.primary_target:
            missing.append("primary_target")
            questions.append("一番訴求したいセグメントはどれですか？")
        if not p.positioning_statement:
            missing.append("positioning_statement")
            questions.append(
                "ポジショニングステートメントを一言で言うと？"
                "（『〇〇な人にとって、本作は××である』形式）"
            )

        data = {
            "segmentation": {
                "candidate_segments": p.segments,
                "criteria": "（年齢／嗜好ジャンル／消費スタイル等で切り分ける）",
            },
            "targeting": {
                "primary": p.primary_target or _PLACEHOLDER,
                "rationale": _PLACEHOLDER,
            },
            "positioning": {
                "statement": p.positioning_statement or _PLACEHOLDER,
                "key_differentiators": _PLACEHOLDER,
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

    def _render(self, p: STPInput, data: dict[str, object]) -> str:
        lines = [
            f"## STP分析: {p.title}",
            "",
            "### Segmentation（市場細分化）",
        ]
        if p.segments:
            lines.extend(f"- {s}" for s in p.segments)
        else:
            lines.append(f"- {_PLACEHOLDER}")
        lines.extend(
            [
                "",
                "### Targeting（ターゲット選定）",
                f"- メインターゲット: {p.primary_target or _PLACEHOLDER}",
                f"- 選定理由: {_PLACEHOLDER}",
                "",
                "### Positioning（ポジショニング）",
                f"- ステートメント: {p.positioning_statement or _PLACEHOLDER}",
                f"- 差別化ポイント: {_PLACEHOLDER}",
            ]
        )
        return "\n".join(lines)
