"""content_extractor.py のテスト。"""

from datetime import UTC, datetime

from src.content_extractor import (
    ExtractionResult,
    _build_fallback_input,
    _classify_length,
    extract_body,
)
from src.models import RaindropItem, SummaryInputType


def _make_raindrop(**kwargs) -> RaindropItem:
    defaults = {
        "raindrop_id": 1,
        "collection_id": 100,
        "created_at": datetime(2026, 3, 25, tzinfo=UTC),
    }
    defaults.update(kwargs)
    return RaindropItem(**defaults)


class TestClassifyLength:
    def test_fulltext(self):
        assert _classify_length(2000) == SummaryInputType.fulltext
        assert _classify_length(1500) == SummaryInputType.fulltext

    def test_shorttext(self):
        assert _classify_length(800) == SummaryInputType.shorttext
        assert _classify_length(500) == SummaryInputType.shorttext

    def test_metadata(self):
        assert _classify_length(300) == SummaryInputType.metadata
        assert _classify_length(0) == SummaryInputType.metadata


class TestBuildFallbackInput:
    def test_with_all_fields(self):
        item = _make_raindrop(
            title="Test", excerpt="Excerpt", url="https://example.com",
            domain="example.com", tags=["python"],
        )
        fb = _build_fallback_input(item, og_description="OG desc")
        assert fb["title"] == "Test"
        assert fb["og_description"] == "OG desc"
        assert fb["tags"] == ["python"]

    def test_empty_returns_empty(self):
        item = _make_raindrop()
        assert _build_fallback_input(item) == {}

    def test_title_only(self):
        item = _make_raindrop(title="Title only")
        fb = _build_fallback_input(item)
        assert fb["title"] == "Title only"


class TestExtractBody:
    def test_with_enough_content(self):
        html = "<html><body><article>" + "テスト本文。" * 200 + "</article></body></html>"
        item = _make_raindrop(title="Test")
        result = extract_body(html, item)
        assert result.ok
        assert result.method in ("trafilatura", "readability")

    def test_empty_html_fallback(self):
        item = _make_raindrop(title="Test", excerpt="Excerpt")
        result = extract_body("<html><body></body></html>", item)
        assert result.ok
        assert result.method == "metadata"
        assert result.fallback_input["title"] == "Test"

    def test_empty_html_no_metadata(self):
        item = _make_raindrop()
        result = extract_body("<html><body></body></html>", item)
        assert not result.ok
