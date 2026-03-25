"""Raindrop.io API クライアント。"""

import json
import logging
from pathlib import Path

import httpx

from src.config import Config
from src.models import RaindropItem

logger = logging.getLogger("raindrop_summarizer")

API_BASE = "https://api.raindrop.io/rest/v1"


class RaindropClient:
    """Raindrop.io API からコレクションの記事を取得する。"""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {config.raindrop_token}"},
            timeout=config.request_timeout_seconds,
        )

    def fetch_collection(self) -> list[RaindropItem]:
        """コレクションの全記事を取得する。ページネーション対応。"""
        collection_id = self.config.raindrop_collection_id
        all_items: list[dict] = []
        page = 0

        logger.info(f"Raindrop API: コレクション {collection_id} を取得開始")

        while True:
            url = f"{API_BASE}/raindrops/{collection_id}"
            params = {"perpage": 50, "sort": "-created", "page": page}

            try:
                response = self.client.get(url, params=params)
            except httpx.RequestError as e:
                logger.error(f"ネットワークエラー: {e}")
                break

            if response.status_code == 401:
                logger.error("認証エラー: RAINDROP_TOKEN が無効です")
                break
            if response.status_code == 429:
                logger.error("レートリミット超過")
                break
            if response.status_code >= 500:
                logger.error(f"サーバーエラー: {response.status_code}")
                break

            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            all_items.extend(items)
            logger.debug(f"ページ {page}: {len(items)} 件取得")
            page += 1

        logger.info(f"Raindrop API: 合計 {len(all_items)} 件取得")
        return [self._map_item(item) for item in all_items]

    def save_raw(self, items: list[dict] | None = None) -> Path:
        """生データを data/raw/latest_raindrops.json に保存する。"""
        raw_dir = Path(self.config.data_dir) / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        path = raw_dir / "latest_raindrops.json"

        if items is None:
            # fetch_collection を呼んで生データも保存
            collection_id = self.config.raindrop_collection_id
            all_items: list[dict] = []
            page = 0
            while True:
                url = f"{API_BASE}/raindrops/{collection_id}"
                params = {"perpage": 50, "sort": "-created", "page": page}
                response = self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                batch = data.get("items", [])
                if not batch:
                    break
                all_items.extend(batch)
                page += 1
            items = all_items

        path.write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"生データを保存: {path} ({len(items)} 件)")
        return path

    def fetch_and_save(self) -> list[RaindropItem]:
        """取得と生データ保存を一度に行う。"""
        collection_id = self.config.raindrop_collection_id
        all_raw: list[dict] = []
        page = 0

        logger.info(f"Raindrop API: コレクション {collection_id} を取得開始")

        while True:
            url = f"{API_BASE}/raindrops/{collection_id}"
            params = {"perpage": 50, "sort": "-created", "page": page}

            try:
                response = self.client.get(url, params=params)
            except httpx.RequestError as e:
                logger.error(f"ネットワークエラー: {e}")
                break

            if response.status_code == 401:
                logger.error("認証エラー: RAINDROP_TOKEN が無効です")
                break
            if response.status_code == 429:
                logger.error("レートリミット超過")
                break
            if response.status_code >= 500:
                logger.error(f"サーバーエラー: {response.status_code}")
                break

            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            all_raw.extend(items)
            logger.debug(f"ページ {page}: {len(items)} 件取得")
            page += 1

        logger.info(f"Raindrop API: 合計 {len(all_raw)} 件取得")

        # 生データ保存
        self.save_raw(all_raw)

        return [self._map_item(item) for item in all_raw]

    def close(self) -> None:
        """HTTP クライアントを閉じる。"""
        self.client.close()

    @staticmethod
    def _map_item(raw: dict) -> RaindropItem:
        """API レスポンスの 1 件を RaindropItem にマッピングする。"""
        collection = raw.get("collection", {})
        return RaindropItem(
            raindrop_id=raw["_id"],
            collection_id=collection.get("$id", 0),
            title=raw.get("title", ""),
            url=raw.get("link", ""),
            domain=raw.get("domain", ""),
            created_at=raw.get("created", ""),
            tags=raw.get("tags", []),
            excerpt=raw.get("excerpt", ""),
            type=raw.get("type", "link"),
            cover=raw.get("cover", ""),
            note=raw.get("note", ""),
        )
