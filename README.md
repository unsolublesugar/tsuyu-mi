# Raindrop Collection Summarizer

Raindrop.io の特定コレクションを定期取得し、保存記事の本文を抽出して AI で短く要約し、HTML 一覧として出力するバッチツールです。

![Raindrop Collection Summary](assets/images/screenshot.png)

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

Python 3.11 以上が必要です。[uv](https://docs.astral.sh/uv/) を使うと Python ごとインストールできます。

```bash
# uv を使う場合（推奨）
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev]"

# pip を使う場合
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. API キーの取得

このツールの実行には **Raindrop.io API トークン** と **LLM API キー** の 2 つが必要です。

#### Raindrop.io テストトークン

1. [Raindrop.io Integrations](https://app.raindrop.io/settings/integrations) にアクセス
2. 「For Developers」セクションの **Create new app** をクリック
3. アプリ名を入力（例: `RaindropSummarizer`）して作成
4. 作成したアプリをクリック → **Create test token** をクリック
5. 表示されたトークンをコピー

#### コレクション ID の確認

1. [Raindrop.io](https://app.raindrop.io) にアクセス
2. 対象のコレクション（「あとで読む」等）を開く
3. URL を確認: `https://app.raindrop.io/my/{collection_id}` — この数値部分がコレクション ID

#### LLM API キー

以下のいずれか 1 つのプロバイダーの API キーを取得します。

**Google Gemini（推奨・無料枠あり）**

1. [Google AI Studio](https://aistudio.google.com/apikey) にアクセス
2. **Create API Key** → **Create API key in new project** を選択
3. API キーが発行される
4. 推奨モデル: `gemini-2.5-flash`

> Google Cloud の請求先アカウントの紐づけと [Gemini API の有効化](https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com) が必要な場合があります。

**OpenAI**

1. [OpenAI API Keys](https://platform.openai.com/api-keys) にアクセス
2. **Create new secret key** でキーを生成
3. 推奨モデル: `gpt-4.1-mini`

**Anthropic**

1. [Anthropic Console](https://console.anthropic.com/settings/keys) にアクセス
2. **Create Key** でキーを生成
3. 推奨モデル: `claude-haiku-4-5-20251001`

### 4. 環境変数の設定

#### ローカル実行の場合

```bash
cp .env.example .env
```

`.env` を開いて取得したキーを設定します:

```env
RAINDROP_TOKEN=your-raindrop-token
RAINDROP_COLLECTION_ID=your-collection-id
LLM_PROVIDER=gemini
LLM_API_KEY=your-llm-api-key
LLM_MODEL=gemini-2.5-flash
```

> `.env` はリポジトリにコミットしないでください。

#### GitHub Actions の場合

リポジトリの Settings → Secrets and variables → Actions → Repository secrets に以下を設定:

| Secret 名 | 値 |
|---|---|
| `RAINDROP_TOKEN` | Raindrop.io API テストトークン |
| `RAINDROP_COLLECTION_ID` | 対象コレクション ID |
| `LLM_PROVIDER` | `gemini` / `openai` / `anthropic` |
| `LLM_API_KEY` | LLM の API キー |
| `LLM_MODEL` | モデル名（例: `gemini-2.5-flash`） |

### 5. 動作確認

```bash
# まず Raindrop API の接続だけ確認（LLM 不要）
python -m src fetch-only

# 少数で要約を試す
MAX_SUMMARIZE_PER_RUN=3 python -m src run

# 問題なければフル実行
python -m src run
```

## 使い方

```bash
# フルパイプライン実行（取得 → 抽出 → 要約 → HTML 生成）
python -m src run

# 対象記事を確認だけ（処理はしない）
python -m src run --dry-run

# 詳細ログ付き実行
python -m src run --verbose

# Raindrop 取得のみ
python -m src fetch-only

# HTML 再生成
python -m src build-html

# 特定記事の再処理
python -m src reprocess --id 123456789

# 失敗記事の一括再試行
python -m src reprocess-failed
```

## 出力

`docs/index.html` に記事一覧が生成されます。ブラウザで開いて確認できます。

- 優先度ごとに色分け（HIGH=赤 / MEDIUM=黄 / LOW=灰）
- フィルタボタンで優先度別に絞り込み可能
- 各記事に 3 行要約・今読む理由・後回し理由・キーワードを表示

## 設定

| 環境変数 | 説明 | デフォルト |
|---|---|---|
| `RAINDROP_TOKEN` | Raindrop.io API テストトークン | （必須） |
| `RAINDROP_COLLECTION_ID` | 対象コレクション ID | （必須） |
| `LLM_PROVIDER` | `openai` / `gemini` / `anthropic` | `openai` |
| `LLM_API_KEY` | LLM の API キー | （必須） |
| `LLM_MODEL` | 使用するモデル名 | （必須） |
| `MAX_SUMMARIZE_PER_RUN` | 1 回の要約件数上限 | `30` |
| `REQUEST_TIMEOUT_SECONDS` | HTTP リクエストタイムアウト | `20` |
| `USER_AGENT` | HTTP リクエストの User-Agent | `RaindropSummarizer/0.1` |
| `OUTPUT_DIR` | HTML 出力先ディレクトリ | `docs` |
| `DATA_DIR` | データ保存ディレクトリ | `data` |
| `STATE_DIR` | 状態管理ディレクトリ | `state` |
| `LOG_LEVEL` | ログレベル | `INFO` |

## GitHub Actions による自動運用

### 1. GitHub Secrets の設定

セットアップの「4. 環境変数の設定 → GitHub Actions の場合」を参照してください。

### 2. GitHub Pages の有効化

Settings → Pages → Source を **Deploy from a branch** に設定:
- Branch: `main`
- Folder: `/docs`

> プライベートリポジトリで GitHub Pages を使うには **GitHub Pro** 以上が必要です。

### 3. 実行スケジュール

- **自動実行**: 3 日おき JST 7:00（UTC 22:00）
- **手動実行**: Actions タブから「Run workflow」で即時実行可能

変更があった場合のみ自動コミット・プッシュされます。

## テスト

```bash
pytest
```

## ライセンス

MIT
