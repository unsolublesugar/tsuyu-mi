# データモデル概要

## 記事の状態遷移

```
pending → fetched → extracted → summarized
                  ↘ fallback_ready ↗
          ↘ skipped (理由付き)
          ↘ failed (エラーログ付き)
```

## スキップ理由

- `fetch_failed`: URL 取得失敗
- `extract_failed`: 本文抽出失敗
- `summary_input_unavailable`: 簡易要約用入力も不足
- `unsupported_video`: 動画コンテンツ
- `unsupported_non_html`: 非 HTML コンテンツ
- `llm_failed`: LLM 応答失敗
- `too_short`: 本文が短すぎる

## 主要モデル

- `RaindropItem`: Raindrop API レスポンスの内部表現
- `ProcessedArticle`: 処理済み記事の正本（`data/articles/{id}.json`）
- `SummaryResult`: LLM 出力の JSON スキーマ
- `StateEntry` / `StateIndex`: 差分管理用（`state/index.json`）

詳細なスキーマ定義は `src/models.py` および `docs/specs/02_data_models.md` を参照。
