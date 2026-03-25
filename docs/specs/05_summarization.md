# 05. AI 要約仕様

## 出力言語

- 常に日本語で出力
- 英語記事も日本語で要約
- 元言語は `source_language` に保存

## LLM プロバイダー抽象化

### Protocol

```python
class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str: ...
```

### 実装

- `OpenAIProvider`: openai SDK
- `GeminiProvider`: google-generativeai SDK
- `AnthropicProvider`: anthropic SDK

### Factory

```python
def create_provider(config: Config) -> LLMProvider:
    match config.llm_provider:
        case "openai": return OpenAIProvider(config)
        case "gemini": return GeminiProvider(config)
        case "anthropic": return AnthropicProvider(config)
```

## プロンプト

### summarize_full.txt

本文全文がある場合に使用。以下を要求:
- topic: 主題
- summary_3lines: 3 行要約（簡潔に、感想文にしない、事実ベース）
- priority: high / medium / low
- read_now_reason: 今読む価値の理由
- defer_reason: 後回しでよい理由
- drop_candidate: boolean
- drop_reason: ドロップ候補の理由
- keywords: キーワード 3〜5 個

### summarize_fallback.txt

メタデータのみの場合に使用。「本文未取得前提」であることを明示。

## 出力フォーマット

JSON 固定。Pydantic の `SummaryResult` でバリデーション。

## 要約ルール

- 3 行要約は簡潔に（1 行あたり長くなりすぎない）
- 記事の内容紹介であり、感想文にしない
- 日本語として自然に整える
- 英語記事でも直訳調にしすぎない
- 事実不明な断定を避ける

## 優先度判定基準

### high（今読む価値が高い）

- 新規性が高い
- 関心領域と近い
- 今後の発信や調査に活かせる
- 実務や制作に影響がある
- 要約だけでは足りず、本文を読む価値がある

### medium（時間があれば読む価値がある）

- 要点は短く把握できる
- 深掘り前提でまとまった時間が必要

### low（要約把握で十分、後回しでよい）

- 内容の重複度が高そう
- 関心軸から遠い
- 速報性が過ぎて後追い価値が低い

## エラーハンドリング

- LLM 応答が JSON でない場合 → リトライ 1 回
- リトライ失敗 → `status = "failed"`, `reason = "llm_failed"`
- タイムアウト → 同上
