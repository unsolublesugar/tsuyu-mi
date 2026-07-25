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
  "scores": {
    "novelty": 2,
    "relevance": 2,
    "depth": 1,
    "actionability": 2
  },
  "priority": "medium",
  "read_now_reason": "今読む価値の理由",
  "defer_reason": "後回しでよい理由",
  "drop_candidate": false,
  "drop_reason": "",
  "keywords": ["キーワード1", "キーワード2", "キーワード3"]
}
```

### PriorityScores

優先度判定の 4 軸スコア。各軸 0〜3 の整数（`SCORE_MIN` 〜 `SCORE_MAX`）。範囲外の値は Pydantic バリデータで丸める。

| フィールド | 意味 |
|---|---|
| `novelty` | 新規性。既知の再掲か、初出・独自の情報や視点があるか |
| `relevance` | 関心の近さ。実務・制作・技術発信にどれだけ近いテーマか |
| `depth` | 読む必要性。3 行要約で足りるか、本文まで読む必要があるか |
| `actionability` | 活用度。手順・設定・数値など、そのまま使える具体性があるか |

`scores` がある場合、`priority` と `drop_candidate` は `src/priority.py` が再計算した値で上書きされる（LLM が返した `priority` は無視される）。`scores` が無い場合のみ LLM の `priority` をそのまま採用する（旧データ・パース失敗時のフォールバック）。判定基準は [05_summarization.md](05_summarization.md) を参照。

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
  "scores": {
    "novelty": 2,
    "relevance": 2,
    "depth": 1,
    "actionability": 2
  },
  "priority": "medium",
  "read_now_reason": "最近の関心領域と近く、今後の発信や調査に活かしやすいため。",
  "defer_reason": "要点把握だけでも十分で、緊急性は高くないため。",
  "drop_candidate": false,
  "drop_reason": "",
  "keywords": ["AI", "検索", "プロダクト"],
  "model_provider": "gemini",
  "model_name": "gemini-3.5-flash-lite",
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
