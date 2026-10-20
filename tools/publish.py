# -*- coding: utf-8 -*-
"""Publish verified events to Telegram (dry-run if unavailable)."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from publication.telegram import TelegramChannelDestination
from publication.formatter import ClaimLine, EventPost, format_post

ROOT = Path(__file__).resolve().parent.parent


def publish_pending_events(channel_id: str | None = None, db_path: str | None = None, limit: int = 10) -> list[dict]:
    load_dotenv(ROOT / ".env")
    target = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row

    events = conn.execute(
        """SELECT e.id, e.title, e.summary, e.current_status, m.original_text, m.source_url, c.username
           FROM events e
           JOIN event_messages em ON em.event_id = e.id
           JOIN messages m ON m.id = em.message_id
           JOIN channels c ON c.id = m.channel_id
           LEFT JOIN published_messages pm ON pm.event_id = e.id
           WHERE pm.id IS NULL AND e.current_status IS NOT NULL
           ORDER BY e.id LIMIT ?""",
        (limit,),
    ).fetchall()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    destination_channel = channel_id or os.getenv("TELEGRAM_CHANNEL_ID", "")
    results = []

    for event in events:
        claims = conn.execute(
            "SELECT claim_text, status, is_key FROM claims WHERE event_id=? ORDER BY id",
            (event["id"],),
        ).fetchall()

        event_sources = conn.execute(
            "SELECT s.url, s.domain, s.title FROM sources s "
            "JOIN event_sources es ON es.source_id = s.id "
            "WHERE es.event_id = ? ORDER BY s.id LIMIT 5",
            (event["id"],),
        ).fetchall()
        source_links = [row["url"] for row in event_sources]

        post = EventPost(
            event_id=event["id"],
            original_text=event["original_text"] or "",
            status=event["current_status"],
            reason="Проверено по источникам",
            claims=[
                ClaimLine(text=c["claim_text"], status=c["status"])
                for c in claims
            ],
            source_links=source_links,
            source_channel=event["username"] or "",
            original_url=event["source_url"] or "",
            tags=[],
        )
        rendered = format_post(post)

        if token and destination_channel:
            try:
                destination = TelegramChannelDestination(token, destination_channel)
                result = destination.publish(type("R", (), {"event_id": event["id"], "text": rendered})())
                conn.execute(
                    "INSERT INTO published_messages (event_id, destination, telegram_message_id) VALUES (?, ?, ?)",
                    (event["id"], "telegram", result.external_id),
                )
                results.append({"event_id": event["id"], "status": "PUBLISHED"})
            except Exception as exc:
                results.append({"event_id": event["id"], "status": "ERROR", "error": str(exc)})
        else:
            print(rendered)
            print("---")
            results.append({"event_id": event["id"], "status": "DRY_RUN"})

    conn.commit()
    conn.close()
    return results


if __name__ == "__main__":
    for item in publish_pending_events():
        print(item)


