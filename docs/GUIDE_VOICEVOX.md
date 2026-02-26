# voicevox 向け: 音声・口パク生成ガイド

## あなたの役割

`reviews.json` の各 sentence に対して、VOICEVOX で音声（wav）と口パクデータ（mouth.json）を生成し、`audio/` フォルダに配置する。

## インストール

```bash
pip install git+https://github.com/rato-tokyo/video-generator-schema.git
```

## 前提条件

- VOICEVOX Engine がローカルで起動済み（`http://localhost:50021`）
- `reviews.json` が data-to-prompt で生成済み

## ワークフロー

```
reviews.json を読み込む
  ↓
全 sentence を抽出（reviewIndex, paragraphIndex, sentenceIndex を記録）
  ↓
各 sentence に対して:
  1. VOICEVOX API で音声合成 → wav ファイル
  2. VOICEVOX API で音素タイミング取得 → mouth.json に変換
  3. r{R}_p{P}_s{S}.wav / r{R}_p{P}_s{S}.json として保存
```

## ファイル命名規則

`r{R}_p{P}_s{S}` — 全て0始まりのインデックス

| 記号 | 意味 |
|------|------|
| R | 口コミのインデックス（reviews.json の配列順） |
| P | 段落のインデックス |
| S | 文のインデックス（sentences 配列順） |

例: 口コミ0, 段落2, 文1 → `r0_p2_s1.wav` + `r0_p2_s1.json`

## 出力先

```
audio/
├── r0_p0_s0.wav
├── r0_p0_s0.json
├── r0_p0_s1.wav
├── r0_p0_s1.json
├── r0_p1_s0.wav
├── r0_p1_s0.json
└── ...
```

## WAV ファイル仕様

| 項目 | 値 |
|------|------|
| フォーマット | WAV |
| サンプルレート | 24kHz |
| チャンネル | mono |
| ビット深度 | 16-bit |
| 話者 | ずんだもん |

VOICEVOX API のデフォルト出力は 24kHz mono なのでそのまま保存すればよい。

## mouth.json 仕様

```python
from video_generator_schema import MouthData, MouthTimingShape, MouthShape

mouth = MouthData(
    text="契約社員として入社したんですが、ミッショングレード制で給料が決まります。",
    shapes=[
        MouthTimingShape(shape=MouthShape.CLOSED, start=0.0, end=0.0833),
        MouthTimingShape(shape=MouthShape.E, start=0.0833, end=0.3626),
        MouthTimingShape(shape=MouthShape.A, start=0.3626, end=0.4957),
        # ...
    ],
)

# JSON出力
mouth.model_dump_json(indent=2)
```

### MouthData 構造

| フィールド | 型 | 説明 |
|-----------|------|------|
| `text` | string | 対応する sentence テキスト（完全一致必須） |
| `shapes` | MouthTimingShape[] | 口形状のタイムライン |

### MouthTimingShape 構造

| フィールド | 型 | 説明 |
|-----------|------|------|
| `shape` | `"a"` / `"i"` / `"u"` / `"e"` / `"o"` / `"closed"` | 口の形状 |
| `start` | float | 開始時刻（秒） |
| `end` | float | 終了時刻（秒） |

## VOICEVOX 音素 → MouthShape 変換ルール

VOICEVOX の `audio_query` で得られる音素データを以下のルールで変換する:

| 音素 | → shape | 理由 |
|------|---------|------|
| `a` | `"a"` | ア行母音 |
| `i` | `"i"` | イ行母音 |
| `u` | `"u"` | ウ行母音 |
| `e` | `"e"` | エ行母音 |
| `o` | `"o"` | オ行母音 |
| `N` | `"closed"` | 撥音（ん） |
| `cl` | `"closed"` | 促音（っ） |
| `pau` | `"closed"` | 無音（ポーズ） |
| `sil` | `"closed"` | 無音（文頭末） |
| 子音のみ（`k`, `s`, `t`, `n`, `h`, `m`, `y`, `r`, `w`, `g`, `z`, `d`, `b`, `p`, `f`, `j`, `ch`, `sh`, `ts`, `ky`, `ny`, `hy`, `ry`, `gy`, `by`, `py`, `my`, `v`） | 直後の母音の shape。直後に母音がなければ `"closed"` | 子音は次の母音の口形状に遷移中 |

### 変換の考え方

VOICEVOX の音素列は `[子音, 母音, 子音, 母音, ...]` のように並ぶ。
子音と直後の母音をセットにして、**母音の shape** を割り当てる。
子音単体の区間も同じ shape にマージして1つの MouthTimingShape にする。

例: 「か」= `k` + `a` → 両方 `"a"` → 1つの shape `{"shape": "a", "start": ..., "end": ...}` にマージ

## shapes の制約（バリデーション済み）

- 時間順にソートされていること
- 隙間なく連続（前の `end` = 次の `start`）
- 最初の `start` が `0.0`
- 最後の `end` が WAV の実際の長さ（秒）と一致

これらはスキーマの `MouthData` バリデーションで自動チェックされる。

## VOICEVOX API の使い方（参考）

```python
import requests

VOICEVOX_URL = "http://localhost:50021"
SPEAKER_ID = 3  # ずんだもん（ノーマル）

# 1. audio_query で音素タイミング取得
query = requests.post(
    f"{VOICEVOX_URL}/audio_query",
    params={"text": sentence, "speaker": SPEAKER_ID},
).json()

# query["accent_phrases"] に音素情報が含まれる
# ここから moras を取り出して MouthTimingShape に変換

# 2. synthesis で音声生成
wav_data = requests.post(
    f"{VOICEVOX_URL}/synthesis",
    params={"speaker": SPEAKER_ID},
    json=query,
).content

# wav_data を .wav ファイルとして保存
```

## バリデーション

全ファイル生成後、InputBundle で一括バリデーション可能:

```python
from video_generator_schema import InputBundle

# input/ に meta.json, reviews.json, audio/ が揃った状態で:
bundle = InputBundle.load("input/")
# エラーが出なければ全データが正しい
```

## reviews.json の読み込み例

```python
import json
from video_generator_schema import Review

with open("reviews.json", encoding="utf-8") as f:
    raw = json.load(f)

reviews = [Review.model_validate(r) for r in raw]

for ri, review in enumerate(reviews):
    for pi, para in enumerate(review.paragraphs):
        for si, sentence in enumerate(para.sentences):
            stem = f"r{ri}_p{pi}_s{si}"
            print(f"{stem}: {sentence}")
            # ここで VOICEVOX API を呼んで wav + json を生成
```
