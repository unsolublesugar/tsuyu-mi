"""utils のテスト。"""

from datetime import UTC, datetime

from src.utils.hashing import compute_content_hash
from src.utils.text import clean_text, count_chars, is_video_content, is_video_url
from src.utils.time import format_display, now_utc, to_iso


class TestHashing:
    def test_compute_content_hash(self):
        h = compute_content_hash("hello")
        assert h.startswith("sha256:")
        assert len(h) > 10

    def test_same_input_same_hash(self):
        h1 = compute_content_hash("test")
        h2 = compute_content_hash("test")
        assert h1 == h2

    def test_different_input_different_hash(self):
        h1 = compute_content_hash("a")
        h2 = compute_content_hash("b")
        assert h1 != h2


class TestText:
    def test_is_video_url_youtube(self):
        assert is_video_url("https://youtube.com/watch?v=abc") is True
        assert is_video_url("https://www.youtube.com/watch?v=abc") is True
        assert is_video_url("https://youtu.be/abc") is True

    def test_is_video_url_others(self):
        assert is_video_url("https://vimeo.com/123") is True
        assert is_video_url("https://nicovideo.jp/watch/sm123") is True
        assert is_video_url("https://twitch.tv/stream") is True

    def test_is_video_url_non_video(self):
        assert is_video_url("https://example.com") is False
        assert is_video_url("https://github.com") is False

    def test_is_video_url_invalid(self):
        assert is_video_url("") is False
        assert is_video_url("not-a-url") is False

    def test_is_video_content_by_type(self):
        assert is_video_content("https://example.com", "video") is True
        assert is_video_content("https://example.com", "link") is False

    def test_is_video_content_by_url(self):
        assert is_video_content("https://youtube.com/watch", "link") is True

    def test_clean_text(self):
        assert clean_text("  hello   world  ") == "hello world"
        assert clean_text("a\n\n\nb") == "a b"

    def test_count_chars(self):
        assert count_chars("hello") == 5
        assert count_chars("h e l l o") == 5
        assert count_chars("") == 0


class TestTime:
    def test_now_utc(self):
        dt = now_utc()
        assert dt.tzinfo is not None

    def test_to_iso(self):
        dt = datetime(2026, 3, 25, 8, 30, 0, tzinfo=UTC)
        iso = to_iso(dt)
        assert "2026-03-25" in iso

    def test_format_display_jst(self):
        dt = datetime(2026, 3, 25, 8, 30, 0, tzinfo=UTC)
        display = format_display(dt)
        assert display == "2026-03-25 17:30"  # UTC+9 = JST
