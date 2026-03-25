"""AI 要約。LLM プロバイダー抽象化 + 要約実行。"""

import json
import logging
from pathlib import Path
from typing import Protocol

from src.config import Config
from src.models import SummaryResult

logger = logging.getLogger("raindrop_summarizer")

PROMPTS_DIR = Path("prompts")


# --- LLM プロバイダー抽象化 ---


class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


class OpenAIProvider:
    """OpenAI API プロバイダー。"""

    def __init__(self, config: Config) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=config.llm_api_key)
        self.model = config.llm_model

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""


class GeminiProvider:
    """Google Gemini API プロバイダー。"""

    def __init__(self, config: Config) -> None:
        from google import genai

        self.client = genai.Client(api_key=config.llm_api_key)
        self.model_name = config.llm_model

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text or ""


class AnthropicProvider:
    """Anthropic API プロバイダー。"""

    def __init__(self, config: Config) -> None:
        from anthropic import Anthropic

        self.client = Anthropic(api_key=config.llm_api_key)
        self.model = config.llm_model

    def generate(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""


def create_provider(config: Config) -> LLMProvider:
    """Config に基づき LLM プロバイダーを生成する。"""
    match config.llm_provider:
        case "openai":
            return OpenAIProvider(config)
        case "gemini":
            return GeminiProvider(config)
        case "anthropic":
            return AnthropicProvider(config)
        case _:
            raise ValueError(f"未対応の LLM プロバイダー: {config.llm_provider}")


# --- プロンプト読み込み ---


def _load_prompt(name: str) -> str:
    """prompts/ からプロンプトテンプレートを読み込む。"""
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8")


# --- 要約実行 ---


def summarize_fulltext(
    provider: LLMProvider,
    text: str,
    title: str = "",
    url: str = "",
    domain: str = "",
) -> SummaryResult | None:
    """本文全文から要約を生成する。"""
    template = _load_prompt("summarize_full.txt")
    prompt = template.format(title=title, url=url, domain=domain, text=text)
    return _call_and_parse(provider, prompt)


def summarize_fallback(
    provider: LLMProvider,
    fallback_input: dict,
) -> SummaryResult | None:
    """メタデータから簡易要約を生成する。"""
    template = _load_prompt("summarize_fallback.txt")
    metadata_str = json.dumps(fallback_input, ensure_ascii=False, indent=2)
    prompt = template.format(metadata=metadata_str)
    return _call_and_parse(provider, prompt)


def _call_and_parse(provider: LLMProvider, prompt: str) -> SummaryResult | None:
    """LLM を呼び出し、レスポンスを SummaryResult にパースする。リトライ 1 回。"""
    for attempt in range(2):
        try:
            raw = provider.generate(prompt)
            return _parse_response(raw)
        except Exception as e:
            if attempt == 0:
                logger.warning(f"LLM 呼び出し/パース失敗、リトライします: {e}")
            else:
                logger.error(f"LLM 呼び出し/パース失敗（リトライ後）: {e}")
    return None


def _parse_response(raw: str) -> SummaryResult:
    """LLM レスポンスから JSON を抽出し SummaryResult にパースする。"""
    text = raw.strip()

    # ```json ... ``` で囲まれている場合
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()

    data = json.loads(text)
    return SummaryResult.model_validate(data)
