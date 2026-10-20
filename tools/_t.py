# -*- coding: utf-8 -*-
from pathlib import Path
test = """from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sqlite3
from database.migrate import apply_migrations
from matching.event_dedup import find_existing_event


def test_same_message_returns_same_event(tmp_path):
    db = str(tmp_path / "m.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO events (title, summary) VALUES ('T1', 's')")
    conn.execute("INSERT INTO messages (channel_id, source_message_id, original_text, content_hash) VALUES (1, '1', 'text', 'h')")
    conn.execute("INSERT INTO event_messages (event_id, message_id, relation_confidence) VALUES (1, 1, 1.0)")
    conn.commit()
    conn.close()
    eid = find_existing_event("Any Title", "any text", db, message_id=1)
    assert eid == 1
"""
Path("tests/test_event_dedup.py").write_bytes(test.encode("utf-8"))
print('ok')
