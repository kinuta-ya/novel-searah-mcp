from __future__ import annotations

from novel_searah_mcp.frameworks.four_p import FourPFramework, FourPInput
from novel_searah_mcp.frameworks.persona import PersonaFramework, PersonaInput
from novel_searah_mcp.frameworks.stp import STPFramework, STPInput
from novel_searah_mcp.frameworks.swot import SWOTFramework, SWOTInput
from novel_searah_mcp.frameworks.three_c import ThreeCFramework, ThreeCInput
from novel_searah_mcp.tools.frameworks import build_framework


def test_3c_minimal_input_returns_missing_inputs() -> None:
    out = ThreeCFramework().build(ThreeCInput(title="俺TUEEE"))
    assert out.framework == "3c"
    assert "competitors" in out.missing_inputs
    assert "target_reader" in out.missing_inputs
    assert any("競合" in q for q in out.follow_up_questions)
    assert "## 3C分析: 俺TUEEE" in out.markdown


def test_3c_full_input_clears_missing() -> None:
    out = ThreeCFramework().build(
        ThreeCInput(
            title="俺TUEEE",
            target_reader="社会人男性",
            customer_needs="退社後の癒し",
            competitors=["転スラ", "オバロ"],
            company_strengths="毎日更新できる",
        )
    )
    assert out.missing_inputs == []
    assert "転スラ" in out.markdown


def test_stp_lists_segments_in_markdown() -> None:
    out = STPFramework().build(
        STPInput(title="作品A", segments=["中高生女子", "30代男性"])
    )
    assert "中高生女子" in out.markdown
    assert "30代男性" in out.markdown


def test_4p_renders_features_and_channels() -> None:
    out = FourPFramework().build(
        FourPInput(
            title="作品B",
            product_features=["主人公がチート", "テンポ重視"],
            channels=["なろう", "Kindle"],
            price_range="Web無料／単行本700円",
            promotion_ideas=["X宣伝", "試し読み"],
        )
    )
    assert out.missing_inputs == []
    assert "主人公がチート" in out.markdown
    assert "Kindle" in out.markdown


def test_swot_includes_cross_swot() -> None:
    out = SWOTFramework().build(
        SWOTInput(
            title="作品C",
            strengths=["筆力"],
            weaknesses=["更新遅い"],
            opportunities=["追放系ブーム"],
            threats=["なろう競合多数"],
        )
    )
    assert out.missing_inputs == []
    cross = out.data["cross_swot"]
    assert isinstance(cross, dict)
    assert "SO_aggressive" in cross
    assert "クロスSWOT" in out.markdown


def test_persona_demographics_split() -> None:
    out = PersonaFramework().build(
        PersonaInput(
            title="作品D",
            age_range="16-22歳",
            gender="女性",
            occupation="高校生",
        )
    )
    assert "16-22歳" in out.markdown
    # まだ未記入の項目があるので missing は空ではない
    assert "lifestyle_notes" in out.missing_inputs


def test_build_framework_dispatcher_works_for_all_five() -> None:
    for name in ["3c", "stp", "4p", "swot", "persona"]:
        out = build_framework(name, {"title": "作品"})
        assert out.framework == name
        assert out.markdown.startswith("## ")
