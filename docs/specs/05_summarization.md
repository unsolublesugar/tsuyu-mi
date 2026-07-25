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

- `OpenAIProvider`: openai SDK。`response_format={"type": "json_object"}` で JSON を強制する。
  **`temperature` は渡さない** — GPT-5 系（推論モデル）は既定値以外を受け付けず 400 になる。
- `GeminiProvider`: google-genai SDK。`response_mime_type="application/json"` で JSON を強制する。
- `AnthropicProvider`: anthropic SDK。thinking が既定で有効なモデル（Claude Opus 5 など）では
  `content[0]` が thinking ブロックになるため、**最初の `text` ブロックを探して返す**。
  `stop_reason == "refusal"` は例外にしてリトライ経路へ流す。

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
- scores: 優先度判定の 4 軸スコア（novelty / relevance / depth / actionability、各 0〜3）
- read_now_reason: 今読む価値の理由
- defer_reason: 後回しでよい理由
- drop_candidate: boolean
- drop_reason: ドロップ候補の理由
- keywords: キーワード 3〜5 個
- priority: high / medium / low（scores から再計算されるためフォールバック用）

### summarize_fallback.txt

メタデータのみの場合に使用。「本文未取得前提」であることを明示。scores は確信の持てない軸を低め（0〜1）に付けるよう追加で指示する。

## 出力フォーマット

JSON 固定。Pydantic の `SummaryResult` でバリデーション。

## 要約ルール

- 3 行要約は簡潔に（1 行あたり長くなりすぎない）
- 記事の内容紹介であり、感想文にしない
- 日本語として自然に整える
- 英語記事でも直訳調にしすぎない
- 事実不明な断定を避ける

## 優先度判定

### 方式: スコアリング + 決定論的変換

LLM に `high` / `medium` / `low` を直接選ばせると、ブックマーク済みの記事はどれも多少は興味を引くため判定が **high に偏る**（実測で 15 件中 14 件が high）。そのため次の 2 段構成にする。

1. LLM は 4 軸（`novelty` / `relevance` / `depth` / `actionability`）を **0〜3 で採点するだけ**
2. `src/priority.py` がスコアから `priority` と `drop_candidate` を決定論的に導出する

閾値がコード側にあるため、仕分けの厳しさはプロンプトを触らずに調整でき、ユニットテストで保証できる。

### 採点基準（プロンプト側）

| 点 | 意味 |
|---|---|
| 0 | 該当しない、またはむしろ逆 |
| 1 | 少しは当てはまる（多くの記事はここ） |
| 2 | 明確に当てはまる |
| 3 | 例外的に強く当てはまる（滅多に付けない） |

プロンプトでは「ブックマーク済みゆえに全体的に高く付けたくなる」ことを明示し、**相対評価**で平均的な記事を合計 5〜8 に収めるよう指示する。フォールバック（本文未取得）プロンプトでは、判断材料が乏しいため確信の持てない軸は低め（0〜1）に付けるよう追加で指示する。

### 閾値（`src/priority.py`）

| 定数 | 値 | 用途 |
|---|---|---|
| `HIGH_TOTAL_MIN` | 10 | high の合計下限 |
| `HIGH_DEPTH_MIN` | 2 | high に必要な `depth` の下限 |
| `MEDIUM_TOTAL_MIN` | 5 | medium の合計下限 |
| `DROP_TOTAL_MAX` | 2 | ドロップ候補の合計上限 |

- `high`: 合計 10 点以上 **かつ** `depth` >= 2（要約で足りる記事は high に上げない）
- `medium`: 合計 5〜9 点
- `low`: 合計 4 点以下
- `drop_candidate`: 合計 2 点以下、または LLM が明示的に true を返した場合

### フォールバック

`scores` が無い場合（旧データ、LLM が出力できなかった場合）は、LLM が返した `priority` をそのまま採用する。プロンプトは互換のため `priority` フィールドも引き続き要求する。

## エラーハンドリング

- LLM 応答が JSON でない場合 → リトライ 1 回
- リトライ失敗 → `status = "failed"`, `reason = "llm_failed"`
- タイムアウト → 同上
