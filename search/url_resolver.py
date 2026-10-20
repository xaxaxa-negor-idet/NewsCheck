# -*- coding: utf-8 -*-
"""Resolve Google News redirect URLs to real article URLs."""
from __future__ import annotations

import re


def resolve_google_news_url(url: str) -> str:
    """Convert news.google.com redirect to real article URL if possible."""
    if "news.google.com/rss/articles/" not in url:
        return url

    match = re.search(r"articles/([A-Za-z0-9_-]+)", url)
    if not match:
        return url

    encoded = match.group(1)
    try:
        import base64
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += "=" * padding
        decoded = base64.urlsafe_b64decode(encoded)
        text = decoded.decode("utf-8", errors="ignore")
        url_match = re.search(r"https?://[^\s\x00-\x1f]+", text)
        if url_match:
            return url_match.group(0)
    except Exception:
        pass
    return url
