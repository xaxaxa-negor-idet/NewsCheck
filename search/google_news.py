"""Google News RSS search provider: free, excellent Russian support."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import feedparser
import requests

from search.url import canonicalize_url


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    snippet: str
    domain: str
    published_at: datetime | None


def search(
    query: str,
    session: requests.Session | None = None,
    max_results: int = 10,
    language: str = "ru",
    country: str = "RU",
) -> list[SearchResult]:
    requester = session or requests
    response = requester.get(
        "https://news.google.com/rss/search",
        params={"q": query, "hl": language, "gl": country, "ceid": f"{country}:{language}"},
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 NewsCheck/0.1"},
    )
    response.raise_for_status()

    feed = feedparser.parse(response.content)
    results = []
    for entry in feed.entries[:max_results]:
        url = entry.get("link", "")
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        published_raw = entry.get("published", "")
        published = _parse_date(published_raw)

        # Google News links redirect; source is in <source> tag
        source_tag = entry.get("source", {})
        domain = source_tag.get("title", "") if isinstance(source_tag, dict) else str(source_tag)

        results.append(
            SearchResult(
                url=url,
                title=title,
                snippet=summary,
                domain=domain or "news.google.com",
                published_at=published,
            )
        )
    return results


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(value)
    except (ValueError, TypeError):
        return None
