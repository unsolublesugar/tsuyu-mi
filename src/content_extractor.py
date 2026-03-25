"""本文抽出。trafilatura → readability-lxml → メタデータフォールバック。"""

import logging
from dataclasses import dataclass, field

import trafilatura
from readability import Document

from src.models import RaindropItem, SummaryInputType
from src.utils.text import clean_text, count_chars

logger = logging.getLogger("raindrop_summarizer")


@dataclass
class ExtractionResult:
    """本文抽出結果。"""

    text: str = ""
    method: str = ""
    summary_input_type: SummaryInputType | None = None
    ok: bool = False
    fallback_input: dict = field(default_factory=dict)


def extract_body(html: str, raindrop: RaindropItem, og_description: str = "") -> ExtractionResult:
    """HTML から本文を抽出する。フォールバックチェーン付き。"""

    # 1. trafilatura
    try:
        text = trafilatura.extract(html, include_comments=False, include_tables=True)
        if text and count_chars(text) >= 100:
            cleaned = clean_text(text)
            input_type = _classify_length(count_chars(cleaned))
            logger.debug(f"trafilatura で抽出成功: {count_chars(cleaned)} 文字")
            return ExtractionResult(
                text=cleaned,
                method="trafilatura",
                summary_input_type=input_type,
                ok=True,
            )
    except Exception as e:
        logger.debug(f"trafilatura 失敗: {e}")

    # 2. readability-lxml
    try:
        doc = Document(html)
        summary_html = doc.summary()
        # HTML タグを除去して本文テキストに
        text = trafilatura.extract(summary_html) or ""
        if not text:
            # trafilatura での再抽出も失敗したら簡易タグ除去
            import re

            text = re.sub(r"<[^>]+>", " ", summary_html)
        text = clean_text(text)
        if count_chars(text) >= 100:
            input_type = _classify_length(count_chars(text))
            logger.debug(f"readability で抽出成功: {count_chars(text)} 文字")
            return ExtractionResult(
                text=text,
                method="readability",
                summary_input_type=input_type,
                ok=True,
            )
    except Exception as e:
        logger.debug(f"readability 失敗: {e}")

    # 3. メタデータフォールバック
    fallback = _build_fallback_input(raindrop, og_description)
    if fallback:
        logger.debug("メタデータフォールバックを構成")
        return ExtractionResult(
            method="metadata",
            summary_input_type=SummaryInputType.metadata,
            ok=True,
            fallback_input=fallback,
        )

    # 4. すべて失敗
    logger.debug("本文抽出に完全に失敗")
    return ExtractionResult()


def _classify_length(chars: int) -> SummaryInputType:
    """文字数に基づいて要約入力タイプを分類する。"""
    if chars >= 1500:
        return SummaryInputType.fulltext
    if chars >= 500:
        return SummaryInputType.shorttext
    return SummaryInputType.metadata


def _build_fallback_input(raindrop: RaindropItem, og_description: str = "") -> dict:
    """簡易要約用の入力を構成する。"""
    parts: dict = {}

    if raindrop.title:
        parts["title"] = raindrop.title
    if raindrop.excerpt:
        parts["excerpt"] = raindrop.excerpt
    if og_description:
        parts["og_description"] = og_description
    if raindrop.url:
        parts["url"] = raindrop.url
    if raindrop.domain:
        parts["domain"] = raindrop.domain
    if raindrop.tags:
        parts["tags"] = raindrop.tags
    if raindrop.created_at:
        parts["created_at"] = raindrop.created_at.isoformat()

    # タイトルすらなければフォールバック不可
    if "title" not in parts and "excerpt" not in parts:
        return {}

    return parts
