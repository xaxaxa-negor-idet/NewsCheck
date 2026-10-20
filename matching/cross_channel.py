# -*- coding: utf-8 -*-
"""Cross-channel source search: find the same event in other monitored channels."""
from __future__ import annotations

import re
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
    conn = _connect(db_path)
    try:
        # Extract strong signals: numbers, capitalized names, unique nouns
        keywords = _extract_keywords(title)
        numbers = _extract_numbers(title)
        proper_nouns = _extract_proper_nouns(title)

        if not keywords and not numbers:
            return []

        rows = conn.execute(
            """SELECT m.id, m.original_text, m.source_url, m.published_at,
                      c.id AS channel_id, c.username, c.name
               FROM messages m
               JOIN channels c ON c.id = m.channel_id
               WHERE m.channel_id != ? AND m.id != ?
                 AND m.processing_status != 'IGNORED'
                 AND length(m.original_text) > 40
                 AND m.published_at > datetime('now', '-3 days')
               ORDER BY m.id DESC LIMIT 300""",
            (current_channel_id, current_message_id),
        ).fetchall()

        matches = []
        for row in rows:
            text = row["original_text"]
            # Must share at least one number OR proper noun (strong signal)
            strong_overlap = False
            for num in numbers:
                if num in text:
                    strong_overlap = True
                    break
            if not strong_overlap:
                for noun in proper_nouns:
                    if noun.lower() in text.lower():
                        strong_overlap = True
                        break
            if not strong_overlap:
                continue

            # High keyword threshold to avoid common-word matches
            similarity = _similarity(keywords, text)
            if similarity >= 0.5:
                matches.append(
                    ChannelMatch(
                        source_id=row["id"],
                        channel_id=row["channel_id"],
                        channel_username=row["username"],
                        channel_name=row["name"],
                        message_id=row["id"],
                        message_text=text,
                        source_url=row["source_url"] or "",
                        published_at=row["published_at"],
                        similarity=similarity,
                    )
                )

        matches.sort(key=lambda m: m.similarity, reverse=True)
        return matches[:limit]
    finally:
        conn.close()


STOP_WORDS = {
    "в", "на", "с", "и", "по", "из", "у", "к", "за", "от", "до", "о", "об",
    "что", "это", "как", "для", "при", "про", "его", "её", "их", "они",
    "был", "была", "было", "будет", "стал", "стала", "есть", "начали",
    "год", "года", "лет", "день", "дня", "время", "больше", "меньше",
    "стали", "стать", "тратить", "тратят", "пишет", "сообщает", "заявил",
}


def _extract_keywords(text: str) -> list[str]:
    words = [w.strip(".,!?«»\"'()[]{}:;").lower() for w in text.split()]
    keywords = [w for w in words if len(w) >= 4 and w not in STOP_WORDS]
    return list(dict.fromkeys(keywords))[:12]


def _extract_numbers(text: str) -> list[str]:
    """Extract numbers as strong identity signals: $529, 21-летний, 2026."""
    return re.findall(r"\d+[\d\-.,]*", text)[:6]


def _extract_proper_nouns(text: str) -> list[str]:
    """Extract capitalized multi-word names and known entities."""
    words = re.findall(r"\b[А-ЯЁA-Z][а-яёa-z]{2,}\b", text)
    return [w for w in words if w.lower() not in STOP_WORDS][:6]


def _similarity(keywords: list[str], text: str) -> float:
    if not keywords:
        return 0.0
    text_lower = text.lower()
    found = sum(1 for kw in keywords if kw in text_lower)
    return found / len(keywords)

