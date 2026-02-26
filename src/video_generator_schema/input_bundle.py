import json
import math
import wave
from pathlib import Path

from pydantic import BaseModel, Field

from .constants import (
    MAX_REVIEWS,
    MIN_REVIEWS,
    VIDEO_FPS,
    WAV_CHANNELS,
    WAV_SAMPLE_RATE,
)
from .enums import Expression, Gender
from .models.meta import Meta
from .models.mouth import MouthData
from .models.review import Paragraph, Review


class AudioPair(BaseModel):
    """A validated wav + mouth-data pair for one sentence."""

    wav_path: Path
    mouth_data: MouthData

    model_config = {"arbitrary_types_allowed": True}


class ValidatedParagraph(BaseModel):
    """A paragraph with its resolved audio pairs and computed duration."""

    text: str
    expression: Expression
    sentences: list[str]
    audio_pairs: list[AudioPair]
    duration_frames: int = Field(
        description="Computed duration in frames (sum of audio + buffer)"
    )

    model_config = {"arbitrary_types_allowed": True}


class ValidatedReview(BaseModel):
    """A review with fully resolved audio data."""

    gender: Gender
    occupation: str
    paragraphs: list[ValidatedParagraph]

    model_config = {"arbitrary_types_allowed": True}


class InputBundle(BaseModel):
    """
    The complete validated input for video-generator.

    Use ``InputBundle.load(path)`` to load and validate an entire input/ directory.
    """

    meta: Meta
    reviews: list[ValidatedReview] = Field(
        min_length=MIN_REVIEWS,
        max_length=MAX_REVIEWS,
    )
    input_dir: Path

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def load(cls, input_dir: str | Path) -> "InputBundle":
        """Load and validate an entire input/ directory.

        Validates:
        - meta.json exists and is valid
        - reviews.json exists, is valid, and has 1-20 items
        - For every sentence, the corresponding wav + json pair exists
        - Each wav is 24kHz mono WAV
        - Each json passes MouthData validation
        - Each json text matches its corresponding sentence
        - Last shape.end matches WAV duration (within tolerance)
        """
        input_dir = Path(input_dir)
        audio_dir = input_dir / "audio"

        # --- meta.json ---
        meta_path = input_dir / "meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"meta.json not found in {input_dir}")
        meta = Meta.model_validate_json(meta_path.read_text(encoding="utf-8"))

        # --- reviews.json ---
        reviews_path = input_dir / "reviews.json"
        if not reviews_path.exists():
            raise FileNotFoundError(f"reviews.json not found in {input_dir}")
        raw_list = json.loads(reviews_path.read_text(encoding="utf-8"))
        if not isinstance(raw_list, list):
            raise ValueError("reviews.json must be a JSON array")

        reviews_parsed: list[Review] = [
            Review.model_validate(r) for r in raw_list
        ]

        if not (MIN_REVIEWS <= len(reviews_parsed) <= MAX_REVIEWS):
            raise ValueError(
                f"reviews count must be {MIN_REVIEWS}-{MAX_REVIEWS}, "
                f"got {len(reviews_parsed)}"
            )

        # --- Validate audio files and build ValidatedReviews ---
        validated_reviews: list[ValidatedReview] = []
        for ri, review in enumerate(reviews_parsed):
            validated_paragraphs: list[ValidatedParagraph] = []
            for pi, paragraph in enumerate(review.paragraphs):
                audio_pairs: list[AudioPair] = []
                for si, sentence in enumerate(paragraph.sentences):
                    stem = f"r{ri}_p{pi}_s{si}"
                    wav_path = audio_dir / f"{stem}.wav"
                    json_path = audio_dir / f"{stem}.json"

                    if not wav_path.exists():
                        raise FileNotFoundError(f"Missing audio file: {wav_path}")
                    if not json_path.exists():
                        raise FileNotFoundError(
                            f"Missing mouth data file: {json_path}"
                        )

                    # Validate WAV format
                    wav_duration = _validate_wav(wav_path)

                    # Parse and validate mouth data
                    mouth_data = MouthData.model_validate_json(
                        json_path.read_text(encoding="utf-8")
                    )

                    # Cross-validate: mouth text must match sentence
                    if mouth_data.text != sentence:
                        raise ValueError(
                            f"{stem}: mouth data text does not match sentence.\n"
                            f"  mouth: {mouth_data.text!r}\n"
                            f"  sentence: {sentence!r}"
                        )

                    # Cross-validate: last shape.end ≈ WAV duration
                    shape_end = mouth_data.duration_seconds
                    if abs(shape_end - wav_duration) > 0.05:
                        raise ValueError(
                            f"{stem}: last shape.end ({shape_end:.4f}s) does not "
                            f"match WAV duration ({wav_duration:.4f}s)"
                        )

                    audio_pairs.append(
                        AudioPair(wav_path=wav_path, mouth_data=mouth_data)
                    )

                # Compute duration: sum of audio durations + 0.5s buffer
                buffer_sec = 0.5
                total_audio_sec = sum(
                    ap.mouth_data.duration_seconds for ap in audio_pairs
                )
                duration_frames = math.ceil(
                    (total_audio_sec + buffer_sec) * VIDEO_FPS
                )

                validated_paragraphs.append(
                    ValidatedParagraph(
                        text=paragraph.text,
                        expression=paragraph.expression,
                        sentences=paragraph.sentences,
                        audio_pairs=audio_pairs,
                        duration_frames=duration_frames,
                    )
                )

            validated_reviews.append(
                ValidatedReview(
                    gender=review.gender,
                    occupation=review.occupation,
                    paragraphs=validated_paragraphs,
                )
            )

        return cls(
            meta=meta,
            reviews=validated_reviews,
            input_dir=input_dir,
        )


def _validate_wav(wav_path: Path) -> float:
    """Validate WAV file format and return duration in seconds."""
    with wave.open(str(wav_path), "rb") as wf:
        rate = wf.getframerate()
        channels = wf.getnchannels()
        n_frames = wf.getnframes()

        if rate != WAV_SAMPLE_RATE:
            raise ValueError(
                f"{wav_path.name}: expected {WAV_SAMPLE_RATE}Hz, got {rate}Hz"
            )
        if channels != WAV_CHANNELS:
            raise ValueError(
                f"{wav_path.name}: expected mono, got {channels} channels"
            )

        return n_frames / rate
