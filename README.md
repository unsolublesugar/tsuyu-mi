# Raindrop Collection Summarizer

Raindrop.io の特定コレクションを定期取得し、保存記事の本文を抽出して AI で短く要約し、HTML 一覧として出力するバッチツールです。

## 目的

Raindrop に溜めた「あとで読む」記事を、全文を読む前に一次判定できる状態にします。

- 今読むべきか
- 後回しでよいか
- 読まずに捨ててよいか

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/unsolublesugar/raindrop-collection-summarizer.git
cd raindrop-collection-summarizer
```

### 2. Python 環境を用意

Python 3.11 以上が必要です。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. 環境変数を設定

```bash
cp .env.example .env
# .env を編集して API キーなどを設定
```

必要な環境変数:
- `RAINDROP_TOKEN`: Raindrop.io API テストトークン
- `RAINDROP_COLLECTION_ID`: 対象コレクション ID
- `LLM_PROVIDER`: `openai` / `gemini` / `anthropic`
- `LLM_API_KEY`: LLM の API キー
- `LLM_MODEL`: 使用するモデル名

## 使い方

```bash
# フルパイプライン実行（取得 → 抽出 → 要約 → HTML 生成）
python -m src.main run

# Raindrop 取得のみ
python -m src.main fetch-only

# HTML 再生成
python -m src.main build-html

# 特定記事の再処理
python -m src.main reprocess --id 123456789

# 失敗記事の一括再試行
python -m src.main reprocess-failed
```

## 出力

`docs/index.html` に記事一覧が生成されます。ブラウザで開いて確認できます。

## テスト

```bash
pytest
```

## ライセンス

MIT
