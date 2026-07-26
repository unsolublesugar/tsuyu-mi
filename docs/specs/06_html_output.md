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
- 優先度スコア（`scores` がある記事のみ表示）
- 今読む理由（read_now_reason）
- 後回し理由（defer_reason）
- ドロップ候補かどうか
- 本文取得ステータス（content_status）
- 手動ステータス（manual_status）
- メモ欄（notes）

### カードのレイアウト

2 カラム構成（`.card-body`）。

- 左（`.card-main`）: メタ行 → タイトル → 3 行要約
  - メタ行は 優先度バッジ / DROP バッジ / ドメイン / 追加日 の順に並べる
- 右（`.score-panel`）: 優先度スコアの 4 軸内訳（幅 176px 固定）

判定理由は `<details class="reasons-toggle">`（summary は「判定理由」）に折りたたみ、キーワードはカード下部に並べる。

### 優先度スコアの表示

hover 依存の `title` 属性ではなく、4 軸を常時可視のバー UI で表示する。

- 合計は `スコア N/12`。PC・モバイルとも常にスコアパネル上部（`.score-total`）の 1 箇所に出す
- 各軸（新規性 / 関心の近さ / 読む必要性 / 活用度）は `.bar` > `.fill.sN` で描画し、`N`（0〜3）に応じて CSS で幅を決める（s0 は非表示、s1=33% / s2=67% / s3=100%）
- `scores` を持たない旧データではスコアパネルを出力しない

## ソート順

初期表示:

1. priority（high → medium → low）
2. created_at の新しい順

## フィルタ

ヘッダー下のタブ（`nav.filters`）で優先度を絞り込む。

- タブは すべて / High / Medium / Low の 4 つ。初期 active は **High**（まず読むべきものから見せる）
- 各タブに件数バッジ（`.tab-count`）を出す。中身は空要素として出力し、`docs/app.js` がカード数から埋める
- 絞り込みは `docs/app.js` によるクライアントサイド処理。カードの `data-priority` を対象にする
- JS なしでも全記事が読める HTML にする（JS 無効時は絞り込みなしで全カードが並ぶ）
- 該当 0 件のときは `.filter-empty` メッセージを表示する

ステータスフィルタ・キーワード検索は未実装（今後の拡張候補）。

## スタイリング

`docs/styles.css`:

- 優先度ごとの色分け（high=赤系 / medium=黄系 / low=灰系）
- カード形式レイアウト
- ドロップ候補は視覚的に薄く表示（`opacity` + 破線ボーダー）
- 見出しに Zen Kaku Gothic New、本文に Noto Sans JP（Google Fonts、`display=swap`）
- レスポンシブ（ブレークポイントは 2 つ）
  - `max-width: 680px`: カードを 1 カラムに切り替え、スコアパネルは要約の下へ回す。合計スコアは 4 軸バーの見出しとしてパネル先頭に置く。4 軸は `auto-fit` グリッドで 2 列 → さらに狭ければ 1 列。ヘッダーの統計は非表示
  - `max-width: 360px`: フィルタタブの余白・文字サイズを詰めて 4 タブが横スクロールなしで収まるようにする

## スキップ記事の表示

- 要約済み記事とは別セクションに表示
- スキップ理由を明示
- 動画は動画アイコンで区別

## 統計情報

ヘッダー右側（`.stats`）に以下を表示する。

- `N / M 件を表示` — `N` は現在のフィルタで表示中の件数、`M` はカード総数。
  どちらも **要約済み件数**（`summarized_count`）が基準で、スキップ記事は含めない。
  静的な HTML には `M`（および JS 無効時の `N`）として `summarized_count` を焼き込み、
  `docs/app.js` がフィルタ操作に応じて `N` を書き換える
- 最終実行日時（`last_run_at` がある場合のみ）

スキップ・未処理の件数は別セクションの `<summary>` に出す（統計には混ぜない）。

ブランド表示としてサイト名とタグライン（「あとで読む」を、読む前に仕分ける）をヘッダー左に置く。

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
