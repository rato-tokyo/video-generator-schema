import re

from pydantic import BaseModel, Field, model_validator

from ..constants import (
    MAX_PARAGRAPHS,
    MIN_PARAGRAPHS,
    PARAGRAPH_TEXT_MAX_LENGTH,
    PARAGRAPH_TEXT_MIN_LENGTH,
)
from ..enums import Expression, Gender


class Paragraph(BaseModel):
    """A single paragraph in a review."""

    text: str = Field(
        min_length=1,
        description="Display text. Use \\n for line breaks within the paragraph",
    )
    expression: Expression = Field(
        default=Expression.NORMAL,
        description="Zundamon's facial expression during this paragraph",
    )
    sentences: list[str] = Field(
        min_length=1,
        description="Sentences for audio generation. Each gets one wav+json pair",
    )

    @model_validator(mode="after")
    def sentences_match_text(self) -> "Paragraph":
        """sentences joined must equal text with newlines removed."""
        text_normalized = self.text.replace("\n", "")
        sentences_joined = "".join(self.sentences)
        if text_normalized != sentences_joined:
            raise ValueError(
                f"sentences concatenated does not match text (newlines removed).\n"
                f"  text (normalized): {text_normalized!r}\n"
                f"  sentences joined:  {sentences_joined!r}"
            )
        return self

    @model_validator(mode="after")
    def text_length_in_range(self) -> "Paragraph":
        """Paragraph text length (excluding newlines) must be within limits."""
        length = len(self.text.replace("\n", ""))
        if length < PARAGRAPH_TEXT_MIN_LENGTH:
            raise ValueError(
                f"Paragraph text too short: {length} chars "
                f"(min {PARAGRAPH_TEXT_MIN_LENGTH}). text={self.text!r}"
            )
        if length > PARAGRAPH_TEXT_MAX_LENGTH:
            raise ValueError(
                f"Paragraph text too long: {length} chars "
                f"(max {PARAGRAPH_TEXT_MAX_LENGTH}). text={self.text!r}"
            )
        return self


class Review(BaseModel):
    """A single employee review."""

    gender: Gender
    occupation: str = Field(min_length=1, description="Job title")
    paragraphs: list[Paragraph] = Field(
        min_length=MIN_PARAGRAPHS,
        max_length=MAX_PARAGRAPHS,
    )
