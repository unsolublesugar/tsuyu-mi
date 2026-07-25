"""summarizer.py のテスト。"""

import json

import pytest

from src.config import Config
from src.models import Priority, SummaryResult
from src.summarizer import (
    AnthropicProvider,
    OpenAIProvider,
    _load_prompt,
    _parse_response,
    create_provider,
    summarize_fallback,
    summarize_fulltext,
)


class MockProvider:
    """テスト用のモック LLM プロバイダー。"""

    def __init__(self, response: str = ""):
        self.response = response
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


class FailingProvider:
    """常に失敗するプロバイダー。"""

    def generate(self, prompt: str) -> str:
        raise RuntimeError("LLM error")


def _valid_response(**overrides) -> str:
    data = {
        "topic": "テスト主題",
        "summary_3lines": ["1行目", "2行目", "3行目"],
        "priority": "high",
        "read_now_reason": "理由",
        "defer_reason": "後回し理由",
        "drop_candidate": False,
        "drop_reason": "",
        "keywords": ["AI", "テスト"],
    }
    data.update(overrides)
    return json.dumps(data, ensure_ascii=False)


class TestLoadPrompt:
    def test_load_full(self):
        prompt = _load_prompt("summarize_full.txt")
        assert "{title}" in prompt
        assert "{text}" in prompt

    def test_load_fallback(self):
        prompt = _load_prompt("summarize_fallback.txt")
        assert "{metadata}" in prompt


class TestParseResponse:
    def test_valid_json(self):
        result = _parse_response(_valid_response())
        assert isinstance(result, SummaryResult)
        assert result.topic == "テスト主題"
        assert result.priority == Priority.high

    def test_codeblock_json(self):
        raw = "```json\n" + _valid_response() + "\n```"
        result = _parse_response(raw)
        assert result.topic == "テスト主題"

    def test_invalid_json(self):
        with pytest.raises(Exception):
            _parse_response("not json")

    def test_scores_override_llm_priority(self):
        """scores がある場合、LLM が返した priority は無視して再計算する。"""
        raw = _valid_response(
            priority="high",
            scores={"novelty": 1, "relevance": 1, "depth": 1, "actionability": 1},
        )
        result = _parse_response(raw)
        assert result.scores is not None
        assert result.scores.total == 4
        assert result.priority == Priority.low

    def test_scores_promote_to_high(self):
        raw = _valid_response(
            priority="low",
            scores={"novelty": 3, "relevance": 3, "depth": 3, "actionability": 2},
        )
        result = _parse_response(raw)
        assert result.priority == Priority.high

    def test_scores_set_drop_candidate(self):
        raw = _valid_response(
            drop_candidate=False,
            scores={"novelty": 1, "relevance": 0, "depth": 0, "actionability": 0},
        )
        result = _parse_response(raw)
        assert result.priority == Priority.low
        assert result.drop_candidate is True

    def test_llm_drop_candidate_is_preserved(self):
        """スコアが高くても LLM が drop 判定していれば維持する。"""
        raw = _valid_response(
            drop_candidate=True,
            scores={"novelty": 2, "relevance": 2, "depth": 2, "actionability": 2},
        )
        result = _parse_response(raw)
        assert result.drop_candidate is True

    def test_without_scores_falls_back_to_llm_priority(self):
        """旧プロンプト互換: scores がなければ LLM の priority をそのまま使う。"""
        result = _parse_response(_valid_response(priority="high"))
        assert result.scores is None
        assert result.priority == Priority.high


class TestSummarizeFulltext:
    def test_success(self):
        mock = MockProvider(_valid_response())
        result = summarize_fulltext(mock, "本文テキスト", title="タイトル")
        assert result is not None
        assert result.topic == "テスト主題"
        assert "タイトル" in mock.last_prompt

    def test_failure_returns_none(self):
        result = summarize_fulltext(FailingProvider(), "本文")
        assert result is None


class TestSummarizeFallback:
    def test_success(self):
        mock = MockProvider(_valid_response())
        result = summarize_fallback(mock, {"title": "Test", "excerpt": "Exc"})
        assert result is not None
        assert "Test" in mock.last_prompt


class TestCreateProvider:
    def test_invalid_provider(self):
        config = Config(llm_provider="invalid")
        with pytest.raises(ValueError, match="invalid"):
            create_provider(config)


class _Block:
    def __init__(self, type_: str, text: str = "", thinking: str = ""):
        self.type = type_
        self.text = text
        self.thinking = thinking


class _AnthropicResponse:
    def __init__(self, content, stop_reason="end_turn"):
        self.content = content
        self.stop_reason = stop_reason


class _StubMessages:
    def __init__(self, response):
        self.response = response
        self.last_kwargs: dict = {}

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self.response


def _anthropic_provider(response) -> AnthropicProvider:
    """SDK を呼ばずに AnthropicProvider を組み立てる。"""
    provider = object.__new__(AnthropicProvider)
    provider.client = type("Client", (), {"messages": _StubMessages(response)})()
    provider.model = "claude-haiku-4-5"
    return provider


class TestAnthropicProvider:
    def test_returns_text_block(self):
        provider = _anthropic_provider(_AnthropicResponse([_Block("text", text="{}")]))
        assert provider.generate("p") == "{}"

    def test_skips_thinking_block(self):
        """thinking が既定で有効なモデルでも本文を取り出せること。"""
        response = _AnthropicResponse(
            [_Block("thinking", thinking="考え中"), _Block("text", text="{}")]
        )
        assert _anthropic_provider(response).generate("p") == "{}"

    def test_refusal_raises(self):
        response = _AnthropicResponse([], stop_reason="refusal")
        with pytest.raises(RuntimeError, match="refusal"):
            _anthropic_provider(response).generate("p")

    def test_empty_content_returns_empty(self):
        assert _anthropic_provider(_AnthropicResponse([])).generate("p") == ""


class TestOpenAIProvider:
    def test_does_not_send_temperature(self):
        """GPT-5 系は既定値以外の temperature を受け付けず 400 になるため送らない。"""
        message = type("Message", (), {"content": "{}"})()
        choice = type("Choice", (), {"message": message})()
        stub = _StubMessages(type("Response", (), {"choices": [choice]})())

        provider = object.__new__(OpenAIProvider)
        completions = type("Completions", (), {"create": stub.create})
        provider.client = type(
            "Client", (), {"chat": type("Chat", (), {"completions": completions()})()}
        )()
        provider.model = "gpt-5.6-luna"

        assert provider.generate("p") == "{}"
        assert "temperature" not in stub.last_kwargs
        assert stub.last_kwargs["response_format"] == {"type": "json_object"}


class TestPromptsRequestScores:
    """プロンプトが scores を要求していることを保証する（優先度の high 偏り対策）。"""

    @pytest.mark.parametrize("name", ["summarize_full.txt", "summarize_fallback.txt"])
    def test_prompt_defines_score_axes(self, name):
        prompt = _load_prompt(name)
        for axis in ("novelty", "relevance", "depth", "actionability"):
            assert axis in prompt
