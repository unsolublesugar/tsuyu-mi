"""html_builder.py のテスト。"""

import tempfile
from datetime import UTC, datetime

from src.html_builder import HtmlBuilder
from src.models import ContentType, Priority, ProcessedArticle, SummaryInputType


def _make_article(rid: int, priority: Priority = Priority.medium, **kwargs) -> ProcessedArticle:
    defaults = {
        "raindrop_id": rid,
        "collection_id": 100,
        "title": f"記事 {rid}",
        "url": f"https://example.com/{rid}",
        "domain": "example.com",
        "created_at": datetime(2026, 3, 25 - rid, tzinfo=UTC),
        "priority": priority,
        "topic": f"主題 {rid}",
        "summary_3lines": ["要約1", "要約2", "要約3"],
        "read_now_reason": "理由",
        "defer_reason": "後回し",
        "keywords": ["keyword"],
        "fetch_status": "ok",
        "summary_input_type": SummaryInputType.fulltext,
    }
    defaults.update(kwargs)
    return ProcessedArticle(**defaults)


class TestHtmlBuilder:
    def test_build_basic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            articles = [
                _make_article(1, Priority.high),
                _make_article(2, Priority.low),
            ]
            path = builder.build(articles)
            assert path.exists()
            html = path.read_text()
            assert "<!DOCTYPE html>" in html
            assert "記事 1" in html

    def test_sort_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            articles = [
                _make_article(1, Priority.low),
                _make_article(2, Priority.high),
                _make_article(3, Priority.medium),
            ]
            path = builder.build(articles)
            html = path.read_text()
            high_pos = html.index("記事 2")
            medium_pos = html.index("記事 3")
            low_pos = html.index("記事 1")
            assert high_pos < medium_pos < low_pos

    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            articles = [
                _make_article(1),
                ProcessedArticle(
                    raindrop_id=2, collection_id=100,
                    created_at=datetime(2026, 3, 20, tzinfo=UTC),
                    content_type=ContentType.video,
                    content_status="unsupported_video",
                ),
            ]
            path = builder.build(articles, last_run_at="2026-03-25 08:00")
            html = path.read_text()
            assert "2 件" in html
            assert "2026-03-25 08:00" in html

    def test_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            path = builder.build([])
            html = path.read_text()
            assert "要約済みの記事はありません" in html

    def test_drop_candidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            articles = [_make_article(1, drop_candidate=True, drop_reason="価値薄い")]
            path = builder.build(articles)
            html = path.read_text()
            assert "drop-candidate" in html
            assert "DROP" in html
            assert "価値薄い" in html
