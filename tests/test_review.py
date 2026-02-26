import pytest
from pydantic import ValidationError

from video_generator_schema import Paragraph, Review


class TestParagraph:
    def test_valid(self):
        p = Paragraph(
            text="テスト文です。",
            expression="normal",
            sentences=["テスト文です。"],
        )
        assert p.text == "テスト文です。"
        assert p.expression.value == "normal"

    def test_text_with_newline(self):
        p = Paragraph(
            text="一行目\n二行目",
            expression="normal",
            sentences=["一行目", "二行目"],
        )
        assert len(p.sentences) == 2

    def test_sentences_mismatch(self):
        with pytest.raises(ValidationError, match="does not match text"):
            Paragraph(
                text="テスト文です。",
                expression="normal",
                sentences=["別のテキスト。"],
            )

    def test_invalid_expression(self):
        with pytest.raises(ValidationError):
            Paragraph(
                text="テスト",
                expression="angry",
                sentences=["テスト"],
            )

    def test_default_expression(self):
        p = Paragraph(text="テスト", sentences=["テスト"])
        assert p.expression.value == "normal"


class TestReview:
    def test_valid(self):
        r = Review(
            gender="男性",
            occupation="営業",
            paragraphs=[
                {
                    "text": "テスト文です。",
                    "expression": "normal",
                    "sentences": ["テスト文です。"],
                }
            ],
        )
        assert r.gender.value == "男性"
        assert r.occupation == "営業"

    def test_invalid_gender(self):
        with pytest.raises(ValidationError):
            Review(
                gender="その他",
                occupation="営業",
                paragraphs=[
                    {
                        "text": "テスト",
                        "expression": "normal",
                        "sentences": ["テスト"],
                    }
                ],
            )

    def test_empty_paragraphs(self):
        with pytest.raises(ValidationError):
            Review(gender="男性", occupation="営業", paragraphs=[])
