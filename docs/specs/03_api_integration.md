# 03. Raindrop.io API 連携仕様

## 対象

単一コレクションのみ。

## 認証

- テストトークンを使用（OAuth 不要）
- ヘッダー: `Authorization: Bearer {RAINDROP_TOKEN}`

## エンドポイント

```
GET https://api.raindrop.io/rest/v1/raindrops/{collectionId}
```

### パラメータ

| パラメータ | 値 | 説明 |
|---|---|---|
| `perpage` | `50` | API 最大値 |
| `sort` | `-created` | 新しい順 |
| `page` | `0, 1, 2...` | ページネーション |

## ページネーション

- `page=0` から開始
- レスポンスの `items` が空になるまでループ
- 差分処理により通常は 1〜2 ページで十分

## レスポンスマッピング

API レスポンスの各フィールドを `RaindropItem` にマッピングする。

| API フィールド | 内部フィールド |
|---|---|
| `_id` | `raindrop_id` |
| `collection.$id` | `collection_id` |
| `title` | `title` |
| `link` | `url` |
| `domain` | `domain` |
| `created` | `created_at` |
| `tags` | `tags` |
| `excerpt` | `excerpt` |
| `type` | `type` |
| `cover` | `cover` |
| `note` | `note` |

## 生データ保存

取得した生レスポンスを `data/raw/latest_raindrops.json` に保存する。
デバッグおよび再処理時の参照用。

## エラーハンドリング

- 401: トークン無効 → エラーメッセージを出して終了
- 429: レートリミット → ログ出力して終了
- 5xx: サーバーエラー → ログ出力して終了
- ネットワークエラー → ログ出力して終了
