# -*- coding: utf-8 -*-
"""Event fingerprinting: detect duplicates by content similarity before creating a new event."""
from __future__ import annotations

import re
import sqlite3
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation/emojis/stop-words, keep keywords."""
    text = text.lower()
    text = re.sub(r"[^\w\sа-яё]", " ", text)
    stop = {"в", "на", "с", "и", "по", "из", "у", "к", "за", "от", "до", "о", "об",
            "что", "это", "как", "для", "при", "про", "его", "её", "их", "они",
            "был", "была", "было", "будет", "стал", "стала", "есть", "год", "года", "годах"}
    words = [w for w in text.split() if w not in stop and len(w) > 2]
    return " ".join(words)


def compute_fingerprint(text: str) -> str:
    """Stable fingerprint from normalized significant keywords."""
    normalized = normalize_text(text)
    return sha256(normalized.encode("utf-8")).hexdigest()[:32]


def find_existing_event(title: str, original_text: str, db_path: str | None = None, message_id: int | None = None) -> int | None:
    """Return existing event id if a similar event already exists."""
    conn = _connect(db_path)
    try:
        # 1. Same source message already has an event ? strongest signal
        if message_id is not None:
            row = conn.execute(
                "SELECT em.event_id FROM event_messages em WHERE em.message_id=? LIMIT 1",
                (message_id,),
            ).fetchone()
            if row:
                return int(row["event_id"])

        fingerprint = compute_fingerprint(title + " " + original_text[:200])
        row = conn.execute(
            "SELECT id FROM events WHERE fingerprint=? LIMIT 1", (fingerprint,)
        ).fetchone()
        if row:
            return int(row["id"])

        # Fallback: normalized-title similarity over recent events
        norm_title = normalize_text(title)
        if not norm_title:
            return None
        candidates = conn.execute(
            "SELECT id, title FROM events WHERE created_at > datetime('now', '-3 days') ORDER BY id DESC LIMIT 100"
        ).fetchall()
        title_words = set(norm_title.split())
        for cand in candidates:
            cand_words = set(normalize_text(cand["title"]).split())
            if not cand_words:
                continue
            overlap = len(title_words & cand_words)
            if overlap >= max(3, int(0.7 * len(cand_words))):
                return int(cand["id"])
        return None
    finally:
        conn.close()
