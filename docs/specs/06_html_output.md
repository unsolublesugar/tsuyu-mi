# 06. HTML 出力仕様

## 目的

一覧を見返しながら、読む / 保留 / 捨てる判断をしやすくすること。

## 出力先

`docs/index.html`（GitHub Pages 対応）

## テンプレートエンジン

Jinja2

## 記事カードの必須項目

- タイトル（元記事 URL へのリンク）
- ドメイン
- 追加日（created_at）
- 3 行要約
- 主題（topic）
- 優先度バッジ（high / medium / low）
- 優先度スコア（`合計/12` 表記。`title` 属性に 4 軸の内訳。`scores` がある記事のみ表示）
- 今読む理由（read_now_reason）
- 後回し理由（defer_reason）
- ドロップ候補かどうか
- 本文取得ステータス（content_status）
- 手動ステータス（manual_status）
- メモ欄（notes）

## ソート順

初期表示:
1. priority（high → medium → low）
2. created_at の新しい順

## フィルタ

- JS なしでも全記事が読める HTML にする
- `docs/app.js` で軽いクライアントサイド絞り込みを追加
  - 優先度フィルタ
  - ステータスフィルタ
  - キーワード検索

## スタイリング

`docs/styles.css`:
- 優先度ごとの色分け（high=赤系 / medium=黄系 / low=灰系）
- レスポンシブ対応
- カード形式レイアウト
- ドロップ候補は視覚的に薄く表示

## スキップ記事の表示

- 要約済み記事とは別セクションに表示
- スキップ理由を明示
- 動画は動画アイコンで区別

## 統計情報

HTML のヘッダーに以下を表示:
- 総記事数
- 要約済み件数
- スキップ件数
- 最終実行日時

## OGP / favicon

SNS・チャットのカードビューでリンクを共有した際にサムネイルを表示するため、`<head>` に以下を出力する。

### メタタグ

- `meta name="description"` / `link rel="canonical"`
- OGP: `og:type`(website) / `og:site_name` / `og:title` / `og:description` / `og:url` / `og:image` / `og:image:width`(1200) / `og:image:height`(630) / `og:image:alt` / `og:locale`(ja_JP)
- Twitter Card: `twitter:card`(summary_large_image) / `twitter:title` / `twitter:description` / `twitter:image`

`og:url` / `og:image` は絶対 URL が必須。基点となる公開サイト URL は `Config.site_url`（環境変数 `SITE_URL`、既定値 `https://unsolublesugar.github.io/tsuyu-mi/`）から取得し、`HtmlBuilder` が末尾スラッシュを正規化した上でテンプレートへ渡す。フォークして別ドメインに公開する場合は `SITE_URL` を上書きする。

タイトル・説明文は `src/html_builder.py` の `SITE_TITLE` / `SITE_DESCRIPTION` 定数で定義する。

### 静的アセット

`docs/` 配下に配置し、GitHub Pages からそのまま配信する（`HtmlBuilder` は生成しない）。

| ファイル | 用途 | サイズ |
| --- | --- | --- |
| `docs/og.png` | OGP 画像 | 1200×630 |
| `docs/favicon.svg` | favicon（ベクタ） | 64×64 viewBox |
| `docs/favicon-32.png` | favicon（PNG フォールバック） | 32×32 |
| `docs/apple-touch-icon.png` | iOS ホーム画面アイコン | 180×180 |

### OG 画像の更新手順

デザイン原本はリポジトリルートの `og.html`（1200×630 固定レイアウト、配色は `docs/styles.css` に準拠）。
編集後、ヘッドレスブラウザでレンダリングして `docs/og.png` を差し替える。

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --hide-scrollbars --virtual-time-budget=4000 \
  --screenshot=docs/og.png --window-size=1200,630 "file://$PWD/og.html"
```

記事件数などの動的な値は焼き込まず、静的な 1 枚として運用する（CI に画像生成ステップを持たせない）。
