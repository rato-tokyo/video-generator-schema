import pytest
from pydantic import ValidationError

from video_generator_schema import (
    MAX_PARAGRAPHS,
    MIN_PARAGRAPHS,
    PARAGRAPH_TEXT_MAX_LENGTH,
    PARAGRAPH_TEXT_MIN_LENGTH,
    Paragraph,
    Review,
)


# Helper: generate text of exact length
def _text(n: int) -> str:
    """n文字のダミーテキストを生成（末尾「。」付き）"""
    return "あ" * (n - 1) + "。"


class TestParagraph:
    def test_valid(self):
        text = _text(80)
        p = Paragraph(
            text=text,
            expression="normal",
            sentences=[text],
        )
        assert p.text == text
        assert p.expression.value == "normal"

    def test_text_with_newline(self):
        part1 = "あ" * 30
        part2 = "い" * 30 + "。"
        p = Paragraph(
            text=f"{part1}\n{part2}",
            expression="normal",
            sentences=[part1, part2],
        )
        assert len(p.sentences) == 2

    def test_sentences_mismatch(self):
        text = _text(50)
        with pytest.raises(ValidationError, match="does not match text"):
            Paragraph(
                text=text,
                expression="normal",
                sentences=["別のテキスト。" + "あ" * 40],
            )

    def test_invalid_expression(self):
        text = _text(50)
        with pytest.raises(ValidationError):
            Paragraph(
                text=text,
                expression="angry",
                sentences=[text],
            )

    def test_default_expression(self):
        text = _text(50)
        p = Paragraph(text=text, sentences=[text])
        assert p.expression.value == "normal"

    def test_text_empty_rejected(self):
        with pytest.raises(ValidationError):
            Paragraph(text="", sentences=[""])

    def test_text_too_long(self):
        text = _text(PARAGRAPH_TEXT_MAX_LENGTH + 1)
        with pytest.raises(ValidationError, match="too long"):
            Paragraph(text=text, sentences=[text])

    def test_text_at_min_boundary(self):
        text = _text(PARAGRAPH_TEXT_MIN_LENGTH)
        p = Paragraph(text=text, sentences=[text])
        assert len(p.text.replace("\n", "")) == PARAGRAPH_TEXT_MIN_LENGTH

    def test_text_at_max_boundary(self):
        text = _text(PARAGRAPH_TEXT_MAX_LENGTH)
        p = Paragraph(text=text, sentences=[text])
        assert len(p.text.replace("\n", "")) == PARAGRAPH_TEXT_MAX_LENGTH

    def test_text_length_excludes_newlines(self):
        """Newlines should not count toward text length."""
        base = _text(PARAGRAPH_TEXT_MIN_LENGTH)
        text_with_newlines = base[:20] + "\n" + base[20:]
        sentences = [base[:20], base[20:]]
        p = Paragraph(text=text_with_newlines, sentences=sentences)
        assert "\n" in p.text


class TestReview:
    def _paragraph(self, text: str | None = None) -> dict:
        t = text or _text(80)
        return {
            "text": t,
            "expression": "normal",
            "sentences": [t],
        }

    def test_valid(self):
        r = Review(
            gender="男性",
            occupation="営業",
            paragraphs=[self._paragraph() for _ in range(2)],
        )
        assert r.gender.value == "男性"
        assert r.occupation == "営業"
        assert len(r.paragraphs) == 2

    def test_three_paragraphs(self):
        r = Review(
            gender="女性",
            occupation="エンジニア",
            paragraphs=[self._paragraph() for _ in range(3)],
        )
        assert len(r.paragraphs) == 3

    def test_four_paragraphs(self):
        r = Review(
            gender="男性",
            occupation="営業",
            paragraphs=[self._paragraph() for _ in range(4)],
        )
        assert len(r.paragraphs) == 4

    def test_six_paragraphs(self):
        r = Review(
            gender="女性",
            occupation="エンジニア",
            paragraphs=[self._paragraph() for _ in range(6)],
        )
        assert len(r.paragraphs) == 6

    def test_invalid_gender(self):
        with pytest.raises(ValidationError):
            Review(
                gender="その他",
                occupation="営業",
                paragraphs=[self._paragraph() for _ in range(2)],
            )

    def test_too_few_paragraphs(self):
        with pytest.raises(ValidationError):
            Review(
                gender="男性",
                occupation="営業",
                paragraphs=[self._paragraph()],
            )

    def test_too_many_paragraphs(self):
        with pytest.raises(ValidationError):
            Review(
                gender="男性",
                occupation="営業",
                paragraphs=[self._paragraph() for _ in range(MAX_PARAGRAPHS + 1)],
            )

    def test_empty_paragraphs(self):
        with pytest.raises(ValidationError):
            Review(gender="男性", occupation="営業", paragraphs=[])
