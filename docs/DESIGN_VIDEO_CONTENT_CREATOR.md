# video-content-creator 設計書

## 概要

`data-to-prompt`（口コミ選定・リライト）と `voicevox`（音声・口パク生成）を統合し、video-generator 向けの input/ フォルダを一気通貫で生成するプロジェクト。

## 統合元リポジトリ

| リポジトリ | 役割 | 移行するコア |
|-----------|------|-------------|
| `git/data-to-prompt` | 口コミ選定+リライト | `scripts/`, `scripts/lib/`, `scripts/prompts/` |
| `git/voicevox` | 音声+mouth.json生成 | `generate.py`, `post_process.py`, `config/` |

## フォルダ構成

```
video-content-creator/
├── pyproject.toml
├── CLAUDE.md
├── companies.json                    ← data-to-prompt から移行
│
├── src/
│   ├── review_builder/               ← 旧 data-to-prompt
│   │   ├── __init__.py
│   │   ├── config.py                 ← パス定数等
│   │   ├── io_utils.py               ← JSON I/O, テキスト前処理
│   │   ├── companies.py              ← companies.json アクセス
│   │   ├── progress.py               ← パイプライン進捗管理
│   │   ├── claude_runner.py          ← Claude CLI ラッパー
│   │   └── prompts/
│   │       ├── step2_system.txt      ← 口コミ選定プロンプト
│   │       └── step3_system.txt      ← リライトプロンプト（※要改修）
│   │
│   ├── audio_generator/              ← 旧 voicevox
│   │   ├── __init__.py
│   │   ├── generate.py               ← VOICEVOX音声+mouth.json生成
│   │   └── post_process.py           ← EQ+コンプレッサー
│   │
│   └── pipeline.py                   ← 統合パイプライン（新規）
│
├── config/                           ← 旧 voicevox/config/
│   ├── voice_config.json
│   └── post_process_config.json
│
├── output/                           ← 中間出力（gitignore）
│   └── {企業名}/
│       ├── meta.json                 ← Step 1
│       ├── review_NNN.json           ← Step 1
│       ├── picked.json               ← Step 2
│       ├── final.json                ← Step 3
│       ├── reviews.json              ← Step 4（新規: スキーマ準拠）
│       ├── video_meta.json           ← Step 4（新規: スキーマ準拠）
│       └── audio/                    ← Step 5（新規）
│           ├── r0_p0_s0.wav
│           ├── r0_p0_s0.json
│           └── ...
│
└── input/                            ← 最終出力（video-generator に渡す）
    ├── meta.json
    ├── reviews.json
    └── audio/
        └── ...
```

## パイプライン（5ステップ）

```
Step 1: 口コミ分割       [既存] prepare_reviews.py の処理
  ↓
Step 2: 口コミ選定       [既存] Claude で動画向き口コミを選定
  ↓
Step 3: リライト         [改修必要] Claude でリライト → final.json
  ↓
Step 4: スキーマ変換     [新規] final.json → reviews.json + meta.json
  ↓
Step 5: 音声生成         [改修必要] reviews.json → wav + mouth.json
  ↓
完了: input/ に配置      [新規] output/{企業名}/ → input/ にコピー
```

## 各ステップの詳細

### Step 1〜2: 変更なし

data-to-prompt の既存ロジックをそのまま移行。

### Step 3: リライト（改修必要）

**現状**: final.json の出力形式が独自（highlight + reviews）。

**改修方針**: step3_system.txt のプロンプトを修正し、video-generator-schema に準拠した形式で出力させる。

具体的に追加すべき出力要件:
- 各口コミに `paragraphs` 配列を持たせる（現状は `comment` が1つの文字列）
- 各段落に `expression` を指定させる
- 各段落に `sentences` を指定させる（句読点区切り）
- `topBarText`（キャッチコピー）を生成させる
- `companyIntro` を生成させる

**つまり Step 3 の出力を直接 reviews.json + meta.json に近い形にすることで、Step 4 の変換を最小化する。**

### Step 4: スキーマ変換（新規）

Step 3 の Claude 出力を video-generator-schema でバリデーションし、正式な reviews.json + meta.json として保存する。

```python
from video_generator_schema import Review, Meta, Paragraph

# Claude出力をパースしてPydanticモデルに変換
reviews = [Review.model_validate(r) for r in claude_output["reviews"]]
meta = Meta.model_validate(claude_output["meta"])

# バリデーション通過 → ファイル出力
```

### Step 5: 音声生成（改修必要）

**現状**: `generate.py` はテキストファイルを行単位で読み、`output/NNN/` に出力。

**改修内容**:
- 入力を reviews.json に変更（sentences を抽出してループ）
- 出力ファイル名を `r{R}_p{P}_s{S}.wav` / `.json` に変更
- video-generator-schema の MouthData でバリデーション

```python
from video_generator_schema import Review, MouthData
import json

reviews = [Review.model_validate(r) for r in json.load(open("reviews.json"))]

for ri, review in enumerate(reviews):
    for pi, para in enumerate(review.paragraphs):
        for si, sentence in enumerate(para.sentences):
            stem = f"r{ri}_p{pi}_s{si}"
            # VOICEVOX API → wav + mouth shapes
            # MouthData でバリデーション
            # audio/{stem}.wav, audio/{stem}.json に保存
```

### 最終: input/ に配置

output/{企業名}/ から必要なファイルを input/ にコピーし、InputBundle.load() で最終バリデーション。

```python
from video_generator_schema import InputBundle

bundle = InputBundle.load("input/")
print(f"OK: {len(bundle.reviews)} reviews, all audio validated")
```

## 依存パッケージ

```toml
[project]
dependencies = [
    "video-generator-schema @ git+https://github.com/rato-tokyo/video-generator-schema.git",
    "requests",        # VOICEVOX API
    "numpy",           # 音声処理
    "scipy",           # 音声処理
    "soundfile",       # WAV I/O
]
```

外部依存:
- ffmpeg（音声後処理）
- VOICEVOX Engine（localhost:50021 で事前起動）
- Claude CLI（`claude` コマンド）

## 設定

### config/voice_config.json（既存のまま移行）

```json
{
  "speaker": 3,
  "speedScale": 1.2,
  "pitchScale": -0.08,
  "intonationScale": 1.25,
  "prePhonemeLength": 0.1,
  "postPhonemeLength": 0.1,
  "pauseLengthScale": 1.2,
  "outputSamplingRate": 24000,
  "outputStereo": false
}
```

### config/post_process_config.json（既存のまま移行）

EQ + コンプレッサー設定。変更不要。

## CLAUDE.md に書くべきこと

統合リポジトリの CLAUDE.md には以下を含めること:

1. プロジェクト概要（video-generator 向けデータ準備パイプライン）
2. 5ステップのパイプライン説明
3. video-generator-schema パッケージの使い方
4. VOICEVOX Engine の前提条件（localhost:50021）
5. ffmpeg の前提条件
6. `companies.json` の構造
7. スクレイパーデータのパス（`/Volumes/SyncData/openwork/`）
8. Claude CLI の使い方（subprocess 呼び出し、タイムアウト 600s）

## 移行チェックリスト

実装担当のClaudeへ:

- [ ] GitHub に `rato-tokyo/video-content-creator` リポジトリを作成
- [ ] pyproject.toml を作成（video-generator-schema を依存に含める）
- [ ] data-to-prompt から `scripts/lib/`, `scripts/prompts/`, `companies.json` を移行
- [ ] voicevox から `generate.py`, `post_process.py`, `config/` を移行
- [ ] Step 3 の system prompt を改修（スキーマ準拠の出力形式に）
- [ ] Step 4 のスキーマ変換ロジックを実装
- [ ] Step 5 の generate.py を改修（reviews.json 入力、r{R}_p{P}_s{S} 命名）
- [ ] 統合パイプライン（pipeline.py）を実装
- [ ] InputBundle.load() での最終バリデーションを組み込み
- [ ] CLAUDE.md を作成
- [ ] 既存の動作（Step 1〜3）が壊れていないことを確認
- [ ] 1社分のデータで全パイプラインを通しテスト
