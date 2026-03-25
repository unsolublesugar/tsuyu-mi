# 08. CLI インターフェース仕様

## 実行方法

```bash
python -m src.main <command>
```

## コマンド一覧

### `run`

フルパイプラインを実行。

```bash
python -m src.main run
```

処理フロー:
1. Config ロード
2. StateIndex 読込
3. Raindrop API から記事取得
4. 差分検出（最大 30 件）
5. 各記事: fetch → extract → summarize
6. StateIndex 更新
7. HTML 生成
8. 完了サマリー表示

### `fetch-only`

Raindrop 取得と生データ保存のみ。

```bash
python -m src.main fetch-only
```

### `build-html`

保存済み JSON から HTML を再生成。

```bash
python -m src.main build-html
```

### `reprocess`

特定記事を再処理。

```bash
python -m src.main reprocess --id 123456789
```

### `reprocess-failed`

失敗・スキップ記事を一括再試行。

```bash
python -m src.main reprocess-failed
```

## 共通オプション

| オプション | 説明 | デフォルト |
|---|---|---|
| `--dry-run` | 実際の処理は行わず、対象記事を表示 | false |
| `--verbose` | 詳細ログ出力 | false |

## 出力

- rich ライブラリで見やすい CLI 出力
- 処理サマリー: 取得件数、新規件数、要約件数、スキップ件数、失敗件数
- プログレスバー: 記事処理の進捗表示
