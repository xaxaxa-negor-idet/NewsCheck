# -*- coding: utf-8 -*-
"""Fetch original media from t.me page at publish time (always fresh URL with token)."""
from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup


def fetch_fresh_media(post_url: str, timeout: int = 30) -> tuple[str | None, str]:
    """Fetch the ORIGINAL media URL from the live t.me post page.

    CDN links in DB may be truncated/stale; the live page always has the
    current full URL with a valid token.

    Returns (url, kind) — kind is 'video' or 'photo'.
    """
    try:
        r = requests.get(post_url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 NewsCheck/1.0"})
        if r.status_code != 200:
            return None, "photo"
        soup = BeautifulSoup(r.text, "html.parser")

        for msg in soup.select(".tgme_widget_message"):
            post_id = msg.get("data-post", "")
            if not post_id or not post_url.rstrip("/").endswith(post_id):
                continue
            # video first (priority)
            for v in msg.select("video"):
                src = v.get("src", "")
                if src:
                    return src, "video"
            # photo via background-image
            for el in msg.find_all(style=True):
                style = el["style"]
                if "background-image" not in style:
                    continue
                m = re.search(r"url\('([^']+)'\)", style)
                if m and "cdn" in m.group(1):
                    return m.group(1), "photo"
            break
    except Exception:
        pass
    return None, "photo"
