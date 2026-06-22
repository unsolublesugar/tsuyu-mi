"""PR #72 回帰テスト。

フォールバック要約経路（X 記事 / 本文抽出が空のケース）が
NameError を起こさず動作することを保証する。

背景: PR #72 で `src/main.py` の `summarize_fallback` import が誤って
削除されたが、本体では `_process_article` 内で今も呼ばれていた。
通常の本文要約（fulltext）経路では発火しないためすり抜けるが、
X/Twitter 記事や抽出失敗記事を処理すると
`NameError: name 'summarize_fallback' is not defined` で落ちる。
"""

import json
from datetime import UTC, datetime

import pytest

import src.main as main
from src.config import Config
from src.models import RaindropItem, SummaryInputType


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


class MockProvider:
    """テスト用のモック LLM プロバイダー（固定 JSON を返す）。"""

    def __init__(self, response: str = ""):
        self.response = response
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


class _FakeState:
    """state_store のスタブ。状態遷移呼び出しを受け流す。"""

    def update_status(self, *args, **kwargs) -> None:
        pass


class _FakeRepo:
    """article_repository のスタブ。保存された記事を保持する。"""

    def __init__(self):
        self.saved = []

    def save(self, article) -> None:
        self.saved.append(article)


@pytest.fixture
def deps():
    import logging

    config = Config(llm_provider="anthropic", llm_model="dummy-model")
    provider = MockProvider(_valid_response())
    state = _FakeState()
    repo = _FakeRepo()
    logger = logging.getLogger("test")
    return config, provider, state, repo, logger


class TestImportRegression:
    """import 削除（PR #72 の不具合本体）を直接検知する。"""

    def test_summarize_fallback_is_bound_in_main(self):
        # main.py が裸の `summarize_fallback(...)` を呼んでいるため、
        # モジュール名前空間に束縛されていないと実行時 NameError になる。
        assert hasattr(main, "summarize_fallback"), (
            "src.main に summarize_fallback が import されていません"
            "（_process_article のフォールバック経路で NameError になります）"
        )

    def test_summarize_fulltext_is_bound_in_main(self):
        assert hasattr(main, "summarize_fulltext")


class TestProcessArticleFallbackPath:
    """フォールバック経路を実際に通し、NameError なく要約が入ることを保証する。"""

    def test_x_post_uses_fallback_summary(self, deps, monkeypatch):
        config, provider, state, repo, logger = deps

        # X 記事として扱わせ、外部取得はスキップ（メタデータのみで fallback）
        monkeypatch.setattr(main, "is_x_url", lambda url: True)
        monkeypatch.setattr(main, "fetch_x_post", lambda url: None)

        raindrop = RaindropItem(
            raindrop_id=1,
            collection_id=1,
            title="Xポストのタイトル",
            url="https://x.com/foo/status/1",
            domain="x.com",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        # 修正前はこの呼び出しで NameError: summarize_fallback が送出される
        article = main._process_article(raindrop, config, provider, state, repo, logger)

        assert article is not None
        assert article.topic == "テスト主題"
        assert article.summary_input_type == SummaryInputType.metadata
        # fallback プロンプト（メタデータ）が provider に渡っていること
        assert "Xポストのタイトル" in provider.last_prompt
        assert repo.saved, "記事が保存されていません"


class TestProviderRouting:
    """PR #72 で追加される新プロバイダーの Factory 分岐を保証する。

    ollama / opencode-ai の実体に依存しないよう、Provider クラスをスタブ化して
    create_provider の分岐のみを検証する。修正前（クラス未追加）は skip。
    """

    @pytest.mark.skipif(
        not hasattr(main, "summarize_fallback"),
        reason="import 修正前はフォールバック回帰テストを優先",
    )
    @pytest.mark.parametrize("provider_name", ["ollama", "opencode"])
    def test_create_provider_dispatch(self, provider_name, monkeypatch):
        import src.summarizer as summarizer

        class_name = {"ollama": "OllamaProvider", "opencode": "OpenCodeProvider"}[provider_name]
        if not hasattr(summarizer, class_name):
            pytest.skip(f"{class_name} はまだ未実装（PR #72 取り込み後に有効化）")

        marker = object()
        monkeypatch.setattr(summarizer, class_name, lambda config: marker)

        config = Config(llm_provider=provider_name, llm_model="dummy")
        assert summarizer.create_provider(config) is marker
