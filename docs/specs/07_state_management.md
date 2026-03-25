# 07. 状態管理仕様

## 概要

`state/index.json` で記事の処理状態を管理し、差分処理を実現する。

## 差分判定ルール

### 基本ルール

- `raindrop_id` を主キーとする
- `summarized` 済みは通常スキップ
- `content_hash` が変わった場合は再要約対象にできる設計にする
- 初期リリースでは再要約は明示的フラグ（`reprocess` コマンド）のみ

### 初期リリースの実運用ルール

- 新規記事のみ要約
- 1 回の処理上限は 30 件（`MAX_SUMMARIZE_PER_RUN`）
- 上限を超えた分は次回へ持ち越し

## 状態遷移

```
[Raindrop API取得]
    ↓
  pending ──→ fetched ──→ extracted ──→ summarized
    │            │           │
    │            │           └→ fallback_ready → summarized
    │            │
    │            └→ skipped (fetch_failed)
    │            └→ failed
    │
    └→ skipped (unsupported_video, unsupported_non_html)
```

## index.json 構造

```json
{
  "last_run_at": "ISO8601",
  "items": {
    "{raindrop_id}": {
      "status": "summarized | skipped | failed | pending",
      "content_hash": "sha256:... | null",
      "reason": "スキップ理由 | null",
      "summarized_at": "ISO8601 | null",
      "updated_at": "ISO8601"
    }
  }
}
```

## 操作

### 新規記事の検出

```
Raindrop API の ID 一覧 - index.json の既存 ID = 新規記事
```

### 処理対象の決定

1. 新規記事を `created_at` の新しい順にソート
2. 先頭から `MAX_SUMMARIZE_PER_RUN` 件を処理対象にする
3. 残りは `pending` として index に追加

### 再処理

- `reprocess --id`: 指定 ID のエントリを index から削除して再処理
- `reprocess-failed`: `status == "failed"` のエントリを一括で再処理対象にする
