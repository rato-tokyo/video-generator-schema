import json
import struct
import wave
from pathlib import Path

import pytest


@pytest.fixture
def tmp_input_dir(tmp_path: Path) -> Path:
    """Create a valid input/ directory with meta.json, reviews.json, and audio files."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()

    # meta.json
    meta = {
        "companyName": "テスト株式会社",
        "topBarText": "{accent}テスト{/accent}の会社",
        "companyIntro": "テスト株式会社\n・業種：テスト",
    }
    (tmp_path / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )

    # reviews.json — 1 review, 1 paragraph, 1 sentence
    reviews = [
        {
            "gender": "男性",
            "occupation": "営業",
            "paragraphs": [
                {
                    "text": "テスト文です。",
                    "expression": "normal",
                    "sentences": ["テスト文です。"],
                }
            ],
        }
    ]
    (tmp_path / "reviews.json").write_text(
        json.dumps(reviews, ensure_ascii=False), encoding="utf-8"
    )

    # Audio: r0_p0_s0.wav (24kHz mono, ~1s silence)
    wav_path = audio_dir / "r0_p0_s0.wav"
    _write_silent_wav(wav_path, duration_sec=1.0)

    # Mouth data: r0_p0_s0.json
    mouth = {
        "text": "テスト文です。",
        "shapes": [
            {"shape": "a", "start": 0.0, "end": 0.5},
            {"shape": "closed", "start": 0.5, "end": 1.0},
        ],
    }
    (audio_dir / "r0_p0_s0.json").write_text(
        json.dumps(mouth, ensure_ascii=False), encoding="utf-8"
    )

    return tmp_path


def _write_silent_wav(
    path: Path, duration_sec: float = 1.0, rate: int = 24000
) -> None:
    """Write a silent mono 16-bit WAV file."""
    n_frames = int(rate * duration_sec)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{n_frames}h", *([0] * n_frames)))
