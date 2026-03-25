"""SHA256 コンテンツハッシュ。"""

import hashlib


def compute_content_hash(text: str) -> str:
    """テキストの SHA256 ハッシュを返す。"""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
