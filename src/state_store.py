"""状態管理。state/index.json の読み書きと差分検出。"""

import json
import logging
from pathlib import Path

from src.models import ArticleState, RaindropItem, StateEntry, StateIndex
from src.utils.time import now_utc

logger = logging.getLogger("raindrop_summarizer")


class StateStore:
    """state/index.json を管理する。"""

    def __init__(self, state_dir: str = "state") -> None:
        self.state_dir = Path(state_dir)
        self.index_path = self.state_dir / "index.json"
        self.index = self._load()

    def _load(self) -> StateIndex:
        """index.json を読み込む。存在しなければ空の StateIndex を返す。"""
        if self.index_path.exists():
            try:
                data = json.loads(self.index_path.read_text(encoding="utf-8"))
                return StateIndex.model_validate(data)
            except Exception:
                logger.warning("state/index.json の読み込みに失敗。新規作成します。")
        return StateIndex()

    def save(self) -> None:
        """index.json を書き出す。"""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        data = self.index.model_dump(mode="json")
        self.index_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_new_articles(
        self, raindrops: list[RaindropItem], max_count: int = 30
    ) -> list[RaindropItem]:
        """未要約の記事を抽出する。created_at の新しい順、上限 max_count 件。"""
        summarized_ids = {
            rid for rid, entry in self.index.items.items()
            if entry.status == ArticleState.summarized
        }
        unsummarized = [r for r in raindrops if str(r.raindrop_id) not in summarized_ids]
        unsummarized.sort(key=lambda r: r.created_at, reverse=True)

        return unsummarized[:max_count]

    def get_failed_ids(self) -> list[str]:
        """status が failed のエントリの ID リストを返す。"""
        return [
            rid
            for rid, entry in self.index.items.items()
            if entry.status == ArticleState.failed
        ]

    def update_status(
        self,
        raindrop_id: int | str,
        status: ArticleState,
        content_hash: str | None = None,
        reason: str | None = None,
    ) -> None:
        """エントリの状態を更新する。"""
        rid = str(raindrop_id)
        entry = self.index.items.get(rid, StateEntry())
        entry.status = status
        entry.updated_at = now_utc()
        if content_hash is not None:
            entry.content_hash = content_hash
        if reason is not None:
            entry.reason = reason
        if status == ArticleState.summarized:
            entry.summarized_at = now_utc()
        self.index.items[rid] = entry

    def remove_entry(self, raindrop_id: int | str) -> None:
        """エントリを削除する（再処理用）。"""
        rid = str(raindrop_id)
        self.index.items.pop(rid, None)

    def mark_run_completed(self) -> None:
        """実行完了時刻を記録する。"""
        self.index.last_run_at = now_utc()

    def _set_entry(self, rid: str, status: ArticleState) -> None:
        """内部用。エントリを設定する。"""
        if rid not in self.index.items:
            self.index.items[rid] = StateEntry(status=status, updated_at=now_utc())
