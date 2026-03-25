"""state_store.py のテスト。"""

import tempfile
from datetime import UTC, datetime

from src.models import ArticleState, RaindropItem
from src.state_store import StateStore


def _make_raindrop(rid: int, days_ago: int = 0) -> RaindropItem:
    return RaindropItem(
        raindrop_id=rid,
        collection_id=100,
        created_at=datetime(2026, 3, 25 - days_ago, tzinfo=UTC),
    )


class TestStateStore:
    def test_empty_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(state_dir=tmpdir)
            assert store.index.items == {}
            assert store.index.last_run_at is None

    def test_get_new_articles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(state_dir=tmpdir)
            raindrops = [_make_raindrop(1, 5), _make_raindrop(2, 0), _make_raindrop(3, 3)]
            new = store.get_new_articles(raindrops, max_count=2)
            assert len(new) == 2
            assert new[0].raindrop_id == 2  # newest first
            assert new[1].raindrop_id == 3

    def test_overflow_becomes_pending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(state_dir=tmpdir)
            raindrops = [_make_raindrop(1, 5), _make_raindrop(2, 0), _make_raindrop(3, 3)]
            store.get_new_articles(raindrops, max_count=2)
            assert "1" in store.index.items
            assert store.index.items["1"].status == ArticleState.pending

    def test_skips_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(state_dir=tmpdir)
            store.update_status(1, ArticleState.summarized)
            raindrops = [_make_raindrop(1), _make_raindrop(2)]
            new = store.get_new_articles(raindrops, max_count=10)
            assert len(new) == 1
            assert new[0].raindrop_id == 2

    def test_update_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(state_dir=tmpdir)
            store.update_status(1, ArticleState.summarized, content_hash="sha256:abc")
            entry = store.index.items["1"]
            assert entry.status == ArticleState.summarized
            assert entry.content_hash == "sha256:abc"
            assert entry.summarized_at is not None

    def test_get_failed_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(state_dir=tmpdir)
            store.update_status(1, ArticleState.summarized)
            store.update_status(2, ArticleState.failed)
            store.update_status(3, ArticleState.failed)
            failed = store.get_failed_ids()
            assert set(failed) == {"2", "3"}

    def test_remove_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(state_dir=tmpdir)
            store.update_status(1, ArticleState.summarized)
            store.remove_entry(1)
            assert "1" not in store.index.items

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(state_dir=tmpdir)
            store.update_status(1, ArticleState.summarized)
            store.mark_run_completed()
            store.save()

            store2 = StateStore(state_dir=tmpdir)
            assert store2.index.last_run_at is not None
            assert "1" in store2.index.items
