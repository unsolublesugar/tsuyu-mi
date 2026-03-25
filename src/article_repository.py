"""記事 JSON の永続化。data/articles/{raindrop_id}.json の CRUD。"""

import json
import logging
from pathlib import Path

from src.models import ProcessedArticle

logger = logging.getLogger("raindrop_summarizer")


class ArticleRepository:
    """data/articles/ 配下の記事 JSON を管理する。"""

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.articles_dir = self.data_dir / "articles"
        self.output_dir = self.data_dir / "output"

    def save(self, article: ProcessedArticle) -> Path:
        """記事を JSON ファイルとして保存する。"""
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        path = self.articles_dir / f"{article.raindrop_id}.json"
        data = article.model_dump(mode="json")
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.debug(f"記事を保存: {path}")
        return path

    def load(self, raindrop_id: int) -> ProcessedArticle | None:
        """記事を JSON ファイルから読み込む。存在しなければ None。"""
        path = self.articles_dir / f"{raindrop_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return ProcessedArticle.model_validate(data)
        except Exception:
            logger.warning(f"記事の読み込みに失敗: {path}")
            return None

    def list_all(self) -> list[ProcessedArticle]:
        """保存済みの全記事を読み込む。"""
        articles: list[ProcessedArticle] = []
        if not self.articles_dir.exists():
            return articles
        for path in sorted(self.articles_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                articles.append(ProcessedArticle.model_validate(data))
            except Exception:
                logger.warning(f"記事の読み込みをスキップ: {path}")
        return articles

    def export_all(self) -> Path:
        """全記事を統合した articles.json を出力する。"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        articles = self.list_all()
        data = [a.model_dump(mode="json") for a in articles]
        path = self.output_dir / "articles.json"
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"全記事を出力: {path} ({len(articles)} 件)")
        return path

    def delete(self, raindrop_id: int) -> bool:
        """記事ファイルを削除する。"""
        path = self.articles_dir / f"{raindrop_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False
