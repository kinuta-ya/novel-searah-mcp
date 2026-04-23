from __future__ import annotations

from .base import Framework, FrameworkInput, FrameworkOutput

_PLACEHOLDER = "（要追記）"


class PersonaInput(FrameworkInput):
    age_range: str | None = None
    gender: str | None = None
    occupation: str | None = None
    lifestyle_notes: str | None = None
    reading_habits: str | None = None
    pain_points: str | None = None
    goals: str | None = None


class PersonaFramework(Framework):
    name = "persona"
    display_name = "ペルソナ設計"
    description = "想定読者を具体的な1人の人物像として記述するためのテンプレを生成する"
    InputModel = PersonaInput

    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        p = PersonaInput.model_validate(payload.model_dump())

        missing: list[str] = []
        questions: list[str] = []
        check_pairs = [
            (p.age_range, "age_range", "想定する年齢層は？（例: 16-22歳）"),
            (p.gender, "gender", "想定性別は？（男性／女性／不問など）"),
            (p.occupation, "occupation", "職業は？（高校生／大学生／会社員など）"),
            (p.lifestyle_notes, "lifestyle_notes", "ライフスタイル・趣味嗜好は？"),
            (p.reading_habits, "reading_habits", "読書習慣は？（投稿サイト中心／電書／紙）"),
            (p.pain_points, "pain_points", "読者は普段どんな不満や欠乏感を抱えていますか？"),
            (p.goals, "goals", "読者は読書を通じて何を得たいですか？"),
        ]
        for value, key, q in check_pairs:
            if not value:
                missing.append(key)
                questions.append(q)

        data = {
            "demographics": {
                "age_range": p.age_range or _PLACEHOLDER,
                "gender": p.gender or _PLACEHOLDER,
                "occupation": p.occupation or _PLACEHOLDER,
            },
            "psychographics": {
                "lifestyle": p.lifestyle_notes or _PLACEHOLDER,
                "reading_habits": p.reading_habits or _PLACEHOLDER,
            },
            "needs": {
                "pain_points": p.pain_points or _PLACEHOLDER,
                "goals": p.goals or _PLACEHOLDER,
            },
            "context": {
                "for_work": p.title,
                "summary_target_reader": p.target_reader or _PLACEHOLDER,
            },
        }

        markdown = self._render(p)

        return FrameworkOutput(
            framework=self.name,
            data=data,
            markdown=markdown,
            missing_inputs=missing,
            follow_up_questions=questions,
        )

    def _render(self, p: PersonaInput) -> str:
        return "\n".join(
            [
                f"## ペルソナ設計: {p.title}",
                "",
                "### Demographics（基本属性）",
                f"- 年齢層: {p.age_range or _PLACEHOLDER}",
                f"- 性別: {p.gender or _PLACEHOLDER}",
                f"- 職業: {p.occupation or _PLACEHOLDER}",
                "",
                "### Psychographics（価値観・行動）",
                f"- ライフスタイル: {p.lifestyle_notes or _PLACEHOLDER}",
                f"- 読書習慣: {p.reading_habits or _PLACEHOLDER}",
                "",
                "### Needs（ニーズ）",
                f"- ペインポイント: {p.pain_points or _PLACEHOLDER}",
                f"- ゴール: {p.goals or _PLACEHOLDER}",
                "",
                "### Context（位置付け）",
                f"- 対象作品: {p.title}",
                f"- 想定読者サマリ: {p.target_reader or _PLACEHOLDER}",
            ]
        )
