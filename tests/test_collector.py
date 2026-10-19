from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timezone

from database.migrate import apply_migrations
from sources.collector import content_hash, ensure_channel, ingest_poll_result
from sources.telegram_web import PollResult, SourceMessage


def build_db(tmp_path):
    db = str(tmp_path / "collector.db")
    apply_migrations(db)
    channel_id = ensure_channel("topor", "ТОПОР", "right", db)
    return db, channel_id


def message(message_id="100", text="Первая новость", media=None):
    return SourceMessage(
        source_channel="topor",
        source_message_id=message_id,
        text=text,
        media=media or [],
        published_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        source_url=f"https://t.me/topor/{message_id}",
    )


def test_insert_duplicate_update(tmp_path):
    db, channel_id = build_db(tmp_path)

    first = ingest_poll_result(PollResult(kind="OK", messages=[message()]), channel_id, db)
    assert (first.inserted, first.duplicates, first.updated) == (1, 0, 0)

    second = ingest_poll_result(PollResult(kind="OK", messages=[message()]), channel_id, db)
    assert (second.inserted, second.duplicates, second.updated) == (0, 1, 0)

    changed = ingest_poll_result(
        PollResult(kind="OK", messages=[message(text="Первая новость (обновлено)")]), channel_id, db
    )
    assert (changed.inserted, changed.duplicates, changed.updated) == (0, 0, 1)

    import sqlite3
    conn = sqlite3.connect(db)
    status, availability = conn.execute(
        "SELECT processing_status, availability FROM messages WHERE channel_id=? AND source_message_id=?",
        (channel_id, "100"),
    ).fetchone()
    versions = conn.execute("SELECT COUNT(*) FROM message_versions").fetchone()[0]
    conn.close()
    assert status == "NEW" and availability == "EDITED" and versions == 2


def test_unavailable_is_rejected(tmp_path):
    db, channel_id = build_db(tmp_path)
    try:
        ingest_poll_result(PollResult(kind="UNAVAILABLE", reason="network"), channel_id, db)
    except ValueError:
        pass
    else:
        raise AssertionError("UNAVAILABLE must raise")


def test_content_hash_stable():
    assert content_hash("текст", ["a"]) == content_hash("текст", ["a"])
    assert content_hash("текст", ["a"]) != content_hash("текст", ["b"])
