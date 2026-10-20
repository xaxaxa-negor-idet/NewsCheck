"""Web panel: SPEC 14 — server-rendered admin interface."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get_dashboard_counts(db_path: str | None = None) -> dict:
    path = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(path)
    try:
        queries = {
            "messages_total": "SELECT COUNT(*) FROM messages",
            "messages_new": "SELECT COUNT(*) FROM messages WHERE processing_status='NEW'",
            "messages_analyzed": "SELECT COUNT(*) FROM messages WHERE processing_status='ANALYZED'",
            "messages_processed": "SELECT COUNT(*) FROM messages WHERE processing_status='PROCESSED'",
            "messages_ignored": "SELECT COUNT(*) FROM messages WHERE processing_status='IGNORED'",
            "messages_failed": "SELECT COUNT(*) FROM messages WHERE processing_status='FAILED'",
            "events_total": "SELECT COUNT(*) FROM events",
            "events_active": "SELECT COUNT(*) FROM events WHERE lifecycle='ACTIVE'",
            "events_archived": "SELECT COUNT(*) FROM events WHERE lifecycle='ARCHIVED'",
            "events_needs_check": "SELECT COUNT(*) FROM events WHERE current_status='ТРЕБУЕТ ДОПОЛНИТЕЛЬНОЙ ПРОВЕРКИ'",
            "tasks_pending": "SELECT COUNT(*) FROM tasks WHERE status='PENDING'",
            "tasks_failed": "SELECT COUNT(*) FROM tasks WHERE status='FAILED'",
        }
        return {name: conn.execute(query).fetchone()[0] for name, query in queries.items()}
    finally:
        conn.close()


def get_messages(db_path: str | None = None, limit: int = 50, status: str | None = None) -> list[dict]:
    path = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        if status:
            rows = conn.execute(
                "SELECT m.id, m.original_text, m.processing_status, c.username, m.published_at "
                "FROM messages m JOIN channels c ON c.id=m.channel_id "
                "WHERE m.processing_status=? ORDER BY m.id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT m.id, m.original_text, m.processing_status, c.username, m.published_at "
                "FROM messages m JOIN channels c ON c.id=m.channel_id "
                "ORDER BY m.id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_events(db_path: str | None = None, limit: int = 50) -> list[dict]:
    path = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT e.id, e.title, e.current_status, e.created_at, e.status_reason "
            "FROM events e ORDER BY e.id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
