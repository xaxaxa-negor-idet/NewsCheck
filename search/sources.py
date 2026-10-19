"""Source snapshot and independence rules: SPEC 8.3, 8.4, 17.5."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from search.url import canonicalize_url, url_hash

ROOT = Path(__file__).resolve().parent.parent


def domain_of(url: str) -> str:
    return urlsplit(canonicalize_url(url)).netloc.lower()


@dataclass(frozen=True)
class SourceRecord:
    id: int
    domain: str
    published_at: datetime | None
    refers_to_source_id: int | None
    is_primary: bool


def classify_independence(sources: list[SourceRecord]) -> dict[int, bool]:
    """A source is independent when it is primary or a secondary source
    that does not reference an already counted primary source."""
    primary_domains = {source.domain for source in sources if source.is_primary}
    independent = {}
    for source in sources:
        if source.is_primary:
            independent[source.id] = True
        elif source.refers_to_source_id is None and source.domain not in primary_domains:
            independent[source.id] = True
        else:
            independent[source.id] = False
    return independent


def save_source(conn: sqlite3.Connection, url: str, title: str, content: str, published_at: datetime | None, source_name: str | None = None) -> int:
    canonical = canonicalize_url(url)
    digest = url_hash(url)
    existing = conn.execute("SELECT source_id FROM source_dedup WHERE url_hash=?", (digest,)).fetchone()
    if existing:
        return int(existing[0])

    domain = domain_of(url)
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cursor = conn.execute(
        "INSERT INTO sources (canonical_url, url, title, source_name, domain, published_at, retrieved_at, content) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (canonical, url, title, source_name, domain, published_at.isoformat() if published_at else None, retrieved_at, content),
    )
    source_id = int(cursor.lastrowid)
    conn.execute("INSERT INTO source_dedup (url_hash, source_id) VALUES (?, ?)", (digest, source_id))
    return source_id
