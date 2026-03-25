"""HTML 出力。Jinja2 テンプレートで docs/index.html を生成する。"""

import logging
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape

from src.models import Priority, ProcessedArticle
from src.utils.time import format_display

logger = logging.getLogger("raindrop_summarizer")

TEMPLATE_DIR = Path(__file__).parent / "templates"

_INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def _render_inline_code(text: str) -> Markup:
    """テキスト中の `code` をインラインコード表示用の <code> タグに変換する。"""
    escaped = escape(text)
    result = _INLINE_CODE_RE.sub(r"<code>\1</code>", str(escaped))
    return Markup(result)


class HtmlBuilder:
    """記事一覧の HTML を生成する。"""

    def __init__(self, output_dir: str = "docs") -> None:
        self.output_dir = Path(output_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )
        self.env.filters["inline_code"] = _render_inline_code

    def build(self, articles: list[ProcessedArticle], last_run_at: str = "") -> Path:
        """記事一覧 HTML を生成する。"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 要約済みとスキップ/失敗を分離
        summarized = [a for a in articles if a.summary_3lines]
        skipped = [a for a in articles if not a.summary_3lines]

        # ソート: priority (high→medium→low) → created_at 新しい順
        priority_order = {Priority.high: 0, Priority.medium: 1, Priority.low: 2}
        summarized.sort(key=lambda a: (priority_order.get(a.priority, 1), -a.created_at.timestamp()))

        template = self.env.get_template("index.html")
        html = template.render(
            articles=summarized,
            skipped=skipped,
            total=len(articles),
            summarized_count=len(summarized),
            skipped_count=len(skipped),
            last_run_at=last_run_at,
            format_display=format_display,
            Priority=Priority,
        )

        path = self.output_dir / "index.html"
        path.write_text(html, encoding="utf-8")
        logger.info(f"HTML を生成: {path} (要約 {len(summarized)} 件, スキップ {len(skipped)} 件)")
        return path
