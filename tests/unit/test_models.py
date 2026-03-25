"""models.py のテスト。"""

from datetime import UTC, datetime

from src.models import (
    ArticleState,
    ContentType,
    ManualStatus,
    Priority,
    ProcessedArticle,
    RaindropItem,
    SkipReason,
    StateEntry,
    StateIndex,
    SummaryInputType,
    SummaryResult,
)


class TestEnums:
    def test_article_state_values(self):
        assert ArticleState.pending.value == "pending"
        assert ArticleState.summarized.value == "summarized"
        assert len(ArticleState) == 7

    def test_skip_reason_values(self):
        assert SkipReason.fetch_failed.value == "fetch_failed"
        assert len(SkipReason) == 7

    def test_priority_values(self):
        assert Priority.high.value == "high"
        assert Priority.medium.value == "medium"
        assert Priority.low.value == "low"

    def test_content_type_values(self):
        assert ContentType.article.value == "article"
        assert ContentType.video.value == "video"

    def test_manual_status_values(self):
        assert ManualStatus.untriaged.value == "untriaged"

    def test_summary_input_type_values(self):
        assert SummaryInputType.fulltext.value == "fulltext"
        assert SummaryInputType.metadata.value == "metadata"


class TestRaindropItem:
    def test_create(self):
        item = RaindropItem(
            raindrop_id=123,
            collection_id=100,
            created_at=datetime(2026, 3, 25, tzinfo=UTC),
        )
        assert item.raindrop_id == 123
        assert item.title == ""
        assert item.tags == []

    def test_full_fields(self):
        item = RaindropItem(
            raindrop_id=1,
            collection_id=2,
            title="Test",
            url="https://example.com",
            domain="example.com",
            created_at=datetime(2026, 3, 25, tzinfo=UTC),
            tags=["python"],
            excerpt="excerpt",
            type="link",
        )
        assert item.title == "Test"
        assert item.tags == ["python"]


class TestSummaryResult:
    def test_defaults(self):
        result = SummaryResult()
        assert result.topic == ""
        assert result.priority == Priority.medium
        assert result.drop_candidate is False

    def test_from_dict(self):
        data = {
            "topic": "テスト",
            "summary_3lines": ["1", "2", "3"],
            "priority": "high",
            "keywords": ["a", "b"],
        }
        result = SummaryResult.model_validate(data)
        assert result.priority == Priority.high
        assert len(result.summary_3lines) == 3


class TestProcessedArticle:
    def test_defaults(self):
        article = ProcessedArticle(
            raindrop_id=1,
            collection_id=100,
            created_at=datetime(2026, 3, 25, tzinfo=UTC),
        )
        assert article.manual_status == ManualStatus.untriaged
        assert article.output_language == "ja"
        assert article.content_type == ContentType.article

    def test_serialization_roundtrip(self):
        article = ProcessedArticle(
            raindrop_id=1,
            collection_id=100,
            title="Test",
            created_at=datetime(2026, 3, 25, tzinfo=UTC),
            priority=Priority.high,
        )
        data = article.model_dump(mode="json")
        restored = ProcessedArticle.model_validate(data)
        assert restored.raindrop_id == 1
        assert restored.priority == Priority.high


class TestStateIndex:
    def test_empty(self):
        index = StateIndex()
        assert index.last_run_at is None
        assert index.items == {}

    def test_with_entries(self):
        index = StateIndex(
            items={
                "123": StateEntry(status=ArticleState.summarized),
                "456": StateEntry(status=ArticleState.skipped, reason="fetch_failed"),
            }
        )
        assert len(index.items) == 2
        assert index.items["456"].reason == "fetch_failed"
