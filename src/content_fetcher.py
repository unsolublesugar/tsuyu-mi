"""URL から HTML を取得する。"""

import logging
import re

import httpx

from src.config import Config
from src.utils.text import is_video_content

logger = logging.getLogger("raindrop_summarizer")


class FetchResult:
    """HTML 取得結果。"""

    def __init__(
        self,
        html: str = "",
        ok: bool = False,
        error: str = "",
        og_description: str = "",
    ) -> None:
        self.html = html
        self.ok = ok
        self.error = error
        self.og_description = og_description


def fetch_url(url: str, config: Config) -> FetchResult:
    """URL から HTML を取得する。動画 URL はスキップ。"""
    try:
        with httpx.Client(
            timeout=config.request_timeout_seconds,
            headers={"User-Agent": config.user_agent},
            follow_redirects=True,
            max_redirects=10,
        ) as client:
            response = client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return FetchResult(error=f"非 HTML コンテンツ: {content_type}")

            html = _decode_response(response)
            og_desc = _extract_og_description(html)

            return FetchResult(html=html, ok=True, og_description=og_desc)

    except httpx.TimeoutException:
        return FetchResult(error="タイムアウト")
    except httpx.HTTPStatusError as e:
        return FetchResult(error=f"HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        return FetchResult(error=f"リクエストエラー: {e}")
    except Exception as e:
        return FetchResult(error=f"予期しないエラー: {e}")


def _decode_response(response: httpx.Response) -> str:
    """レスポンスを適切なエンコーディングでデコードする。"""
    # Content-Type ヘッダーに charset があればそれを使う
    content_type = response.headers.get("content-type", "")
    ct_match = re.search(r"charset=([^\s;]+)", content_type, re.IGNORECASE)
    if ct_match:
        encoding = ct_match.group(1).strip().strip("'\"")
        try:
            return response.content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            pass

    # HTML 内の meta charset を探す
    raw = response.content
    meta_match = re.search(rb'<meta[^>]+charset=["\']?([^"\'\s;>]+)', raw[:4096], re.IGNORECASE)
    if meta_match:
        encoding = meta_match.group(1).decode("ascii", errors="ignore")
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            pass

    # デフォルト: httpx の判定に任せる
    return response.text


def should_skip_url(url: str, raindrop_type: str) -> str | None:
    """スキップすべき URL の理由を返す。スキップ不要なら None。"""
    if is_video_content(url, raindrop_type):
        return "unsupported_video"
    return None


def is_x_url(url: str) -> bool:
    """X（Twitter）の URL かどうかを判定する。"""
    from urllib.parse import urlparse

    try:
        host = urlparse(url).hostname or ""
        return host in ("x.com", "www.x.com", "twitter.com", "www.twitter.com")
    except Exception:
        return False


def fetch_x_post(url: str) -> dict | None:
    """vxtwitter API で X ポストの情報を取得する。"""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        # /user/status/id のパスから user と id を抽出
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 3 or parts[1] != "status":
            return None

        user = parts[0]
        status_id = parts[2]
        api_url = f"https://api.vxtwitter.com/{user}/status/{status_id}"
        resp = httpx.get(api_url, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"vxtwitter API エラー: {resp.status_code}")
            return None

        data = resp.json()
        result: dict = {
            "user_name": data.get("user_name", ""),
            "text": data.get("text", ""),
        }

        # 記事形式ポストの場合
        article = data.get("article")
        if isinstance(article, dict):
            result["article_title"] = article.get("title", "")
            result["article_preview"] = article.get("preview_text", "")

        return result
    except Exception as e:
        logger.warning(f"X ポスト取得失敗: {e}")
        return None


def _extract_og_description(html: str) -> str:
    """HTML から og:description を正規表現で抽出する。"""
    match = re.search(
        r'<meta\s+[^>]*property=["\']og:description["\']\s+[^>]*content=["\']([^"\']*)["\']',
        html,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    # content が先に来るパターン
    match = re.search(
        r'<meta\s+[^>]*content=["\']([^"\']*?)["\']\s+[^>]*property=["\']og:description["\']',
        html,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    return ""
