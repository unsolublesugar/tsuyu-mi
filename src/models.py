"""データモデル定義。全モジュール共通の型定義層。"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator

# 優先度スコアの各軸が取り得る範囲（src/priority.py の閾値と対応）
SCORE_MIN = 0
SCORE_MAX = 3


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


class PriorityScores(BaseModel):
    """優先度判定の軸スコア。各軸 SCORE_MIN〜SCORE_MAX の整数。

    LLM には「priority を直接選ばせる」のではなく各軸を採点させ、
    そこから `src/priority.py` が決定論的に Priority を導出する。
    high に偏るのを防ぎ、閾値をコード側で調整できるようにするための設計。
    """

    novelty: int = 0  # 新規性: 既知の再掲か、初出・独自の情報か
    relevance: int = 0  # 関心の近さ: 関心領域・実務にどれだけ近いか
    depth: int = 0  # 読む必要性: 3 行要約で足りるか、本文まで読む必要があるか
    actionability: int = 0  # 活用度: 実務・制作・発信にそのまま活かせるか

    @field_validator("novelty", "relevance", "depth", "actionability")
    @classmethod
    def _clamp_score(cls, value: int) -> int:
        """LLM が範囲外の値を返しても閾値計算が壊れないよう丸める。"""
        return max(SCORE_MIN, min(SCORE_MAX, value))

    @property
    def total(self) -> int:
        """4 軸の合計（0〜12）。"""
        return self.novelty + self.relevance + self.depth + self.actionability


class SummaryResult(BaseModel):
    """LLM が出力する要約結果の JSON スキーマ。"""

    topic: str = ""
    summary_3lines: list[str] = []
    # scores がある場合は priority / drop_candidate はそこから再計算される。
    # 未出力（旧プロンプト・パース失敗時）は LLM が返した priority をそのまま使う。
    scores: PriorityScores | None = None
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
    scores: PriorityScores | None = None
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
