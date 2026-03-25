"""article_repository.py のテスト。"""

import tempfile
from datetime import UTC, datetime

from src.article_repository import ArticleRepository
from src.models import ProcessedArticle


def _make_article(rid: int, title: str = "Test") -> ProcessedArticle:
    return ProcessedArticle(
        raindrop_id=rid,
        collection_id=100,
        title=title,
        created_at=datetime(2026, 3, 25, tzinfo=UTC),
    )


class TestArticleRepository:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ArticleRepository(data_dir=tmpdir)
            article = _make_article(1, "テスト記事")
            repo.save(article)

            loaded = repo.load(1)
            assert loaded is not None
            assert loaded.title == "テスト記事"

    def test_load_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ArticleRepository(data_dir=tmpdir)
            assert repo.load(999) is None

    def test_list_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ArticleRepository(data_dir=tmpdir)
            repo.save(_make_article(1, "A"))
            repo.save(_make_article(2, "B"))
            all_articles = repo.list_all()
            assert len(all_articles) == 2

    def test_list_all_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ArticleRepository(data_dir=tmpdir)
            assert repo.list_all() == []

    def test_export_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ArticleRepository(data_dir=tmpdir)
            repo.save(_make_article(1))
            path = repo.export_all()
            assert path.exists()

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ArticleRepository(data_dir=tmpdir)
            repo.save(_make_article(1))
            assert repo.delete(1) is True
            assert repo.delete(1) is False
            assert repo.load(1) is None
