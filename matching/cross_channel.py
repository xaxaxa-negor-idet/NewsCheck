"""Cross-channel source search: find the same event in other monitored channels."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ChannelMatch:
    source_id: int
    channel_id: int
    channel_username: str
    channel_name: str
    message_id: int
    message_text: str
    source_url: str
    published_at: str | None
    similarity: float


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def find_cross_channel_matches(
    current_message_id: int,
    current_channel_id: int,
    title: str,
    entities: list[str],
    db_path: str | None = None,
    limit: int = 10,
) -> list[ChannelMatch]:
    """Find similar messages in other channels (not the source channel)."""
    conn = _connect(db_path)
    try:
        keywords = _extract_keywords(title)
        if not keywords:
            return []

        placeholders = ",".join("?" * len(keywords))
        rows = conn.execute(
            f"""SELECT m.id, m.original_text, m.source_url, m.published_at,
                       c.id AS channel_id, c.username, c.name
                FROM messages m
                JOIN channels c ON c.id = m.channel_id
                WHERE m.channel_id != ? AND m.id != ?
                  AND m.processing_status != 'IGNORED'
                  AND length(m.original_text) > 40
                ORDER BY m.id DESC LIMIT 500""",
            (current_channel_id, current_message_id),
        ).fetchall()

        matches = []
        for row in rows:
            similarity = _similarity(keywords, row["original_text"])
            if similarity >= 0.25:
                matches.append(
                    ChannelMatch(
                        source_id=row["id"],
                        channel_id=row["channel_id"],
                        channel_username=row["username"],
                        channel_name=row["name"],
                        message_id=row["id"],
                        message_text=row["original_text"],
                        source_url=row["source_url"] or "",
                        published_at=row["published_at"],
                        similarity=similarity,
                    )
                )

        matches.sort(key=lambda m: m.similarity, reverse=True)
        return matches[:limit]
    finally:
        conn.close()


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from event title."""
    stop_words = {
        "в", "на", "с", "и", "по", "из", "у", "к", "за", "от", "до", "о", "об",
        "что", "это", "как", "для", "при", "про", "его", "её", "их", "они",
        "был", "была", "было", "будет", "стал", "стала", "есть",
        "год", "года", "лет", "день", "дня", "время",
    }
    words = [w.strip(".,!?«»\"'()[]{}:;").lower() for w in text.split()]
    keywords = [w for w in words if len(w) >= 3 and w not in stop_words]
    return list(dict.fromkeys(keywords))[:10]


def _similarity(keywords: list[str], text: str) -> float:
    """Calculate how many keywords appear in the text."""
    if not keywords:
        return 0.0
    text_lower = text.lower()
    found = sum(1 for kw in keywords if kw in text_lower)
    return found / len(keywords)

