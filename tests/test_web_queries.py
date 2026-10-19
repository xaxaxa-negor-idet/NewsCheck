from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3

from database.migrate import apply_migrations
from web.queries import get_dashboard_counts, get_messages


def test_dashboard_counts(tmp_path):
    db = str(tmp_path / "web.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO channels (name, username) VALUES ('Тест', 'test')")
    conn.execute("INSERT INTO messages (channel_id, source_message_id, original_text, content_hash) VALUES (1, '1', 'текст', 'hash')")
    conn.execute("INSERT INTO events (title, current_status, lifecycle) VALUES ('Событие', 'ТРЕБУЕТ ДОПОЛНИТЕЛЬНОЙ ПРОВЕРКИ', 'ACTIVE')")
    conn.execute("INSERT INTO tasks (type, payload) VALUES ('fetch_source', '{}')")
    conn.commit()
    conn.close()

    counts = get_dashboard_counts(db)
    assert counts["messages_total"] == 1
    assert counts["messages_new"] == 1
    assert counts["events_total"] == 1
    assert counts["events_needs_check"] == 1
    assert counts["tasks_pending"] == 1


def test_get_messages_with_filter(tmp_path):
    db = str(tmp_path / "web.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO channels (name, username) VALUES ('Тест', 'test')")
    conn.execute("INSERT INTO messages (channel_id, source_message_id, original_text, content_hash, processing_status) VALUES (1, '1', 'новая', 'hash1', 'NEW')")
    conn.execute("INSERT INTO messages (channel_id, source_message_id, original_text, content_hash, processing_status) VALUES (1, '2', 'готовая', 'hash2', 'PROCESSED')")
    conn.commit()
    conn.close()

    all_messages = get_messages(db)
    new_messages = get_messages(db, status='NEW')
    assert len(all_messages) == 2
    assert len(new_messages) == 1
    assert new_messages[0]["original_text"] == "новая"
