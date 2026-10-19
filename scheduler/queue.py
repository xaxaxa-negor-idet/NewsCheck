"""Task queue: SPEC 13.1-13.4 — SQLite-backed queue with retry policy."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

TASK_TYPES = {
    "fetch_source", "process_message", "match_event", "search_sources",
    "verify_claims", "publish_event", "recheck_event", "update_publication",
    "fetch_media",
}

PRIORITY = {
    "publish_event": 1,
    "update_publication": 1,
    "process_message": 2,
    "match_event": 2,
    "search_sources": 3,
    "verify_claims": 3,
    "recheck_event": 4,
    "fetch_source": 4,
    "fetch_media": 5,
}


@dataclass(frozen=True)
class Task:
    id: int
    type: str
    payload: dict[str, Any]
    status: str
    priority: int
    attempts: int


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def enqueue_task(task_type: str, payload: dict[str, Any], db_path: str | None = None) -> int:
    if task_type not in TASK_TYPES:
        raise ValueError(f"unknown task type: {task_type}")
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO tasks (type, payload, status, priority) VALUES (?, ?, 'PENDING', ?)",
            (task_type, json.dumps(payload, ensure_ascii=False), PRIORITY[task_type]),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def next_task(db_path: str | None = None) -> Task | None:
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM tasks WHERE status='PENDING' AND (next_retry_at IS NULL OR next_retry_at <= ?) "
            "ORDER BY priority, id LIMIT 1",
            (_now(),),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE tasks SET status='PROCESSING', started_at=? WHERE id=? AND status='PENDING'",
            (_now(), row["id"]),
        )
        conn.commit()
        return Task(
            id=row["id"],
            type=row["type"],
            payload=json.loads(row["payload"] or "{}"),
            status="PROCESSING",
            priority=row["priority"],
            attempts=row["attempts"],
        )
    finally:
        conn.close()


def complete_task(task_id: int, db_path: str | None = None) -> None:
    conn = _connect(db_path)
    try:
        conn.execute("UPDATE tasks SET status='DONE', finished_at=? WHERE id=?", (_now(), task_id))
        conn.commit()
    finally:
        conn.close()


def fail_task(task_id: int, error: str, retry_delays_minutes: tuple[int, ...] = (1, 5, 30), db_path: str | None = None) -> str:
    conn = _connect(db_path)
    try:
        row = conn.execute("SELECT attempts FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise ValueError(f"task not found: {task_id}")
        attempts = row["attempts"] + 1
        status = "PENDING" if attempts < len(retry_delays_minutes) else "FAILED"
        if status == "PENDING":
            delay = retry_delays_minutes[min(attempts - 1, len(retry_delays_minutes) - 1)]
            next_retry = (datetime.now() + timedelta(minutes=delay)).isoformat(timespec="seconds")
            conn.execute(
                "UPDATE tasks SET attempts=?, status='PENDING', error=?, next_retry_at=? WHERE id=?",
                (attempts, error, next_retry, task_id),
            )
        else:
            conn.execute(
                "UPDATE tasks SET attempts=?, status='FAILED', error=?, finished_at=? WHERE id=?",
                (attempts, error, _now(), task_id),
            )
        conn.commit()
        return status
    finally:
        conn.close()
