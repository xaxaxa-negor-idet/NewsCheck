from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pipeline import NewsCheckPipeline
from database.migrate import apply_migrations
from sources.collector import ensure_channel, ingest_poll_result
from sources.telegram_web import PollResult, SourceMessage


def analyzer(text):
    return {
        "event": {
            "title": "ДТП", "summary": "Авария", "location": "Москва",
            "event_date": "2026-10-01", "participants": [], "organizations": [],
            "roads_or_objects": [], "event_type": "ДТП",
        },
        "claims": [{"text": "произошло ДТП", "is_key": True}, {"text": "один погиб", "is_key": True}],
        "entities": ["Москва"], "search_queries": ["ДТП Москва"],
        "tags": ["ДТП"], "is_news": True, "ambiguity": "LOW",
    }


def searcher(query):
    return [{"id": 10, "title": "News", "text": "Авария произошла утром", "domain": "news.com", "url": "https://news.com/1"}]


def verifier(claims, sources):
    return {
        "claim_verdicts": [{
            "claim_id": claims[0]["id"], "status": "CONFIRMED",
            "supporting_source_ids": [10], "refuting_source_ids": [],
            "evidence": [{"source_id": 10, "quote": "Авария произошла"}],
        }],
        "source_relations": [{"source_id": 10, "is_primary": True}],
        "notes": "ok",
    }


def calculator(verdicts, source_count=0):
    return {"status": "ПОДТВЕРЖДЕНО", "reason": "все ключевые подтверждены"}


def prepare(tmp_path):
    db = str(tmp_path / "pipeline.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    channel_id = ensure_channel("topor", "ТОПОР", "right", db)
    ingest_poll_result(
        PollResult(kind="OK", messages=[SourceMessage(
            source_channel="topor", source_message_id="100", text="В Москве произошло ДТП",
            published_at=None, source_url="https://t.me/topor/100",
        )]),
        channel_id, db,
    )
    message_id = conn.execute("SELECT id FROM messages").fetchone()[0]
    conn.close()
    return db, message_id


def test_full_pipeline(tmp_path):
    db, message_id = prepare(tmp_path)
    pipeline = NewsCheckPipeline(db)
    outcome = pipeline.process_pending_message(message_id, analyzer, searcher, verifier, calculator)

    assert not outcome.skipped
    assert outcome.event_id is not None
    assert outcome.status == "ПОДТВЕРЖДЕНО"

    conn = sqlite3.connect(db)
    message_status = conn.execute("SELECT processing_status FROM messages WHERE id=?", (message_id,)).fetchone()[0]
    event_status = conn.execute("SELECT current_status FROM events WHERE id=?", (outcome.event_id,)).fetchone()[0]
    claims_count = conn.execute("SELECT COUNT(*) FROM claims WHERE event_id=?", (outcome.event_id,)).fetchone()[0]
    conn.close()
    assert message_status == "PROCESSED"
    assert event_status == "ПОДТВЕРЖДЕНО"
    assert claims_count == 2


def test_not_news_is_ignored(tmp_path):
    def not_news_analyzer(text):
        payload = analyzer(text)
        payload["is_news"] = False
        return payload

    db, message_id = prepare(tmp_path)
    pipeline = NewsCheckPipeline(db)
    outcome = pipeline.process_pending_message(message_id, not_news_analyzer, searcher, verifier, calculator)
    assert outcome.skipped and outcome.status == "IGNORED"


def test_pipeline_deduplicates_sources(tmp_path):
    db, message_id = prepare(tmp_path)
    pipeline = NewsCheckPipeline(db)

    def analyzer(text):
        return {
            "is_news": True,
            "event": {"title": "DTP", "summary": "s", "location": None, "event_date": None, "participants": [], "organizations": [], "roads_or_objects": [], "event_type": None},
            "claims": [{"text": "claim", "is_key": True}],
            "entities": [],
            "search_queries": ["q1"],
            "tags": [],
        }

    def searcher(query):
        return [
            {"id": 1, "title": "Same", "text": "t1", "domain": "news.com", "url": "https://news.com/a?utm=1"},
            {"id": 2, "title": "Same", "text": "t1", "domain": "news.com", "url": "https://news.com/a?utm=2"},
            {"id": 3, "title": "Other", "text": "t2", "domain": "news.com", "url": "https://news.com/b"},
        ]

    def verifier(claims, sources):
        return {"claim_verdicts": [{"claim_id": 1, "status": "CONFIRMED", "evidence": []}]}

    def calculator(verdicts, source_count=0):
        return {"status": "PODTVERZHDENO", "reason": "ok"}

    outcome = pipeline.process_pending_message(message_id, analyzer, searcher, verifier, calculator)

    import sqlite3
    conn = sqlite3.connect(db)
    count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    conn.close()
    assert count == 2  # dedup: a?utm=1 == a?utm=2, b stays
