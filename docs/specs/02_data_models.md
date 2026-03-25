# 02. データモデル定義

## 状態 Enum

### ArticleState

```
pending → fetched → extracted → summarized
                  ↘ fallback_ready ↗
          ↘ skipped
          ↘ failed
```

- `pending`: 未処理
- `fetched`: HTML 取得済み
- `extracted`: 本文抽出済み
- `fallback_ready`: 簡易要約用入力構成済み
- `summarized`: 要約完了
- `skipped`: スキップ（理由付き）
- `failed`: 処理失敗（エラーログ付き）

### SkipReason

`fetch_failed` / `extract_failed` / `summary_input_unavailable` / `unsupported_video` / `unsupported_non_html` / `llm_failed` / `too_short`

### ContentType

`article` / `video` / `other`

### Priority

`high` / `medium` / `low`

### ManualStatus

`untriaged` / `read` / `keep` / `drop`

## RaindropItem

Raindrop API レスポンスから抽出する内部モデル。

```json
{
  "raindrop_id": 123456789,
  "collection_id": 111111,
  "title": "Example title",
  "url": "https://example.com/article",
  "domain": "example.com",
  "created_at": "2026-03-25T00:00:00Z",
  "tags": [],
  "excerpt": "short excerpt",
  "type": "link",
  "cover": "",
  "note": ""
}
```

## SummaryResult

LLM 出力の JSON スキーマ。

```json
{
  "topic": "主題",
  "summary_3lines": ["1行目", "2行目", "3行目"],
  "priority": "high",
  "read_now_reason": "今読む価値の理由",
  "defer_reason": "後回しでよい理由",
  "drop_candidate": false,
  "drop_reason": "",
  "keywords": ["キーワード1", "キーワード2", "キーワード3"]
}
```

## ProcessedArticle

処理済み記事の正本データ。`data/articles/{raindrop_id}.json` に保存。

```json
{
  "raindrop_id": 123456789,
  "collection_id": 111111,
  "title": "記事タイトル",
  "url": "https://example.com/article",
  "domain": "example.com",
  "created_at": "2026-03-25T00:00:00Z",
  "fetched_at": "2026-03-25T08:30:00Z",
  "source_language": "en",
  "output_language": "ja",
  "content_type": "article",
  "content_status": "ok",
  "fetch_status": "ok",
  "extract_method": "trafilatura",
  "content_chars": 6842,
  "content_hash": "sha256:...",
  "summary_input_type": "fulltext",
  "topic": "AI と検索体験の変化",
  "summary_3lines": [
    "この記事は〜について述べている。",
    "主な論点は〜である。",
    "実務上は〜という示唆がある。"
  ],
  "priority": "medium",
  "read_now_reason": "最近の関心領域と近く、今後の発信や調査に活かしやすいため。",
  "defer_reason": "要点把握だけでも十分で、緊急性は高くないため。",
  "drop_candidate": false,
  "drop_reason": "",
  "keywords": ["AI", "検索", "プロダクト"],
  "model_provider": "openai",
  "model_name": "gpt-4.1-mini",
  "summarized_at": "2026-03-25T08:31:00Z",
  "manual_status": "untriaged",
  "notes": ""
}
```

## StateIndex

差分管理用。`state/index.json` に保存。

```json
{
  "last_run_at": "2026-03-25T08:31:00Z",
  "items": {
    "123456789": {
      "status": "summarized",
      "content_hash": "sha256:...",
      "summarized_at": "2026-03-25T08:31:00Z"
    },
    "987654321": {
      "status": "skipped",
      "reason": "summary_input_unavailable",
      "updated_at": "2026-03-25T08:31:00Z"
    }
  }
}
```
