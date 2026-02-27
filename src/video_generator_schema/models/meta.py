import re

from pydantic import BaseModel, Field, model_validator

from ..constants import TOP_BAR_TEXT_MAX_LENGTH


class Meta(BaseModel):
    """Video metadata from meta.json."""

    company_name: str = Field(
        min_length=1,
        alias="companyName",
        description="Company name for thumbnail. Use \\n for line breaks",
    )
    top_bar_text: str = Field(
        min_length=1,
        alias="topBarText",
        description="Top bar text. Use {accent}...{/accent} for red highlighting",
    )
    company_intro: str = Field(
        min_length=1,
        alias="companyIntro",
        description="Company intro text. Use \\n for line breaks",
    )

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def top_bar_text_length(self) -> "Meta":
        """topBarText must be within max length ({accent} tags excluded)."""
        stripped = re.sub(r"\{/?accent\}", "", self.top_bar_text)
        length = len(stripped)
        if length > TOP_BAR_TEXT_MAX_LENGTH:
            raise ValueError(
                f"topBarText too long: {length} chars "
                f"(max {TOP_BAR_TEXT_MAX_LENGTH}, excluding {{accent}} tags). "
                f"text={stripped!r}"
            )
        return self
