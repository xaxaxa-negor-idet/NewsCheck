"""Collector: SPEC 3.1-3.3 — dedup, versions, availability."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from sources.telegram_web import PollResult, SourceMessage

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class CollectorOutcome:
    inserted: int
    duplicates: int
    updated: int


def content_hash(text: str, media: Iterable[str]) -> str:
    payload = json.dumps({"text": text, "media": list(media)}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_channel(username: str, name: str, category: str, db_path: str | None = None) -> int:
    conn = _connect(db_path)
    try:
        row = conn.execute("SELECT id FROM channels WHERE username=?", (username,)).fetchone()
        if row:
            return int(row["id"])
        cursor = conn.execute(
            "INSERT INTO channels (name, username, url, category) VALUES (?, ?, ?, ?)",
            (name, username, f"https://t.me/{username}", category),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def ingest_poll_result(poll: PollResult, channel_id: int, db_path: str | None = None) -> CollectorOutcome:
    if poll.kind == "UNAVAILABLE":
        raise ValueError(f"UNAVAILABLE must be handled by queue retry: {poll.reason}")

    inserted = 0
    duplicates = 0
    updated = 0
    conn = _connect(db_path)
    try:
        for message in poll.messages:
            digest = content_hash(message.text, message.media)
            existing = conn.execute(
                "SELECT id, content_hash, edited_at FROM messages WHERE channel_id=? AND source_message_id=?",
                (channel_id, message.source_message_id),
            ).fetchone()

            if existing is None:
                cursor = conn.execute(
                    "INSERT INTO messages "
                    "(channel_id, source_message_id, original_text, media, source_url, published_at, content_hash, processing_status, availability, edited_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, 'NEW', 'AVAILABLE', ?)",
                    (
                        channel_id,
                        message.source_message_id,
                        message.text,
                        json.dumps(message.media, ensure_ascii=False),
                        message.source_url,
                        message.published_at.isoformat() if message.published_at else None,
                        digest,
                        message.edited_at.isoformat() if message.edited_at else None,
                    ),
                )
                message_id = int(cursor.lastrowid)
                conn.execute(
                    "INSERT INTO message_versions (message_id, text, content_hash) VALUES (?, ?, ?)",
                    (message_id, message.text, digest),
                )
                inserted += 1
                continue

            if existing["content_hash"] == digest:
                duplicates += 1
                continue

            message_id = int(existing["id"])
            conn.execute(
                "UPDATE messages SET original_text=?, media=?, content_hash=?, availability='EDITED', edited_at=?, processing_status='NEW' WHERE id=?",
                (
                    message.text,
                    json.dumps(message.media, ensure_ascii=False),
                    digest,
                    message.edited_at.isoformat() if message.edited_at else _now_iso(),
                    message_id,
                ),
            )
            conn.execute(
                "INSERT INTO message_versions (message_id, text, content_hash) VALUES (?, ?, ?)",
                (message_id, message.text, digest),
            )
            updated += 1
        conn.commit()
        return CollectorOutcome(inserted=inserted, duplicates=duplicates, updated=updated)
    finally:
        conn.close()
