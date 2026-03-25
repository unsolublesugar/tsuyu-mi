"""テキスト処理ユーティリティ。"""

import re

VIDEO_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "vimeo.com",
    "www.vimeo.com",
    "nicovideo.jp",
    "www.nicovideo.jp",
    "nico.ms",
    "dailymotion.com",
    "www.dailymotion.com",
    "twitch.tv",
    "www.twitch.tv",
}


def is_video_url(url: str) -> bool:
    """URL が動画サイトかどうかを判定する。"""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.hostname or ""
        return domain in VIDEO_DOMAINS
    except Exception:
        return False


def is_video_content(url: str, raindrop_type: str) -> bool:
    """Raindrop type フィールドと URL の両方で動画判定する。"""
    if raindrop_type == "video":
        return True
    return is_video_url(url)


def clean_text(text: str) -> str:
    """テキストの余分な空白・改行を正規化する。"""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def count_chars(text: str) -> int:
    """テキストの文字数を返す（空白除外）。"""
    return len(text.replace(" ", "").replace("\n", ""))
