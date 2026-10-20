import sqlite3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.migrate import apply_migrations


def test_migration_creates_all_tables(tmp_path):
    db = tmp_path / "test.db"
    applied = apply_migrations(str(db))
    assert applied == ["001_init.sql", "002_event_sources.sql", "003_event_reason.sql"]

    conn = sqlite3.connect(db)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()

    required = {
        "channels", "messages", "message_versions", "media", "events",
        "event_messages", "claims", "sources", "claim_sources", "verifications",
        "verification_history", "published_messages", "publication_history",
        "user_decisions", "tasks", "source_dedup", "llm_calls", "config",
        "search_quota", "schema_migrations",
    }
    assert required <= tables


def test_migration_is_idempotent(tmp_path):
    db = tmp_path / "test.db"
    apply_migrations(str(db))
    assert apply_migrations(str(db)) == []
