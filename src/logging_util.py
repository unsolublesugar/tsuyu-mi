"""ロガーセットアップ。rich ベースの見やすい出力。"""

import logging

from rich.logging import RichHandler


def setup_logger(level: str = "INFO") -> logging.Logger:
    """アプリケーションロガーを設定して返す。"""
    logger = logging.getLogger("raindrop_summarizer")

    if logger.handlers:
        return logger

    handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        show_path=False,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    return logger
