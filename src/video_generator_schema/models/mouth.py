from pydantic import BaseModel, Field, model_validator

from ..constants import SHAPE_TIME_TOLERANCE
from ..enums import MouthShape


class MouthTimingShape(BaseModel):
    """A single mouth shape with its time span in seconds."""

    shape: MouthShape
    start: float = Field(ge=0.0, description="Start time in seconds")
    end: float = Field(gt=0.0, description="End time in seconds")

    @model_validator(mode="after")
    def start_before_end(self) -> "MouthTimingShape":
        if self.start >= self.end:
            raise ValueError(
                f"start ({self.start}) must be strictly less than end ({self.end})"
            )
        return self


class MouthData(BaseModel):
    """Mouth timing data for a single sentence (one .json file in audio/)."""

    text: str = Field(min_length=1, description="The spoken text for this audio")
    shapes: list[MouthTimingShape] = Field(
        min_length=1,
        description="Time-ordered mouth shapes covering the entire audio duration",
    )

    @model_validator(mode="after")
    def validate_shapes_timeline(self) -> "MouthData":
        shapes = self.shapes
        # First shape must start at 0.0
        if abs(shapes[0].start) > SHAPE_TIME_TOLERANCE:
            raise ValueError(
                f"First shape must start at 0.0, got {shapes[0].start}"
            )
        # Shapes must be continuous (no gaps) and time-ordered
        for i in range(1, len(shapes)):
            prev_end = shapes[i - 1].end
            curr_start = shapes[i].start
            if abs(prev_end - curr_start) > SHAPE_TIME_TOLERANCE:
                raise ValueError(
                    f"Gap between shape[{i - 1}].end ({prev_end}) and "
                    f"shape[{i}].start ({curr_start})"
                )
            if shapes[i].start < shapes[i - 1].start:
                raise ValueError(
                    f"Shapes not time-ordered at index {i}: "
                    f"{shapes[i].start} < {shapes[i - 1].start}"
                )
        return self

    @property
    def duration_seconds(self) -> float:
        """Total duration derived from the last shape's end time."""
        return self.shapes[-1].end
