# アーキテクチャ概要

## 処理パイプライン

```
Raindrop API → fetch → diff check → fetch URL → extract body → LLM summarize → store JSON → build HTML
```

## モジュール依存関係

```
main.py (CLI オーケストレーション)
  ├── config.py          (環境変数)
  ├── logging_util.py    (ロガー)
  ├── raindrop_client.py (API 取得)
  │     └── models.py
  ├── state_store.py     (差分管理)
  │     ├── models.py
  │     └── utils/hashing.py
  ├── content_fetcher.py (HTML 取得)
  ├── content_extractor.py (本文抽出)
  │     └── utils/text.py
  ├── summarizer.py      (LLM 要約)
  │     └── models.py
  ├── article_repository.py (JSON 保存)
  │     └── models.py
  └── html_builder.py    (HTML 生成)
        ├── models.py
        └── utils/time.py
```

## 設計判断

| 項目 | 判断 | 理由 |
|---|---|---|
| 同期/非同期 | 同期 | MVP は 30 件上限。まず動くものを優先 |
| LLM 抽象化 | Protocol + Factory | SDK の違いを各 Provider 内に閉じ込め |
| JSON 保存 | 1 記事 = 1 ファイル | reprocess が容易 |
| HTML 出力先 | `docs/` | GitHub Pages 対応 |
| プロンプト | 外部ファイル `prompts/*.txt` | コード変更なしで調整可能 |
