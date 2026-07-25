# LLM プロバイダーガイドライン

## プロバイダー切り替え

- `LLM_PROVIDER` 環境変数で `gemini`（既定） / `openai` / `anthropic` を指定
- `LLMProvider` Protocol を実装した各プロバイダークラスで抽象化
- Factory 関数で config に基づきインスタンス生成

### モデル選定方針

処理は「3 行要約 + 4 軸スコアリング」のバッチで、高価な推論モデルは不要。各プロバイダーの低コスト帯を既定とする（2026 年 7 月時点: `gemini-3.5-flash-lite` / `gpt-5.6-luna` / `claude-haiku-4-5`）。モデル名はコードに埋め込まず `LLM_MODEL` で切り替える。

### プロバイダー実装時の注意

- **OpenAI**: GPT-5 系は `temperature` / `top_p` の既定値以外を受け付けず 400 になる。渡さないこと。
- **Anthropic**: thinking が既定で有効なモデルでは `content[0]` が thinking ブロックになる。
  先頭決め打ちではなく最初の `text` ブロックを探す。`stop_reason == "refusal"` も扱う。
- **Gemini**: `response_mime_type="application/json"` で JSON を強制する。
- モデルを追加・更新する際は、SDK の破壊的変更（パラメータの削除など）を公式ドキュメントで確認する。

## プロンプト設計方針

- プロンプトは `prompts/` ディレクトリに外部ファイルとして管理
- `summarize_full.txt`: 本文全文がある場合
- `summarize_fallback.txt`: メタデータのみの場合
- テンプレート変数: `{title}`, `{url}`, `{domain}`, `{text}` 等を `str.format()` で埋め込み

## 出力仕様

- 常に日本語で出力
- JSON 形式を要求し、パース + Pydantic でバリデーション
- 出力スキーマ: topic, summary_3lines, scores, read_now_reason, defer_reason, drop_candidate, drop_reason, keywords, priority
- **優先度は LLM に直接選ばせない。** LLM は 4 軸スコア（scores）を採点するだけで、
  `priority` / `drop_candidate` は `src/priority.py` の閾値から導出する。
  LLM に high/medium/low を選ばせると high に偏るため。仕分けの厳しさを変えるときは
  プロンプトではなく `src/priority.py` の閾値定数を調整する。

## 本文長による要約モード

- 1500 文字以上: 通常要約（summarize_full.txt）
- 500〜1499 文字: 短文要約（同プロンプト、短め指示）
- 500 文字未満: 簡易要約寄り
- 取得不能: fallback プロンプト（summarize_fallback.txt）
