from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.migrate import apply_migrations
from scheduler.worker import QueueWorker


def test_worker_processes_task(tmp_path):
    db = str(tmp_path / "worker.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO tasks (type, payload, priority) VALUES ('test_task', '{\"value\": 42}', 1)")
    conn.commit()
    conn.close()

    worker = QueueWorker(db)
    worker.register("test_task", lambda payload: payload["value"] * 2)

    result = worker.process_one()
    assert result["status"] == "DONE"
    assert result["result"] == 84

    conn = sqlite3.connect(db)
    status = conn.execute("SELECT status FROM tasks").fetchone()[0]
    conn.close()
    assert status == "DONE"


def test_worker_fails_after_three_attempts(tmp_path):
    db = str(tmp_path / "worker.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO tasks (type, payload) VALUES ('bad_task', '{}')")
    conn.commit()
    conn.close()

    worker = QueueWorker(db)
    worker.register("bad_task", lambda payload: 1 / 0)

    for _ in range(3):
        # Reset next_retry_at so task is immediately available
        conn = sqlite3.connect(db)
        conn.execute("UPDATE tasks SET next_retry_at = NULL WHERE status='PENDING'")
        conn.commit()
        conn.close()
        result = worker.process_one()

    assert result is not None
    assert result["status"] == "FAILED"
