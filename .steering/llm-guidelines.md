# LLM プロバイダーガイドライン

## プロバイダー切り替え

- `LLM_PROVIDER` 環境変数で `openai` / `gemini` / `anthropic` を指定
- `LLMProvider` Protocol を実装した各プロバイダークラスで抽象化
- Factory 関数で config に基づきインスタンス生成

## プロンプト設計方針

- プロンプトは `prompts/` ディレクトリに外部ファイルとして管理
- `summarize_full.txt`: 本文全文がある場合
- `summarize_fallback.txt`: メタデータのみの場合
- テンプレート変数: `{title}`, `{url}`, `{domain}`, `{text}` 等を `str.format()` で埋め込み

## 出力仕様

- 常に日本語で出力
- JSON 形式を要求し、パース + Pydantic でバリデーション
- 出力スキーマ: topic, summary_3lines, priority, read_now_reason, defer_reason, drop_candidate, drop_reason, keywords

## 本文長による要約モード

- 1500 文字以上: 通常要約（summarize_full.txt）
- 500〜1499 文字: 短文要約（同プロンプト、短め指示）
- 500 文字未満: 簡易要約寄り
- 取得不能: fallback プロンプト（summarize_fallback.txt）
