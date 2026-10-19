"""Queue worker: SPEC 13 — processes tasks from the SQLite queue."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


class QueueWorker:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path
        self.handlers: dict[str, Callable] = {}

    def register(self, task_type: str, handler: Callable) -> None:
        self.handlers[task_type] = handler

    def process_one(self) -> dict | None:
        conn = _connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM tasks WHERE status='PENDING' AND (next_retry_at IS NULL OR next_retry_at <= ?) "
                "ORDER BY priority, id LIMIT 1",
                (_now(),),
            ).fetchone()
            if row is None:
                return None

            conn.execute(
                "UPDATE tasks SET status='PROCESSING', started_at=? WHERE id=?",
                (_now(), row["id"]),
            )
            conn.commit()
        finally:
            conn.close()

        task_type = row["type"]
        payload = json.loads(row["payload"] or "{}")
        handler = self.handlers.get(task_type)
        if handler is None:
            self._fail(row["id"], f"no handler for task type: {task_type}")
            return {"id": row["id"], "type": task_type, "status": "FAILED"}

        try:
            result = handler(payload)
            conn = _connect(self.db_path)
            conn.execute(
                "UPDATE tasks SET status='DONE', finished_at=? WHERE id=?",
                (_now(), row["id"]),
            )
            conn.commit()
            conn.close()
            return {"id": row["id"], "type": task_type, "status": "DONE", "result": result}
        except Exception as exc:
            self._fail(row["id"], f"{type(exc).__name__}: {exc}")
            return {"id": row["id"], "type": task_type, "status": "FAILED", "error": str(exc)}

    def _fail(self, task_id: int, error: str) -> None:
        conn = _connect(self.db_path)
        try:
            row = conn.execute("SELECT attempts FROM tasks WHERE id=?", (task_id,)).fetchone()
            attempts = (row["attempts"] if row else 0) + 1
            if attempts >= 3:
                conn.execute(
                    "UPDATE tasks SET status='FAILED', attempts=?, error=?, finished_at=? WHERE id=?",
                    (attempts, error, _now(), task_id),
                )
            else:
                delay_minutes = (1, 5)[attempts - 1]
                from datetime import timedelta
                next_retry = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
                conn.execute(
                    "UPDATE tasks SET status='PENDING', attempts=?, error=?, next_retry_at=? WHERE id=?",
                    (attempts, error, next_retry.isoformat(timespec="seconds"), task_id),
                )
            conn.commit()
        finally:
            conn.close()
