# data-to-prompt 向け: 出力フォーマット仕様

## 概要

このドキュメントは、video-generator に渡す `meta.json` と `reviews.json` の**フォーマット仕様**を定義する。

data-to-prompt プロジェクトでは、スクレイピング済み口コミから Claude が動画向けの口コミ選定・リライトを行う。その最終出力を以下の形式に整形して保存すること。

**このガイドはデータの作り方（選定・リライトの方針）には関与しない。あくまで出力形式の仕様書である。**

## インストール

```bash
pip install git+https://github.com/rato-tokyo/video-generator-schema.git
```

## 出力ファイル

### 1. meta.json

動画1本分のメタ情報。

```python
from video_generator_schema import Meta

meta = Meta(
    company_name="リクルート",
    top_bar_text="部署によっては{accent}半分が性格悪い!?{/accent}",
    company_intro="リクルート株式会社\n・業種：人材サービス\n・事業内容：求人広告、人材紹介\n・従業員数：約2万人\n・特徴：ミッショングレード制\n・近況：売上好調\n・その他：フレキシブル休暇あり",
)

# JSON出力（camelCase）
meta.model_dump_json(indent=2, by_alias=True)
```

| フィールド | 説明 |
|-----------|------|
| `companyName` | 企業名。サムネイルに表示。`\n` で改行可 |
| `topBarText` | サムネイル上部テキスト。`{accent}...{/accent}` で囲んだ部分が赤色になる |
| `companyIntro` | 会社紹介ページに表示するテキスト。下記フォーマットに従う |

#### companyIntro のフォーマット

```
{企業正式名称}
・業種：{業種}
・事業内容：{事業内容}
・従業員数：{従業員数}
・特徴：{特徴}
・近況：{近況}
・その他：{その他}
```

### 2. reviews.json

口コミの配列。Claude が選定・リライトした結果をこの形式で格納する。

```python
import json
from video_generator_schema import Review, Paragraph, Expression, Gender

reviews = [
    Review(
        gender=Gender.MALE,
        occupation="営業",
        paragraphs=[
            Paragraph(
                text="契約社員として入社したんですが、ミッショングレード制で給料が決まります。\n世の中水準と比べて高くないですね。",
                expression=Expression.NORMAL,
                sentences=[
                    "契約社員として入社したんですが、ミッショングレード制で給料が決まります。",
                    "世の中水準と比べて高くないですね。",
                ],
            ),
        ],
    ),
]

# JSON出力
json.dumps(
    [r.model_dump() for r in reviews],
    indent=2,
    ensure_ascii=False,
)
```

## フォーマットルール

### sentences

音声合成（VOICEVOX）に渡す単位。1 sentence = 1つの音声ファイルになる。

- sentences を結合すると text（改行 `\n` を除去したもの）と**完全一致**すること
- これはスキーマのバリデーションで自動チェックされる
- 分割の粒度は、句読点（。）区切りが基本。1文が長すぎる場合は読点（、）で分割してもよい

### expression

各段落のずんだもんの表情:

| expression | 見た目 | 使い分け |
|-----------|--------|---------|
| `"normal"` | 通常の目・眉 | 一般的な説明、中立的な内容 |
| `"surprised"` | 見開いた目・上がった眉・軽い赤面 | 驚き、感心、意外な情報 |
| `"troubled"` | ジト目・困り眉 | 困り、心配、ネガティブな内容 |

### text 内の改行

画面表示上で改行したい位置に `\n` を入れる。
1行が長くなりすぎないよう、30〜40文字程度で改行を入れることを推奨。

### topBarText

`{accent}...{/accent}` で最も目を引く部分を囲む。

例:
- `"部署によっては{accent}半分が性格悪い!?{/accent}"`
- `"{accent}残業100時間{/accent}は当たり前の会社"`

## バリデーション

出力後、スキーマでバリデーション可能:

```python
import json
from video_generator_schema import Meta, Review

meta = Meta.model_validate_json(open("meta.json").read())
reviews = [Review.model_validate(r) for r in json.load(open("reviews.json"))]
```

エラーが出た場合はメッセージに従って修正すること。

## 制約

- 口コミは **最大20件**
- gender は `"男性"` または `"女性"` のみ
- expression は `"normal"`, `"surprised"`, `"troubled"` のみ
