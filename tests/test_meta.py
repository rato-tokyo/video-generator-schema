import pytest
from pydantic import ValidationError

from video_generator_schema import TOP_BAR_TEXT_MAX_LENGTH, Meta


class TestMeta:
    def test_valid_with_alias(self):
        m = Meta(
            companyName="テスト株式会社",
            topBarText="{accent}テスト{/accent}の会社",
            companyIntro="テスト株式会社\n・業種：テスト",
        )
        assert m.company_name == "テスト株式会社"
        assert m.top_bar_text == "{accent}テスト{/accent}の会社"

    def test_valid_with_python_names(self):
        m = Meta(
            company_name="テスト株式会社",
            top_bar_text="テキスト",
            company_intro="紹介文",
        )
        assert m.company_name == "テスト株式会社"

    def test_serialization_with_alias(self):
        m = Meta(
            companyName="テスト",
            topBarText="テキスト",
            companyIntro="紹介",
        )
        dumped = m.model_dump(by_alias=True)
        assert "companyName" in dumped
        assert "topBarText" in dumped
        assert "companyIntro" in dumped

    def test_empty_company_name(self):
        with pytest.raises(ValidationError):
            Meta(companyName="", topBarText="text", companyIntro="text")

    def test_top_bar_text_at_max(self):
        text = "あ" * TOP_BAR_TEXT_MAX_LENGTH
        m = Meta(companyName="テスト", topBarText=text, companyIntro="紹介")
        assert len(m.top_bar_text) == TOP_BAR_TEXT_MAX_LENGTH

    def test_top_bar_text_too_long(self):
        text = "あ" * (TOP_BAR_TEXT_MAX_LENGTH + 1)
        with pytest.raises(ValidationError, match="topBarText too long"):
            Meta(companyName="テスト", topBarText=text, companyIntro="紹介")

    def test_top_bar_text_excludes_accent_tags(self):
        """accent tags should not count toward the length limit."""
        inner = "あ" * TOP_BAR_TEXT_MAX_LENGTH
        text_with_tags = f"{{accent}}{inner}{{/accent}}"
        m = Meta(companyName="テスト", topBarText=text_with_tags, companyIntro="紹介")
        assert m.top_bar_text == text_with_tags

    def test_top_bar_text_over_limit_with_tags(self):
        """Even with tags, the visible text must be within limits."""
        inner = "あ" * (TOP_BAR_TEXT_MAX_LENGTH + 1)
        text_with_tags = f"{{accent}}{inner}{{/accent}}"
        with pytest.raises(ValidationError, match="topBarText too long"):
            Meta(companyName="テスト", topBarText=text_with_tags, companyIntro="紹介")
