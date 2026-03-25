"""データモデル定義。全モジュール共通の型定義層。"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


# --- Enums ---


class ArticleState(str, Enum):
    pending = "pending"
    fetched = "fetched"
    extracted = "extracted"
    fallback_ready = "fallback_ready"
    summarized = "summarized"
    skipped = "skipped"
    failed = "failed"


class SkipReason(str, Enum):
    fetch_failed = "fetch_failed"
    extract_failed = "extract_failed"
    summary_input_unavailable = "summary_input_unavailable"
    unsupported_video = "unsupported_video"
    unsupported_non_html = "unsupported_non_html"
    llm_failed = "llm_failed"
    too_short = "too_short"


class ContentType(str, Enum):
    article = "article"
    video = "video"
    other = "other"


class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ManualStatus(str, Enum):
    untriaged = "untriaged"
    read = "read"
    keep = "keep"
    drop = "drop"


class SummaryInputType(str, Enum):
    fulltext = "fulltext"
    shorttext = "shorttext"
    metadata = "metadata"


# --- Raindrop API モデル ---


class RaindropItem(BaseModel):
    """Raindrop API レスポンスから抽出する内部モデル。"""

    raindrop_id: int
    collection_id: int
    title: str = ""
    url: str = ""
    domain: str = ""
    created_at: datetime
    tags: list[str] = []
    excerpt: str = ""
    type: str = "link"
    cover: str = ""
    note: str = ""


# --- LLM 出力モデル ---


class SummaryResult(BaseModel):
    """LLM が出力する要約結果の JSON スキーマ。"""

    topic: str = ""
    summary_3lines: list[str] = []
    priority: Priority = Priority.medium
    read_now_reason: str = ""
    defer_reason: str = ""
    drop_candidate: bool = False
    drop_reason: str = ""
    keywords: list[str] = []


# --- 処理済み記事モデル ---


class ProcessedArticle(BaseModel):
    """処理済み記事の正本データ。data/articles/{raindrop_id}.json に保存。"""

    raindrop_id: int
    collection_id: int
    title: str = ""
    url: str = ""
    domain: str = ""
    created_at: datetime
    fetched_at: datetime | None = None
    source_language: str = ""
    output_language: str = "ja"
    content_type: ContentType = ContentType.article
    content_status: str = ""
    fetch_status: str = ""
    extract_method: str = ""
    content_chars: int = 0
    content_hash: str = ""
    summary_input_type: SummaryInputType | None = None
    topic: str = ""
    summary_3lines: list[str] = []
    priority: Priority = Priority.medium
    read_now_reason: str = ""
    defer_reason: str = ""
    drop_candidate: bool = False
    drop_reason: str = ""
    keywords: list[str] = []
    model_provider: str = ""
    model_name: str = ""
    summarized_at: datetime | None = None
    manual_status: ManualStatus = ManualStatus.untriaged
    notes: str = ""


# --- 状態管理モデル ---


class StateEntry(BaseModel):
    """state/index.json の各エントリ。"""

    status: ArticleState = ArticleState.pending
    content_hash: str | None = None
    reason: str | None = None
    summarized_at: datetime | None = None
    updated_at: datetime | None = None


class StateIndex(BaseModel):
    """state/index.json 全体。"""

    last_run_at: datetime | None = None
    items: dict[str, StateEntry] = {}
