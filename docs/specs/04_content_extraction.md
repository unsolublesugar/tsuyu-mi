# 04. 本文取得・抽出仕様

## フォールバックチェーン

```
1. HTTP GET で HTML 取得
2. trafilatura で本文抽出
3. readability-lxml でフォールバック
4. タイトル / excerpt / URL / domain / tags で簡易要約入力を構成
5. すべて失敗 → スキップ
```

## HTTP 取得

- ライブラリ: httpx（同期クライアント）
- タイムアウト: `REQUEST_TIMEOUT_SECONDS`（デフォルト 20 秒）
- User-Agent: `USER_AGENT` 環境変数
- リダイレクト: 自動追跡
- 動画 URL は HTTP 取得前にスキップ判定

## 本文抽出

### trafilatura（優先）

```python
trafilatura.extract(html, include_comments=False, include_tables=True)
```

成功時: `extract_method = "trafilatura"`

### readability-lxml（フォールバック）

trafilatura が失敗、または結果が 100 文字未満の場合に使用。

```python
from readability import Document
doc = Document(html)
doc.summary()  # HTML → テキスト変換が必要
```

成功時: `extract_method = "readability"`

## 簡易要約用入力

本文が取れない場合、以下を AI に渡す。

- title
- excerpt
- URL
- domain
- tags
- 取得日時
- og:description（取得可能な場合）

`summary_input_type = "metadata"`

## 本文長ルール

| 文字数 | 扱い |
|---|---|
| 1500 文字以上 | 通常要約 |
| 500〜1499 文字 | 短文要約 |
| 500 文字未満 | 簡易要約寄り |
| 取得不能 | fallback or skip |

## 動画コンテンツの判定

### 判定方法

1. Raindrop API の `type == "video"` フィールド
2. ドメインベース判定:
   - `youtube.com`, `youtu.be`
   - `vimeo.com`
   - `nicovideo.jp`, `nico.ms`
   - `dailymotion.com`
   - `twitch.tv`

### 処理

- `content_type = "video"`
- `status = "skipped"`
- `reason = "unsupported_video"`
- HTML 出力では動画であることを表示

## og:description の取得

HTML 取得時に `<meta property="og:description">` を抽出し、簡易要約用入力に含める。
BeautifulSoup ではなく、正規表現または trafilatura の metadata 機能を使用。
