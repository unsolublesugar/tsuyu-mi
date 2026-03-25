"""CLI エントリポイント。全モジュールを統合するオーケストレーション層。"""

import logging
import time
import warnings

# requests の RequestsDependencyWarning を抑制
warnings.filterwarnings("ignore", message="urllib3.*doesn't match a supported version")

import click
from rich.console import Console
from rich.table import Table

from src.article_repository import ArticleRepository
from src.config import Config
from src.content_extractor import extract_body
from src.content_fetcher import FetchResult, fetch_url, should_skip_url
from src.html_builder import HtmlBuilder
from src.logging_util import setup_logger
from src.models import (
    ArticleState,
    ContentType,
    ProcessedArticle,
    SummaryInputType,
)
from src.raindrop_client import RaindropClient
from src.state_store import StateStore
from src.summarizer import (
    create_provider,
    summarize_fallback,
    summarize_fulltext,
)
from src.utils.hashing import compute_content_hash
from src.utils.text import is_video_content
from src.utils.time import format_display, now_utc, to_iso

console = Console()


@click.group()
def cli() -> None:
    """Raindrop Collection Summarizer"""
    pass


@cli.command()
@click.option("--dry-run", is_flag=True, help="実際の処理は行わず、対象記事を表示")
@click.option("--verbose", is_flag=True, help="詳細ログ出力")
def run(dry_run: bool, verbose: bool) -> None:
    """フルパイプラインを実行する。"""
    config = Config()
    setup_logger("DEBUG" if verbose else config.log_level)
    logger = logging.getLogger("raindrop_summarizer")

    errors = config.validate_required()
    if errors:
        console.print(f"[red]未設定の環境変数: {', '.join(errors)}[/red]")
        raise SystemExit(1)

    # 1. Raindrop 取得
    console.print("[bold]1/4 Raindrop API から取得中...[/bold]")
    client = RaindropClient(config)
    try:
        raindrops = client.fetch_and_save()
    finally:
        client.close()
    console.print(f"  取得: {len(raindrops)} 件")

    # 2. 差分検出
    console.print("[bold]2/4 差分検出中...[/bold]")
    state = StateStore(config.state_dir)
    targets = state.get_new_articles(raindrops, config.max_summarize_per_run)
    console.print(f"  新規: {len(targets)} 件")

    if dry_run:
        _print_targets(targets)
        return

    if not targets:
        console.print("[green]新規記事なし。終了します。[/green]")
        state.mark_run_completed()
        state.save()
        return

    # 3. 各記事を処理
    console.print(f"[bold]3/4 記事を処理中... (最大 {len(targets)} 件)[/bold]")
    provider = create_provider(config)
    repo = ArticleRepository(config.data_dir)
    stats = {"summarized": 0, "skipped": 0, "failed": 0}

    for i, raindrop in enumerate(targets, 1):
        console.print(f"  [{i}/{len(targets)}] {raindrop.title[:50]}...")
        try:
            article = _process_article(raindrop, config, provider, state, repo, logger)
            if article and article.summary_3lines:
                stats["summarized"] += 1
            else:
                stats["skipped"] += 1
        except Exception as e:
            logger.error(f"記事処理エラー ({raindrop.raindrop_id}): {e}")
            state.update_status(raindrop.raindrop_id, ArticleState.failed, reason=str(e))
            stats["failed"] += 1

        # レートリミット対策: 記事間に 2 秒待機
        if i < len(targets):
            time.sleep(2)

    state.mark_run_completed()
    state.save()

    # 4. HTML 生成
    console.print("[bold]4/4 HTML を生成中...[/bold]")
    _build_html(config, repo, state)

    _print_summary(stats, len(targets))


@cli.command("fetch-only")
@click.option("--verbose", is_flag=True)
def fetch_only(verbose: bool) -> None:
    """Raindrop 取得と生データ保存のみ。"""
    config = Config()
    setup_logger("DEBUG" if verbose else config.log_level)

    errors = config.validate_required()
    if errors and "RAINDROP_TOKEN" in errors:
        console.print("[red]RAINDROP_TOKEN が未設定です[/red]")
        raise SystemExit(1)

    client = RaindropClient(config)
    try:
        raindrops = client.fetch_and_save()
    finally:
        client.close()

    console.print(f"[green]取得完了: {len(raindrops)} 件[/green]")


@cli.command("build-html")
def build_html() -> None:
    """保存済み JSON から HTML を再生成する。"""
    config = Config()
    setup_logger(config.log_level)

    repo = ArticleRepository(config.data_dir)
    state = StateStore(config.state_dir)
    path = _build_html(config, repo, state)
    console.print(f"[green]HTML 生成完了: {path}[/green]")


@cli.command()
@click.option("--id", "raindrop_id", required=True, type=int, help="再処理する記事 ID")
@click.option("--verbose", is_flag=True)
def reprocess(raindrop_id: int, verbose: bool) -> None:
    """特定記事を再処理する。"""
    config = Config()
    setup_logger("DEBUG" if verbose else config.log_level)
    logger = logging.getLogger("raindrop_summarizer")

    errors = config.validate_required()
    if errors:
        console.print(f"[red]未設定の環境変数: {', '.join(errors)}[/red]")
        raise SystemExit(1)

    state = StateStore(config.state_dir)
    state.remove_entry(raindrop_id)

    # Raindrop から再取得して対象を見つける
    client = RaindropClient(config)
    try:
        raindrops = client.fetch_collection()
    finally:
        client.close()

    target = next((r for r in raindrops if r.raindrop_id == raindrop_id), None)
    if not target:
        console.print(f"[red]記事 ID {raindrop_id} が見つかりません[/red]")
        raise SystemExit(1)

    provider = create_provider(config)
    repo = ArticleRepository(config.data_dir)
    article = _process_article(target, config, provider, state, repo, logger)
    state.save()

    if article and article.summary_3lines:
        console.print(f"[green]再処理完了: {article.title}[/green]")
        _build_html(config, repo, state)
    else:
        console.print("[yellow]再処理しましたが要約は生成されませんでした[/yellow]")


@cli.command("reprocess-failed")
@click.option("--verbose", is_flag=True)
def reprocess_failed(verbose: bool) -> None:
    """失敗記事を一括再試行する。"""
    config = Config()
    setup_logger("DEBUG" if verbose else config.log_level)
    logger = logging.getLogger("raindrop_summarizer")

    errors = config.validate_required()
    if errors:
        console.print(f"[red]未設定の環境変数: {', '.join(errors)}[/red]")
        raise SystemExit(1)

    state = StateStore(config.state_dir)
    failed_ids = state.get_failed_ids()

    if not failed_ids:
        console.print("[green]失敗記事はありません[/green]")
        return

    console.print(f"失敗記事: {len(failed_ids)} 件を再処理します")

    # failed エントリを削除
    for rid in failed_ids:
        state.remove_entry(rid)

    client = RaindropClient(config)
    try:
        raindrops = client.fetch_collection()
    finally:
        client.close()

    provider = create_provider(config)
    repo = ArticleRepository(config.data_dir)
    stats = {"summarized": 0, "skipped": 0, "failed": 0}

    for rid in failed_ids:
        target = next((r for r in raindrops if str(r.raindrop_id) == rid), None)
        if not target:
            logger.warning(f"記事 ID {rid} が見つかりません")
            continue
        try:
            article = _process_article(target, config, provider, state, repo, logger)
            if article and article.summary_3lines:
                stats["summarized"] += 1
            else:
                stats["skipped"] += 1
        except Exception as e:
            logger.error(f"再処理エラー ({rid}): {e}")
            state.update_status(rid, ArticleState.failed, reason=str(e))
            stats["failed"] += 1

    state.save()
    _build_html(config, repo, state)
    _print_summary(stats, len(failed_ids))


# --- 内部関数 ---


def _process_article(
    raindrop, config, provider, state, repo, logger,
) -> ProcessedArticle | None:
    """1 記事を処理する。fetch → extract → summarize → save。"""
    rid = raindrop.raindrop_id

    # 動画スキップ
    skip_reason = should_skip_url(raindrop.url, raindrop.type)
    if skip_reason:
        article = ProcessedArticle(
            raindrop_id=rid,
            collection_id=raindrop.collection_id,
            title=raindrop.title,
            url=raindrop.url,
            domain=raindrop.domain,
            created_at=raindrop.created_at,
            content_type=ContentType.video if "video" in skip_reason else ContentType.other,
            content_status=skip_reason,
        )
        repo.save(article)
        state.update_status(rid, ArticleState.skipped, reason=skip_reason)
        logger.info(f"スキップ ({skip_reason}): {raindrop.title}")
        return article

    # HTML 取得
    state.update_status(rid, ArticleState.fetched)
    fetch_result = fetch_url(raindrop.url, config)

    if not fetch_result.ok:
        article = ProcessedArticle(
            raindrop_id=rid,
            collection_id=raindrop.collection_id,
            title=raindrop.title,
            url=raindrop.url,
            domain=raindrop.domain,
            created_at=raindrop.created_at,
            fetch_status=fetch_result.error,
            content_status="fetch_failed",
        )
        repo.save(article)
        reason = f"fetch_failed: {fetch_result.error}"
        state.update_status(rid, ArticleState.skipped, reason=reason)
        logger.warning(f"取得失敗: {raindrop.title} - {fetch_result.error}")
        return article

    # 本文抽出
    extraction = extract_body(fetch_result.html, raindrop, fetch_result.og_description)

    now = now_utc()
    article = ProcessedArticle(
        raindrop_id=rid,
        collection_id=raindrop.collection_id,
        title=raindrop.title,
        url=raindrop.url,
        domain=raindrop.domain,
        created_at=raindrop.created_at,
        fetched_at=now,
        fetch_status="ok",
        extract_method=extraction.method,
        summary_input_type=extraction.summary_input_type,
    )

    if extraction.ok and extraction.text:
        article.content_status = "ok"
        article.content_chars = len(extraction.text)
        article.content_hash = compute_content_hash(extraction.text)
        state.update_status(rid, ArticleState.extracted, content_hash=article.content_hash)
    elif extraction.ok and extraction.fallback_input:
        article.content_status = "fallback"
        state.update_status(rid, ArticleState.fallback_ready)
    else:
        article.content_status = "extract_failed"
        repo.save(article)
        state.update_status(rid, ArticleState.skipped, reason="extract_failed")
        logger.warning(f"抽出失敗: {raindrop.title}")
        return article

    # AI 要約
    if extraction.text:
        result = summarize_fulltext(
            provider, extraction.text,
            title=raindrop.title, url=raindrop.url, domain=raindrop.domain,
        )
    else:
        result = summarize_fallback(provider, extraction.fallback_input)

    if result:
        article.topic = result.topic
        article.summary_3lines = result.summary_3lines
        article.priority = result.priority
        article.read_now_reason = result.read_now_reason
        article.defer_reason = result.defer_reason
        article.drop_candidate = result.drop_candidate
        article.drop_reason = result.drop_reason
        article.keywords = result.keywords
        article.model_provider = config.llm_provider
        article.model_name = config.llm_model
        article.summarized_at = now_utc()
        state.update_status(rid, ArticleState.summarized, content_hash=article.content_hash)
        logger.info(f"要約完了: {raindrop.title}")
    else:
        article.content_status = "llm_failed"
        state.update_status(rid, ArticleState.failed, reason="llm_failed")
        logger.error(f"要約失敗: {raindrop.title}")

    repo.save(article)
    return article


def _build_html(config: Config, repo: ArticleRepository, state: StateStore):
    """HTML を生成する。"""
    articles = repo.list_all()
    last_run = format_display(state.index.last_run_at) if state.index.last_run_at else ""
    builder = HtmlBuilder(config.output_dir)
    return builder.build(articles, last_run_at=last_run)


def _print_targets(targets) -> None:
    """dry-run 時の対象記事表示。"""
    table = Table(title="処理対象記事")
    table.add_column("ID", style="dim")
    table.add_column("タイトル")
    table.add_column("ドメイン")
    for t in targets:
        table.add_row(str(t.raindrop_id), t.title[:60], t.domain)
    console.print(table)


def _print_summary(stats: dict, total: int) -> None:
    """処理結果サマリーを表示する。"""
    console.print()
    console.print("[bold]処理結果:[/bold]")
    console.print(f"  対象: {total} 件")
    console.print(f"  要約: [green]{stats['summarized']}[/green] 件")
    console.print(f"  スキップ: [yellow]{stats['skipped']}[/yellow] 件")
    console.print(f"  失敗: [red]{stats['failed']}[/red] 件")


if __name__ == "__main__":
    cli()
