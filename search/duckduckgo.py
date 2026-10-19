"""DuckDuckGo HTML search provider: free, no API key required."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qs, unquote, urlsplit

import requests
from bs4 import BeautifulSoup

from search.url import canonicalize_url

SEARCH_URL = "https://html.duckduckgo.com/html/"


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    snippet: str
    domain: str
    published_at: datetime | None


def search(query: str, session: requests.Session | None = None, max_results: int = 10) -> list[SearchResult]:
    requester = session or requests
    response = requester.post(
        SEARCH_URL,
        data={"q": query},
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsCheck/0.1"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for link in soup.select("a.result__a")[:max_results]:
        href = link.get("href", "")
        url = _extract_real_url(href)
        if not url:
            continue
        title = link.get_text(strip=True)
        domain = urlsplit(canonicalize_url(url)).netloc.lower()
        snippet_tag = link.find_parent("div", class_="result")
        snippet = ""
        if snippet_tag:
            snippet_node = snippet_tag.select_one(".result__snippet")
            snippet = snippet_node.get_text(strip=True) if snippet_node else ""
        results.append(SearchResult(url=url, title=title, snippet=snippet, domain=domain, published_at=None))
    return results


def _extract_real_url(href: str) -> str | None:
    if href.startswith("http"):
        return href
    if href.startswith("//duckduckgo.com/l/?"):
        parsed = urlsplit("https:" + href)
        params = parse_qs(parsed.query)
        target = params.get("uddg", [None])[0]
        return unquote(target) if target else None
    return None
