"""summarizer.py のテスト。"""

import json

import pytest

from src.config import Config
from src.models import Priority, SummaryResult
from src.summarizer import (
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
