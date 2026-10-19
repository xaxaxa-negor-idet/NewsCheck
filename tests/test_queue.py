import sqlite3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.migrate import apply_migrations
from scheduler.queue import complete_task, enqueue_task, fail_task, next_task


def prepare(tmp_path):
    db = tmp_path / "q.db"
    apply_migrations(str(db))
    return db


def test_enqueue_and_complete(tmp_path):
    db = prepare(tmp_path)
    task_id = enqueue_task("fetch_source", {"channel": "topor"}, str(db))
    task = next_task(str(db))
    assert task is not None and task.id == task_id and task.type == "fetch_source"
    complete_task(task.id, str(db))

    conn = sqlite3.connect(db)
    status = conn.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()[0]
    conn.close()
    assert status == "DONE"


def test_retry_then_failed(tmp_path):
    db = prepare(tmp_path)
    task_id = enqueue_task("process_message", {"message_id": 1}, str(db))

    for expected in ("PENDING", "PENDING", "FAILED"):
        task = next_task(str(db))
        assert task is not None and task.id == task_id
        assert fail_task(task_id, "UNAVAILABLE", (0, 0, 0), str(db)) == expected

    conn = sqlite3.connect(db)
    attempts, status = conn.execute("SELECT attempts, status FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    assert attempts == 3 and status == "FAILED"


def test_invalid_task_type(tmp_path):
    db = prepare(tmp_path)
    try:
        enqueue_task("unknown", {}, str(db))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
