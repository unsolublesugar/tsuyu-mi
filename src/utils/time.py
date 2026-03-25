"""時刻ユーティリティ。"""

from datetime import UTC, datetime, timezone

JST = timezone(offset=__import__("datetime").timedelta(hours=9))


def now_utc() -> datetime:
    """現在の UTC 時刻を返す。"""
    return datetime.now(UTC)


def to_iso(dt: datetime) -> str:
    """datetime を ISO 8601 文字列に変換する。"""
    return dt.isoformat()


def format_display(dt: datetime) -> str:
    """表示用の日時文字列を返す（JST、YYYY-MM-DD HH:MM）。"""
    jst_dt = dt.astimezone(JST) if dt.tzinfo else dt
    return jst_dt.strftime("%Y-%m-%d %H:%M")
