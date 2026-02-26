import json
import struct
import wave
from pathlib import Path

import pytest

from video_generator_schema import InputBundle


class TestInputBundle:
    def test_load_valid(self, tmp_input_dir: Path):
        bundle = InputBundle.load(tmp_input_dir)
        assert bundle.meta.company_name == "テスト株式会社"
        assert len(bundle.reviews) == 1
        review = bundle.reviews[0]
        assert review.gender.value == "男性"
        assert review.occupation == "営業"
        assert len(review.paragraphs) == 1
        para = review.paragraphs[0]
        assert para.duration_frames > 0
        assert len(para.audio_pairs) == 1

    def test_missing_meta(self, tmp_path: Path):
        (tmp_path / "reviews.json").write_text("[]")
        with pytest.raises(FileNotFoundError, match="meta.json"):
            InputBundle.load(tmp_path)

    def test_missing_reviews(self, tmp_path: Path):
        (tmp_path / "meta.json").write_text(
            json.dumps(
                {
                    "companyName": "X",
                    "topBarText": "Y",
                    "companyIntro": "Z",
                }
            )
        )
        with pytest.raises(FileNotFoundError, match="reviews.json"):
            InputBundle.load(tmp_path)

    def test_missing_wav(self, tmp_input_dir: Path):
        # Remove the wav file
        (tmp_input_dir / "audio" / "r0_p0_s0.wav").unlink()
        with pytest.raises(FileNotFoundError, match="Missing audio file"):
            InputBundle.load(tmp_input_dir)

    def test_missing_mouth_json(self, tmp_input_dir: Path):
        (tmp_input_dir / "audio" / "r0_p0_s0.json").unlink()
        with pytest.raises(FileNotFoundError, match="Missing mouth data file"):
            InputBundle.load(tmp_input_dir)

    def test_mouth_text_mismatch(self, tmp_input_dir: Path):
        # Overwrite mouth json with different text
        mouth = {
            "text": "別のテキスト。",
            "shapes": [
                {"shape": "a", "start": 0.0, "end": 0.5},
                {"shape": "closed", "start": 0.5, "end": 1.0},
            ],
        }
        (tmp_input_dir / "audio" / "r0_p0_s0.json").write_text(
            json.dumps(mouth, ensure_ascii=False), encoding="utf-8"
        )
        with pytest.raises(ValueError, match="does not match sentence"):
            InputBundle.load(tmp_input_dir)

    def test_wav_wrong_sample_rate(self, tmp_input_dir: Path):
        # Overwrite wav with 44100Hz
        wav_path = tmp_input_dir / "audio" / "r0_p0_s0.wav"
        n_frames = 44100  # 1 second at 44100Hz
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(struct.pack(f"<{n_frames}h", *([0] * n_frames)))
        with pytest.raises(ValueError, match="24000Hz"):
            InputBundle.load(tmp_input_dir)

    def test_duration_mismatch(self, tmp_input_dir: Path):
        # Mouth data says 1.0s but wav is 2.0s
        wav_path = tmp_input_dir / "audio" / "r0_p0_s0.wav"
        n_frames = 48000  # 2 seconds at 24000Hz
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(struct.pack(f"<{n_frames}h", *([0] * n_frames)))
        with pytest.raises(ValueError, match="does not match WAV duration"):
            InputBundle.load(tmp_input_dir)
