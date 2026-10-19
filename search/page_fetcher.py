"""Page fetcher: SPEC 8.3 — snapshot external article content."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

from search.url import canonicalize_url


@dataclass(frozen=True)
class PageSnapshot:
    url: str
    title: str
    text: str
    domain: str
    retrieved_at: datetime


def fetch_page(url: str, session: requests.Session | None = None, max_bytes: int = 2_000_000) -> PageSnapshot:
    requester = session or requests
    response = requester.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 NewsCheck/0.1"})
    response.raise_for_status()
    content = response.content[:max_bytes]

    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    text = " ".join(part.strip() for part in soup.get_text("\n").splitlines() if part.strip())
    return PageSnapshot(
        url=canonicalize_url(url),
        title=title,
        text=text,
        domain=urlsplit(canonicalize_url(url)).netloc.lower(),
        retrieved_at=datetime.now(timezone.utc),
    )
