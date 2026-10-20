"""Pipeline: message → analysis → search → verification → status → publication."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from matching.cross_channel import find_cross_channel_matches

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
                """SELECT m.id, m.original_text, c.username, m.channel_id
                   FROM messages m JOIN channels c ON c.id = m.channel_id
                   WHERE m.id = ?""",
                (message_id,),
            ).fetchone()
            if message is None:
                raise ValueError(f"message not found: {message_id}")
            message_channel_id = message["channel_id"]

            # Skip stale messages: published more than 1 hour ago
            age = conn.execute(
                "SELECT (julianday('now') - julianday(m.published_at)) * 24 FROM messages m WHERE m.id = ?",
                (message_id,),
            ).fetchone()
            if age and age[0] is not None and age[0] > 1.0:
                conn.execute("UPDATE messages SET processing_status='IGNORED' WHERE id=?", (message_id,))
                conn.commit()
                return PipelineOutcome(message_id, True, None, "IGNORED", "stale message >1h")

            # Mark as PROCESSING immediately to prevent duplicate processing
            conn.execute("UPDATE messages SET processing_status='PROCESSING' WHERE id=?", (message_id,))
            conn.commit()

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

            # Stage 6a: Cross-channel matches (other Telegram channels)
            cross_matches = find_cross_channel_matches(
                message_id, message_channel_id, event_data["title"], analysis.get("entities", [])
            )
            cross_sources = []
            for match in cross_matches:
                cross_sources.append({
                    "id": None,  # assign later
                    "title": f"@{match.channel_username}: {match.message_text[:100]}",
                    "text": match.message_text,
                    "domain": f"t.me/{match.channel_username}",
                    "url": match.source_url,
                })

            # Stage 6b: External news search
            search_results = []
            for query in analysis["search_queries"][:2]:
                results = searcher(query)[:3]
                search_results.extend(results)

            # Merge sources: external first (higher trust), then cross-channel
            all_sources = search_results + cross_sources

            # Deduplicate by URL and by (domain + title) to avoid identical sources
            seen_urls = set()
            seen_domain_title = set()
            deduped = []
            for source in all_sources:
                url = source.get("url", "")
                domain = source.get("domain", "")
                title = (source.get("title", "") or "")[:80]
                url_key = url.split("?")[0] if url else ""
                domain_title_key = (domain, title)

                if url_key and url_key in seen_urls:
                    continue
                if domain_title_key in seen_domain_title:
                    continue

                if url_key:
                    seen_urls.add(url_key)
                seen_domain_title.add(domain_title_key)
                deduped.append(source)

            all_sources = deduped
            for idx, source in enumerate(all_sources, 1):
                source["id"] = idx

            # Persist sources to database
            source_ids_map = []
            for source in all_sources:
                cursor = conn.execute(
                    "INSERT INTO sources (canonical_url, url, title, source_name, domain, content) VALUES (?, ?, ?, ?, ?, ?)",
                    (source["url"], source["url"], source["title"], source["domain"], source["domain"], source["text"]),
                )
                source_db_id = int(cursor.lastrowid)
                source_ids_map.append(source_db_id)
                conn.execute(
                    "INSERT INTO event_sources (event_id, source_id) VALUES (?, ?)",
                    (event_id, source_db_id),
                )

            # Stage 7: Verification
            claims_for_verifier = [
                {"id": cid, "text": text}
                for cid, text in zip(claim_ids, [c["text"] for c in analysis["claims"]])
            ]

            verification = verifier(claims_for_verifier, all_sources)

            # Update claim statuses from verdicts
            verdicts = verification.get("claim_verdicts", [])
            for verdict in verdicts:
                conn.execute(
                    "UPDATE claims SET status=? WHERE id=?",
                    (verdict["status"], verdict["claim_id"]),
                )

            # Stage 8: Status calculation
            if verdicts:
                claim_rows = conn.execute(
                    "SELECT c.id, c.status, c.is_key FROM claims c WHERE c.event_id=?",
                    (event_id,),
                ).fetchall()
                verdict_map = {v["claim_id"]: v for v in verdicts}
                enriched = []
                for row in claim_rows:
                    enriched.append({
                        "claim_id": row["id"],
                        "status": verdict_map.get(row["id"], {}).get("status", row["status"]),
                        "is_key": bool(row["is_key"]),
                    })
                status_result = calculator(enriched, source_count=len(all_sources))
            else:
                status_result = {"status": "НЕ ПОДТВЕРЖДЕНО", "reason": "нет вердиктов"}

            conn.execute(
                "UPDATE events SET current_status=?, status_reason=?, updated_at=? WHERE id=?",
                (status_result["status"], status_result.get("reason", ""), _now(), event_id),
            )
            conn.execute("UPDATE messages SET processing_status='PROCESSED' WHERE id=?", (message_id,))
            conn.commit()

            return PipelineOutcome(message_id, False, event_id, status_result["status"], status_result["reason"])
        finally:
            conn.close()


