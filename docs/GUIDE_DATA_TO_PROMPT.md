# data-to-prompt 向け: 出力仕様ガイド

## あなたの役割

スクレイピング済みの口コミデータを、video-generator が受け付ける `meta.json` と `reviews.json` に変換する。

## インストール

```bash
pip install git+https://github.com/rato-tokyo/video-generator-schema.git
```

## 出力ファイル

### 1. meta.json

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

## データ変換ルール

### sentences の分割

口コミテキストを **句読点（。）** で区切って sentences に分割する。
1文が長すぎる場合（目安40文字以上）は読点（、）で分割してもよい。

- sentences を結合すると text（改行 `\n` を除去したもの）と完全一致すること
- これはスキーマのバリデーションで自動チェックされる

### expression の選択

各段落の内容に応じて表情を指定する:

| expression | 使い分け |
|-----------|---------|
| `"normal"` | 一般的な説明、中立的な内容 |
| `"surprised"` | 驚き、感心、意外な情報、ポジティブな驚き |
| `"troubled"` | 困り、心配、ネガティブな内容、不満 |

### topBarText の作成

動画のキャッチコピー。口コミ内容から最もインパクトのある要素を抜き出して作成する。
`{accent}...{/accent}` で最も目を引く部分を囲む。

例:
- `"部署によっては{accent}半分が性格悪い!?{/accent}"`
- `"{accent}残業100時間{/accent}は当たり前の会社"`

### 段落の構成

1つの口コミに含まれる段落数は **1〜5段落** 程度が適切。
長い口コミは意味のまとまりで段落に分割する。

### text 内の改行

画面表示上で改行したい位置に `\n` を入れる。
1行が長くなりすぎないよう、30〜40文字程度で改行を入れることを推奨。

## バリデーション

出力後、スキーマでバリデーション可能:

```python
from video_generator_schema import Meta, Review

# ファイルから読み込んでバリデーション
meta = Meta.model_validate_json(open("meta.json").read())
reviews = [Review.model_validate(r) for r in json.load(open("reviews.json"))]
```

エラーが出た場合はメッセージに従って修正すること。

## 制約

- 口コミは **最大20件**
- gender は `"男性"` または `"女性"` のみ
- expression は `"normal"`, `"surprised"`, `"troubled"` のみ
