"""GDELT search provider: free news search fallback. SPEC 8.1."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import requests

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    snippet: str
    domain: str
    published_at: datetime | None


def search(query: str, session: requests.Session | None = None) -> list[SearchResult]:
    requester = session or requests
    response = requester.get(
        BASE_URL,
        params={"query": query, "mode": "artlist", "format": "json", "maxrecords": 10},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    articles = payload.get("articles", [])
    results = []
    for article in articles:
        url = article.get("url", "")
        if not url:
            continue
        date_raw = article.get("seendate", "")
        published = None
        if date_raw:
            try:
                published = datetime.strptime(date_raw, "%Y%m%dT%H%M%SZ")
            except ValueError:
                published = None
        results.append(
            SearchResult(
                url=url,
                title=article.get("title", ""),
                snippet=article.get("snippet", ""),
                domain=article.get("domain", ""),
                published_at=published,
            )
        )
    return results
