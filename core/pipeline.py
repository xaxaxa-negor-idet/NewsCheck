"""Pipeline: message → analysis → search → verification → status → publication."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
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


@dataclass(frozen=True)
class PipelineOutcome:
    message_id: int
    skipped: bool
    event_id: int | None
    status: str | None
    reason: str


class NewsCheckPipeline:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return _connect(self.db_path)

    def process_pending_message(self, message_id: int, analyzer, searcher, verifier, calculator, publisher=None) -> PipelineOutcome:
        conn = self._conn()
        try:
            message = conn.execute(
                """SELECT m.id, m.original_text, c.username
                   FROM messages m JOIN channels c ON c.id = m.channel_id
                   WHERE m.id = ?""",
                (message_id,),
            ).fetchone()
            if message is None:
                raise ValueError(f"message not found: {message_id}")

            # Stage 4: LLM analysis
            analysis = analyzer(message["original_text"])
            if not analysis["is_news"]:
                conn.execute("UPDATE messages SET processing_status='IGNORED' WHERE id=?", (message_id,))
                conn.commit()
                return PipelineOutcome(message_id, True, None, "IGNORED", "not news")

            event_data = analysis["event"]

            # Stage 5: Event creation (simplified matcher for now — no existing events yet)
            cursor = conn.execute(
                "INSERT INTO events (title, summary, location, event_date, event_type, current_status) VALUES (?, ?, ?, ?, ?, ?)",
                (event_data["title"], event_data["summary"], event_data["location"],
                 event_data["event_date"], event_data["event_type"], "ТРЕБУЕТ ДОПОЛНИТЕЛЬНОЙ ПРОВЕРКИ"),
            )
            event_id = int(cursor.lastrowid)
            conn.execute(
                "INSERT INTO event_messages (event_id, message_id, relation_confidence, relation_type) VALUES (?, ?, ?, 'AUTO_MERGE')",
                (event_id, message_id, 1.0),
            )

            claim_ids = []
            for claim in analysis["claims"]:
                cursor = conn.execute(
                    "INSERT INTO claims (event_id, message_id, claim_text, is_key) VALUES (?, ?, ?, ?)",
                    (event_id, message_id, claim["text"], 1 if claim["is_key"] else 0),
                )
                claim_ids.append(int(cursor.lastrowid))

            conn.execute("UPDATE messages SET processing_status='ANALYZED' WHERE id=?", (message_id,))

            # Stage 6: Search
            search_results = []
            for query in analysis["search_queries"][:3]:
                results = searcher(query)
                search_results.extend(results)

            # Stage 7: Verification
            claims_for_verifier = [
                {"id": cid, "text": text}
                for cid, text in zip(claim_ids, [c["text"] for c in analysis["claims"]])
            ]

            verification = verifier(claims_for_verifier, search_results)

            # Stage 8: Status calculation (simplified)
            verdicts = verification.get("claim_verdicts", [])
            if verdicts:
                status_result = calculator(verdicts)
            else:
                from verification.status_calculator import EventStatus
                status_result = {"status": "НЕ ПОДТВЕРЖДЕНО", "reason": "нет вердиктов"}

            conn.execute(
                "UPDATE events SET current_status=?, updated_at=? WHERE id=?",
                (status_result["status"], _now(), event_id),
            )
            conn.execute("UPDATE messages SET processing_status='PROCESSED' WHERE id=?", (message_id,))
            conn.commit()

            return PipelineOutcome(message_id, False, event_id, status_result["status"], status_result["reason"])
        finally:
            conn.close()

