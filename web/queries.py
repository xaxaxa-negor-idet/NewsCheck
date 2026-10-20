# -*- coding: utf-8 -*-
"""Web panel queries: channels, events, edit/delete posts."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent


def _conn(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_channels(db_path: str | None = None) -> list[dict]:
    conn = _conn(db_path)
    try:
        rows = conn.execute("SELECT id, name, username, enabled FROM channels ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_channel(name: str, username: str, db_path: str | None = None) -> bool:
    username = username.lstrip("@").strip()
    if not username:
        return False
    conn = _conn(db_path)
    try:
        conn.execute(
            "INSERT INTO channels (name, username, enabled) VALUES (?, ?, 1)",
            (name.strip() or username, username),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def toggle_channel(channel_id: int, db_path: str | None = None) -> None:
    conn = _conn(db_path)
    try:
        conn.execute("UPDATE channels SET enabled = 1 - enabled WHERE id=?", (channel_id,))
        conn.commit()
    finally:
        conn.close()


def delete_channel(channel_id: int, db_path: str | None = None) -> None:
    conn = _conn(db_path)
    try:
        conn.execute("DELETE FROM channels WHERE id=?", (channel_id,))
        conn.commit()
    finally:
        conn.close()


def get_event_detail(event_id: int, db_path: str | None = None) -> dict | None:
    conn = _conn(db_path)
    try:
        row = conn.execute(
            """SELECT e.id, e.title, e.summary, e.current_status, e.status_reason, e.created_at,
                      m.original_text, m.source_url, c.username AS channel_username, pm.telegram_message_id
               FROM events e
               JOIN event_messages em ON em.event_id=e.id
               JOIN messages m ON m.id=em.message_id
               JOIN channels c ON c.id=m.channel_id
               LEFT JOIN published_messages pm ON pm.event_id=e.id
               WHERE e.id=?""",
            (event_id,),
        ).fetchone()
        if not row:
            return None
        detail = dict(row)
        sources = conn.execute(
            "SELECT s.id, s.title, s.url, s.domain FROM sources s "
            "JOIN event_sources es ON es.source_id=s.id WHERE es.event_id=? ORDER BY s.id LIMIT 5",
            (event_id,),
        ).fetchall()
        detail["sources"] = [dict(s) for s in sources]
        return detail
    finally:
        conn.close()


def update_event_text(event_id: int, new_text: str, db_path: str | None = None) -> None:
    conn = _conn(db_path)
    try:
        conn.execute(
            "UPDATE messages SET original_text=? WHERE id IN "
            "(SELECT message_id FROM event_messages WHERE event_id=?)",
            (new_text, event_id),
        )
        conn.commit()
    finally:
        conn.close()


def telegram_edit_message(event_id: int, new_text: str) -> bool:
    """Edit the published Telegram message text."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    channel = os.getenv("TELEGRAM_CHANNEL_ID", "")
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT telegram_message_id FROM published_messages WHERE event_id=?", (event_id,)
        ).fetchone()
        if not row or not token or not channel:
            return False
        mid = row["telegram_message_id"]
    finally:
        conn.close()
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/editMessageText",
            json={"chat_id": channel, "message_id": int(mid), "text": new_text, "parse_mode": "HTML"},
            timeout=30,
        )
        return r.json().get("ok", False)
    except Exception:
        return False


def telegram_delete_message(event_id: int) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    channel = os.getenv("TELEGRAM_CHANNEL_ID", "")
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT telegram_message_id FROM published_messages WHERE event_id=?", (event_id,)
        ).fetchone()
        if not row or not token or not channel:
            return False
        mid = row["telegram_message_id"]
        conn.execute("DELETE FROM published_messages WHERE event_id=?", (event_id,))
        conn.commit()
    finally:
        conn.close()
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/deleteMessage",
            json={"chat_id": channel, "message_id": int(mid)},
            timeout=30,
        )
        return r.json().get("ok", False)
    except Exception:
        return False


def get_dashboard_counts(db_path: str | None = None) -> dict:
    conn = _conn(db_path)
    try:
        queries = {
            "messages_total": "SELECT COUNT(*) FROM messages",
            "messages_new": "SELECT COUNT(*) FROM messages WHERE processing_status='NEW'",
            "messages_processed": "SELECT COUNT(*) FROM messages WHERE processing_status='PROCESSED'",
            "messages_ignored": "SELECT COUNT(*) FROM messages WHERE processing_status='IGNORED'",
            "events_total": "SELECT COUNT(*) FROM events",
            "events_active": "SELECT COUNT(*) FROM events WHERE lifecycle='ACTIVE'",
            "events_needs_check": "SELECT COUNT(*) FROM events WHERE current_status LIKE '%ПРОВЕРК%'",
            "tasks_pending": "SELECT COUNT(*) FROM tasks WHERE status='PENDING'",
            "tasks_failed": "SELECT COUNT(*) FROM tasks WHERE status='FAILED'",
            "messages_failed": "SELECT COUNT(*) FROM messages WHERE processing_status='FAILED'",
            "events_archived": "SELECT COUNT(*) FROM events WHERE lifecycle='ARCHIVED'",
        }
        return {name: conn.execute(query).fetchone()[0] for name, query in queries.items()}
    finally:
        conn.close()


def get_messages(db_path: str | None = None, limit: int = 50, status: str | None = None) -> list[dict]:
    conn = _conn(db_path)
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
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_events(db_path: str | None = None, limit: int = 50) -> list[dict]:
    conn = _conn(db_path)
    try:
        rows = conn.execute(
            "SELECT e.id, e.title, e.current_status, e.created_at, e.status_reason "
            "FROM events e ORDER BY e.id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
