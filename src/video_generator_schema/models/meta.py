from pydantic import BaseModel, Field


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
