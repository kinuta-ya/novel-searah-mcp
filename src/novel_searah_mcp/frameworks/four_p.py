from __future__ import annotations

from pydantic import Field

from .base import Framework, FrameworkInput, FrameworkOutput

_PLACEHOLDER = "（要追記）"


class FourPInput(FrameworkInput):
    price_range: str | None = None
    channels: list[str] = Field(default_factory=list)
    promotion_ideas: list[str] = Field(default_factory=list)
    product_features: list[str] = Field(default_factory=list)


class FourPFramework(Framework):
    name = "4p"
    display_name = "4P分析"
    description = "Product / Price / Place / Promotion のマーケティングミックスを整理する"
    InputModel = FourPInput

    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        p = FourPInput.model_validate(payload.model_dump())

        missing: list[str] = []
        questions: list[str] = []
        if not p.product_features:
            missing.append("product_features")
            questions.append("作品の特徴的なセールスポイントを3〜5個挙げてください。")
        if not p.price_range:
            missing.append("price_range")
            questions.append(
                "想定価格帯は？（Web無料／単行本700円前後／電書500円前後 など）"
            )
        if not p.channels:
            missing.append("channels")
            questions.append("販売・配信チャネルは？（なろう／カクヨム／Kindle／書店 等）")
        if not p.promotion_ideas:
            missing.append("promotion_ideas")
            questions.append("プロモーション施策のアイデアは？（X、書評、フェア、試し読み等）")

        data = {
            "product": {
                "title": p.title,
                "genre": p.genre or _PLACEHOLDER,
                "logline": p.logline or _PLACEHOLDER,
                "features": p.product_features,
            },
            "price": {
                "range": p.price_range or _PLACEHOLDER,
                "rationale": _PLACEHOLDER,
            },
            "place": {
                "channels": p.channels,
            },
            "promotion": {
                "ideas": p.promotion_ideas,
                "primary_audience": p.target_reader or _PLACEHOLDER,
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

    def _render(self, p: FourPInput, data: dict[str, object]) -> str:
        lines = [
            f"## 4P分析: {p.title}",
            "",
            "### Product（製品）",
            f"- ジャンル: {p.genre or _PLACEHOLDER}",
            f"- ログライン: {p.logline or _PLACEHOLDER}",
            "- セールスポイント:",
        ]
        if p.product_features:
            lines.extend(f"  - {f}" for f in p.product_features)
        else:
            lines.append(f"  - {_PLACEHOLDER}")
        lines.extend(
            [
                "",
                "### Price（価格）",
                f"- 想定価格帯: {p.price_range or _PLACEHOLDER}",
                f"- 価格設定理由: {_PLACEHOLDER}",
                "",
                "### Place（流通／チャネル）",
            ]
        )
        if p.channels:
            lines.extend(f"- {c}" for c in p.channels)
        else:
            lines.append(f"- {_PLACEHOLDER}")
        lines.extend(
            [
                "",
                "### Promotion（販促）",
                f"- 主要オーディエンス: {p.target_reader or _PLACEHOLDER}",
                "- 施策アイデア:",
            ]
        )
        if p.promotion_ideas:
            lines.extend(f"  - {idea}" for idea in p.promotion_ideas)
        else:
            lines.append(f"  - {_PLACEHOLDER}")
        return "\n".join(lines)
