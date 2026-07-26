"""html_builder.py のテスト。"""

import tempfile
from datetime import UTC, datetime

from markupsafe import Markup

from src.html_builder import DEFAULT_SITE_URL, HtmlBuilder, _render_inline_code
from src.models import (
    ContentType,
    Priority,
    PriorityScores,
    ProcessedArticle,
    SummaryInputType,
)


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


class TestRenderInlineCode:
    def test_backtick_to_code_tag(self):
        result = _render_inline_code("ツール `cmux` を紹介")
        assert "<code>cmux</code>" in result
        assert isinstance(result, Markup)

    def test_multiple_backticks(self):
        result = _render_inline_code("`Raycast` と `context7 CLI` の比較")
        assert "<code>Raycast</code>" in result
        assert "<code>context7 CLI</code>" in result

    def test_no_backticks(self):
        result = _render_inline_code("普通のテキスト")
        assert result == "普通のテキスト"

    def test_html_escaped(self):
        result = _render_inline_code("`<script>` タグ")
        assert "<script>" not in result
        assert "<code>&lt;script&gt;</code>" in result


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
            # ヘッダーの「N / M 件を表示」はカード（要約済み）件数が基準。
            # スキップ記事は別セクションで数えるため分母に含めない（2 件中 1 件が要約済み）。
            assert '<strong id="stats-count">1</strong>' in html
            assert '<span id="stats-total">1</span> 件を表示' in html
            assert "2026-03-25 08:00" in html
            # スキップ側は別セクションの件数として出る
            assert "スキップ・未処理 (1 件)" in html

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

    def test_ogp_meta_tags(self):
        """OGP / Twitter Card のメタタグが絶対 URL で出力される。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            path = builder.build([_make_article(1)])
            html = path.read_text()

            assert '<meta name="description"' in html
            assert '<meta property="og:type" content="website">' in html
            assert '<meta property="og:title" content="Tsuyu-mi">' in html
            assert f'<meta property="og:url" content="{DEFAULT_SITE_URL}">' in html
            assert f'<meta property="og:image" content="{DEFAULT_SITE_URL}og.png">' in html
            assert '<meta property="og:image:width" content="1200">' in html
            assert '<meta property="og:image:height" content="630">' in html
            assert '<meta name="twitter:card" content="summary_large_image">' in html
            assert f'<meta name="twitter:image" content="{DEFAULT_SITE_URL}og.png">' in html
            assert f'<link rel="canonical" href="{DEFAULT_SITE_URL}">' in html

    def test_favicon_links(self):
        """favicon 各種の link タグが出力される。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            html = builder.build([]).read_text()
            assert '<link rel="icon" type="image/svg+xml" href="favicon.svg">' in html
            assert '<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">' in html
            assert '<link rel="apple-touch-icon" href="apple-touch-icon.png">' in html

    def test_custom_site_url_normalized(self):
        """site_url を差し替えると OGP の絶対 URL に反映され、末尾スラッシュが正規化される。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir, site_url="https://example.com/mysite")
            html = builder.build([]).read_text()
            assert '<meta property="og:url" content="https://example.com/mysite/">' in html
            assert '<meta property="og:image" content="https://example.com/mysite/og.png">' in html
            assert DEFAULT_SITE_URL not in html

    def test_inline_code_in_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            articles = [_make_article(1, summary_3lines=["`cmux` はターミナルツール", "普通の行", "行3"])]
            path = builder.build(articles)
            html = path.read_text()
            assert "<code>cmux</code>" in html


class TestPriorityScoreDisplay:
    def test_renders_score_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            scores = PriorityScores(novelty=3, relevance=2, depth=2, actionability=1)
            html = builder.build([_make_article(1, scores=scores)]).read_text()
            # 合計スコアはスコアパネル内の 1 箇所のみ（SP でも 4 軸パラメータの見出しとして出す）
            assert "score-panel" in html
            assert "score-inline" not in html
            assert html.count("<strong>8</strong>") == 1

    def test_renders_four_axes_as_bars(self):
        """4 軸スコアは hover ではなくバー UI（.fill.sN）で常時表示される。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            scores = PriorityScores(novelty=3, relevance=2, depth=1, actionability=0)
            html = builder.build([_make_article(1, scores=scores)]).read_text()
            for label in ("新規性", "関心の近さ", "読む必要性", "活用度"):
                assert f'<span class="axis-label">{label}</span>' in html
            for level in ("s3", "s2", "s1", "s0"):
                assert f'<span class="fill {level}"></span>' in html

    def test_omits_score_when_absent(self):
        """scores を持たない旧データでもレンダリングできる。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            html = builder.build([_make_article(1)]).read_text()
            assert "score-panel" not in html
            assert "score-inline" not in html
            assert "axis-label" not in html


class TestPriorityFilter:
    def test_filter_tabs_rendered(self):
        """優先度フィルタは すべて/High/Medium/Low の 4 タブ、初期 active は high。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            html = builder.build([_make_article(1)]).read_text()
            for f in ("all", "high", "medium", "low"):
                assert f'data-filter="{f}"' in html
            assert '<button class="filter-btn active" data-filter="high">' in html
            # 件数バッジは app.js が埋める空要素
            assert html.count('<span class="tab-count"></span>') == 4

    def test_cards_carry_priority_dataset(self):
        """カードの data-priority が JS フィルタの対象になる。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            articles = [_make_article(1, Priority.high), _make_article(2, Priority.low)]
            html = builder.build(articles).read_text()
            assert 'data-priority="high"' in html
            assert 'data-priority="low"' in html


class TestReasonsToggle:
    def test_reasons_are_in_details_toggle(self):
        """判定理由は <details> の中に折りたたまれる。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = HtmlBuilder(output_dir=tmpdir)
            html = builder.build([_make_article(1)]).read_text()
            assert '<details class="reasons-toggle">' in html
            assert "<summary>判定理由</summary>" in html
            assert "今読む:" in html
            assert "後回し:" in html
