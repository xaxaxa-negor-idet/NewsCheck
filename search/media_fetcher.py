# -*- coding: utf-8 -*-
"""Fetch original media from t.me page with retries (VPN-resistant)."""
from __future__ import annotations

import re
import time

import requests
from bs4 import BeautifulSoup

_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsCheck/1.0"})


def _get(url: str, timeout: int = 30) -> requests.Response | None:
    for attempt in range(3):
        try:
            r = _session.get(url, timeout=timeout)
            if r.status_code == 200:
                return r
        except Exception:
            pass
        time.sleep(2 * (attempt + 1))
    return None


def _match_post(soup: BeautifulSoup, post_url: str) -> BeautifulSoup | None:
    target = post_url.rstrip("/").split("/")[-1]
    for msg in soup.select(".tgme_widget_message"):
        post_id = (msg.get("data-post") or "").split("/")[-1]
        if post_id == target:
            return msg
    # fallback: first message block
    msgs = soup.select(".tgme_widget_message")
    return msgs[0] if msgs else None


def fetch_fresh_media(post_url: str, timeout: int = 30) -> tuple[str | None, str]:
    """Fetch ORIGINAL media URL from live t.me post page. Returns (url, kind)."""
    if not post_url or "t.me" not in post_url:
        return None, "photo"
    embed_url = post_url.rstrip("/") + "?embed=1"
    r = _get(embed_url, timeout) or _get(post_url, timeout)
    if r is None:
        return None, "photo"
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        msg = _match_post(soup, post_url)
        if msg is None:
            return None, "photo"
        # video first
        for v in msg.select("video"):
            src = v.get("src", "")
            if src:
                if src.startswith("//"):
                    src = "https:" + src
                return src, "video"
        for s in msg.select("source"):
            src = s.get("src", "")
            if src and ".mp4" in src:
                if src.startswith("//"):
                    src = "https:" + src
                return src, "video"
        # photo: background-image styles
        for el in msg.find_all(style=True):
            style = el["style"]
            if "background-image" not in style:
                continue
            m = re.search(r"url\('([^']+)'\)", style)
            if m and "cdn" in m.group(1):
                url = m.group(1)
                if url.startswith("//"):
                    url = "https:" + url
                return url, "photo"
    except Exception:
        pass
    return None, "photo"
