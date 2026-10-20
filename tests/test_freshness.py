from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sqlite3
from database.migrate import apply_migrations
from core.pipeline import NewsCheckPipeline


def prepare(tmp_path, age_sql="datetime('now')"):
    db = str(tmp_path / "fresh.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO channels (name, username) VALUES ('T', 't')")
    conn.execute(
        f"INSERT INTO messages (channel_id, source_message_id, original_text, content_hash, source_url, published_at) "
        f"VALUES (1, '1', 'Novost pro test event', 'h1', 'https://t.me/t/1', {age_sql})"
    )
    conn.commit()
    conn.close()
    return db, 1


def test_stale_ignored(tmp_path):
    db, mid = prepare(tmp_path, "datetime('now', '-2 hours')")
    pipeline = NewsCheckPipeline(db)
    outcome = pipeline.process_pending_message(mid, lambda t: {}, lambda q: [], lambda c, s: {}, lambda v, sc=0: {})
    assert outcome.skipped is True
    assert outcome.status == "IGNORED"
    conn = sqlite3.connect(db)
    status = conn.execute("SELECT processing_status FROM messages WHERE id=1").fetchone()[0]
    conn.close()
    assert status == "IGNORED"


def test_fresh_processed(tmp_path):
    db, mid = prepare(tmp_path, "datetime('now', '-5 minutes')")
    pipeline = NewsCheckPipeline(db)

    def analyzer(text):
        return {
            "is_news": True,
            "event": {"title": "T", "summary": "s", "location": None, "event_date": None,
                       "participants": [], "organizations": [], "roads_or_objects": [], "event_type": None},
            "claims": [{"text": "c", "is_key": True}],
            "entities": [], "search_queries": ["q"], "tags": [],
        }

    def verifier(claims, sources):
        return {"claim_verdicts": [{"claim_id": 1, "status": "CONFIRMED"}]}

    def calculator(verdicts, source_count=0):
        return {"status": "PODTVERZHDENO", "reason": "ok"}

    outcome = pipeline.process_pending_message(mid, analyzer, lambda q: [], verifier, calculator)
    assert outcome.event_id is not None
