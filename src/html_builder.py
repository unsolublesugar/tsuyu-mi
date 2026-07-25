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

DEFAULT_SITE_URL = "https://unsolublesugar.github.io/tsuyu-mi/"
SITE_TITLE = "Tsuyu-mi"
SITE_DESCRIPTION = (
    "Raindrop.io に溜めた「あとで読む」記事を AI が 3 行要約し、"
    "今読む / 後回し / 捨てる の優先度付きで一覧化する自動更新ダッシュボード。"
)

_INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def _render_inline_code(text: str) -> Markup:
    """テキスト中の `code` をインラインコード表示用の <code> タグに変換する。"""
    escaped = escape(text)
    result = _INLINE_CODE_RE.sub(r"<code>\1</code>", str(escaped))
    return Markup(result)


class HtmlBuilder:
    """記事一覧の HTML を生成する。"""

    def __init__(self, output_dir: str = "docs", site_url: str = DEFAULT_SITE_URL) -> None:
        self.output_dir = Path(output_dir)
        # og:url / og:image は絶対 URL が必須。末尾スラッシュを正規化しておく
        self.site_url = (site_url or DEFAULT_SITE_URL).rstrip("/") + "/"
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
            site_url=self.site_url,
            site_title=SITE_TITLE,
            site_description=SITE_DESCRIPTION,
            og_image_url=f"{self.site_url}og.png",
        )

        path = self.output_dir / "index.html"
        path.write_text(html, encoding="utf-8")
        logger.info(f"HTML を生成: {path} (要約 {len(summarized)} 件, スキップ {len(skipped)} 件)")
        return path
