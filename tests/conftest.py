import json
import struct
import wave
from pathlib import Path

import pytest

# 40文字以上の段落テキスト（PARAGRAPH_TEXT_MIN_LENGTH = 40）
_SENTENCE_1 = "テスト文です。"
_SENTENCE_2 = "これはテスト用の段落テキストで、十分な文字数を確保しているテストです。"
_SENTENCE_3 = "二番目の段落です。"
_SENTENCE_4 = "スキーマのバリデーションを通過するために必要な長さがある段落テキストです。"
_PARA_TEXT_1 = _SENTENCE_1 + _SENTENCE_2
_PARA_TEXT_2 = _SENTENCE_3 + _SENTENCE_4


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

    # reviews.json — 1 review, 2 paragraphs (MIN_PARAGRAPHS=2), 2 sentences each
    reviews = [
        {
            "gender": "男性",
            "occupation": "営業",
            "paragraphs": [
                {
                    "text": _PARA_TEXT_1,
                    "expression": "normal",
                    "sentences": [_SENTENCE_1, _SENTENCE_2],
                },
                {
                    "text": _PARA_TEXT_2,
                    "expression": "normal",
                    "sentences": [_SENTENCE_3, _SENTENCE_4],
                },
            ],
        }
    ]
    (tmp_path / "reviews.json").write_text(
        json.dumps(reviews, ensure_ascii=False), encoding="utf-8"
    )

    # Audio files for paragraph 0: r0_p0_s0.wav, r0_p0_s1.wav
    for name in ["r0_p0_s0", "r0_p0_s1", "r0_p1_s0", "r0_p1_s1"]:
        _write_silent_wav(audio_dir / f"{name}.wav", duration_sec=1.0)

    # Mouth data for each sentence
    _write_mouth_json(audio_dir / "r0_p0_s0.json", _SENTENCE_1)
    _write_mouth_json(audio_dir / "r0_p0_s1.json", _SENTENCE_2)
    _write_mouth_json(audio_dir / "r0_p1_s0.json", _SENTENCE_3)
    _write_mouth_json(audio_dir / "r0_p1_s1.json", _SENTENCE_4)

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


def _write_mouth_json(path: Path, text: str) -> None:
    """Write a valid mouth data JSON file."""
    mouth = {
        "text": text,
        "shapes": [
            {"shape": "a", "start": 0.0, "end": 0.5},
            {"shape": "closed", "start": 0.5, "end": 1.0},
        ],
    }
    path.write_text(json.dumps(mouth, ensure_ascii=False), encoding="utf-8")
