import pytest
from pydantic import ValidationError

from video_generator_schema import Meta


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
