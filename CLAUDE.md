# CLAUDE.md

## 作業ルール

- ファイルを編集したら、ユーザに同意を求めずに適宜 `git push` すること
- CLAUDE.md にディレクトリ構成を書かない

## プロジェクト概要

video-generator パイプラインの入力データを定義・バリデーションする Pydantic v2 パッケージ。`video-content-creator`（データ生成側）と `video-generator`（動画生成側）の間のデータ契約として機能する。

## 技術スタック

- Python 3.11+
- Pydantic 2.0+
- ビルド: hatchling
- テスト: pytest
- リント: ruff
- 型チェック: mypy（strict）

## セットアップ

```bash
pip install -e ".[dev]"
```

## 開発コマンド

| コマンド | 内容 |
|---|---|
| `pytest tests/ -v` | テスト実行 |
| `ruff check src/ tests/` | リント |
| `mypy src/` | 型チェック |

## 公開 API

### 定数（`constants.py`）

| 定数 | 値 | 説明 |
|------|-----|------|
| `VIDEO_FPS` | 30 | フレームレート |
| `WAV_SAMPLE_RATE` | 24000 | WAV サンプルレート |
| `WAV_CHANNELS` | 1 | モノラル |
| `MAX_REVIEWS` | 20 | 1動画あたり最大口コミ数 |
| `MIN_REVIEWS` | 1 | 最小口コミ数 |
| `PARAGRAPH_TEXT_MIN_LENGTH` | 1 | 段落テキスト最小文字数（改行除外） |
| `PARAGRAPH_TEXT_MAX_LENGTH` | 200 | 段落テキスト最大文字数（改行除外） |
| `MIN_PARAGRAPHS` | 2 | 1口コミあたり最小段落数 |
| `MAX_PARAGRAPHS` | 6 | 1口コミあたり最大段落数 |
| `TOP_BAR_TEXT_MAX_LENGTH` | 20 | topBarText 最大文字数（{accent}タグ除外） |
| `SHAPE_TIME_TOLERANCE` | 1e-4 | タイムライン検証の許容誤差 |

### Enum（`enums.py`）

| Enum | 値 | 用途 |
|------|-----|------|
| `MouthShape` | a, i, u, e, o, closed | VOICEVOX 音素 → 口形状マッピング |
| `Expression` | normal, surprised, troubled | ずんだもんの表情プリセット |
| `Gender` | 男性, 女性 | 口コミ投稿者の性別 |

### モデル

- **`Meta`** — `meta.json` の構造。`companyName`, `thumbnailCompanyName`, `topBarText`（{accent}タグ対応）, `companyIntro`
- **`Paragraph`** — 段落。`text`（改行は`\n`）, `expression`, `sentences`（音声生成用の文リスト）。sentences 結合がテキストと一致することをバリデーション
- **`Review`** — 口コミ。`gender`, `occupation`, `paragraphs`（2〜6段落）
- **`MouthTimingShape`** — 口パクタイムライン1要素。`shape`, `start`, `end`
- **`MouthData`** — `audio/*.json` の構造。`text`, `shapes`（連続タイムライン、0.0開始）

### InputBundle（一括バリデーション）

```python
bundle = InputBundle.load("input/")
```

`input/` ディレクトリ全体を読み込み、以下を検証:
- `meta.json` → Meta バリデーション
- `reviews.json` → Review バリデーション（1〜20件）
- 各文の `audio/r{R}_p{P}_s{S}.wav` + `.json` の存在・整合性
- WAV: 24kHz mono、mouth.json: テキスト一致、end値がWAV実長と一致（0.05秒許容差）
- 段落の duration_frames を自動算出（音声合計 + 0.5秒バッファ）

返り値の `ValidatedReview` / `ValidatedParagraph` は `audio_pairs` と `duration_frames` を持つ。

## 設計方針

- **生モデルとバリデーション済みモデルの分離**: `Review`/`Paragraph`はスキーマのみ、`ValidatedReview`/`ValidatedParagraph` は音声解決済み+duration算出済み
- **JSON エイリアス**: `populate_by_name=True` で camelCase（`companyName`）と snake_case（`company_name`）の両方に対応
- **音声ファイル命名**: `r{R}_p{P}_s{S}`（R=口コミ, P=段落, S=文、全て0始まり）
