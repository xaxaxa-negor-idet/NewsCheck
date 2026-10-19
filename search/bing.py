"""Bing web search provider: free, no API key required."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

import requests
from bs4 import BeautifulSoup

from search.url import canonicalize_url

SEARCH_URL = "https://www.bing.com/search"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    snippet: str
    domain: str
    published_at: datetime | None


def search(query: str, session: requests.Session | None = None, max_results: int = 10) -> list[SearchResult]:
    requester = session or requests
    response = requester.get(
        SEARCH_URL,
        params={"q": query, "count": max_results},
        timeout=30,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "ru,en;q=0.9"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for item in soup.select("li.b_algo")[:max_results]:
        link = item.select_one("h2 a")
        if link is None:
            continue
        raw_url = link.get("href", "")
        url = _decode_bing_url(raw_url)
        if not url:
            continue
        title = link.get_text(strip=True)
        snippet_node = item.select_one(".b_caption p, .b_lineclamp2")
        snippet = snippet_node.get_text(strip=True) if snippet_node else ""
        domain = urlsplit(canonicalize_url(url)).netloc.lower()
        results.append(SearchResult(url=url, title=title, snippet=snippet, domain=domain, published_at=None))
    return results


def _decode_bing_url(href: str) -> str | None:
    if href.startswith("http") and "bing.com/ck/a" not in href:
        return href
    if "bing.com/ck/a" in href:
        parsed = urlsplit(href if href.startswith("http") else "https://" + href)
        params = parse_qs(parsed.query)
        encoded = params.get("u", [None])[0]
        if not encoded:
            return None
        # Bing uses base64 with 'a1' prefix
        payload = encoded[2:] if encoded.startswith("a1") else encoded
        try:
            # Add padding
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            decoded = base64.urlsafe_b64decode(payload).decode("utf-8")
            return decoded if decoded.startswith("http") else None
        except Exception:
            return None
    return None


