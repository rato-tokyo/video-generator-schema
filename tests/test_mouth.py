import pytest
from pydantic import ValidationError

from video_generator_schema import MouthData, MouthTimingShape


class TestMouthTimingShape:
    def test_valid(self):
        s = MouthTimingShape(shape="a", start=0.0, end=0.5)
        assert s.shape.value == "a"
        assert s.start == 0.0
        assert s.end == 0.5

    def test_invalid_shape(self):
        with pytest.raises(ValidationError):
            MouthTimingShape(shape="x", start=0.0, end=0.5)

    def test_start_not_before_end(self):
        with pytest.raises(ValidationError, match="must be strictly less than"):
            MouthTimingShape(shape="a", start=0.5, end=0.5)

    def test_negative_start(self):
        with pytest.raises(ValidationError):
            MouthTimingShape(shape="a", start=-0.1, end=0.5)


class TestMouthData:
    def test_valid(self):
        md = MouthData(
            text="hello",
            shapes=[
                {"shape": "a", "start": 0.0, "end": 0.3},
                {"shape": "closed", "start": 0.3, "end": 0.5},
            ],
        )
        assert md.duration_seconds == 0.5
        assert len(md.shapes) == 2

    def test_first_shape_not_zero(self):
        with pytest.raises(ValidationError, match="start at 0.0"):
            MouthData(
                text="hello",
                shapes=[{"shape": "a", "start": 0.1, "end": 0.5}],
            )

    def test_gap_between_shapes(self):
        with pytest.raises(ValidationError, match="Gap"):
            MouthData(
                text="hello",
                shapes=[
                    {"shape": "a", "start": 0.0, "end": 0.3},
                    {"shape": "closed", "start": 0.4, "end": 0.5},
                ],
            )

    def test_empty_shapes(self):
        with pytest.raises(ValidationError):
            MouthData(text="hello", shapes=[])

    def test_empty_text(self):
        with pytest.raises(ValidationError):
            MouthData(
                text="",
                shapes=[{"shape": "a", "start": 0.0, "end": 0.5}],
            )
