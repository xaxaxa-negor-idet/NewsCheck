# -*- coding: utf-8 -*-
"""Full runner: poll channels → analyze → search → verify → status → publish (dry-run)."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from analysis.analyzer import analyze_message
from analysis.llm_client import LLMClient
from analysis.prefilter import should_process
from core.pipeline import NewsCheckPipeline
from database.migrate import apply_migrations
from search.google_news import search as google_search
from verification.llm_verifier import verify_claims
from verification.status_calculator import (
    ClaimStatus,
    ClaimVerdict,
    EventStatus,
    calculate_status,
)
from publication.console import ConsoleDestination, RenderedPost
from publication.formatter import ClaimLine, EventPost, format_post
from sources.collector import ingest_poll_result
from sources.telegram_web import list_messages


def build_llm_client():
    load_dotenv(ROOT / ".env")
    return LLMClient(
        api_key=os.getenv("LLM_API_KEY", ""),
        endpoint=os.getenv("LLM_ENDPOINT", ""),
        model=os.getenv("LLM_MODEL", "claude-opus-5.5"),
    )


def analyzer_fn(client):
    def analyze(text: str) -> dict:
        result = analyze_message(client, text)
        return result.payload
    return analyze


def searcher_fn():
    def search(query: str) -> list[dict]:
        results = google_search(query, max_results=5)
        return [
            {
                "id": index,
                "title": result.title,
                "text": result.snippet or result.title,
                "domain": result.domain,
                "url": result.url,
            }
            for index, result in enumerate(results, start=1)
        ]
    return search


def verifier_fn(client):
    def verify(claims: list[dict], sources: list[dict]) -> dict:
        result = verify_claims(client, claims, sources)
        return result.payload
    return verify


def calculator_fn(verdicts: list[dict]) -> dict:
    claim_verdicts = []
    for verdict in verdicts:
        status = ClaimStatus(verdict["status"])
        is_key = bool(verdict.get("is_key", True))
        claim_verdicts.append(
            ClaimVerdict(status=status, is_key=is_key, direct_refutation=status == ClaimStatus.REFUTED)
        )
    result = calculate_status(claim_verdicts)
    return {"status": result.status.value, "reason": result.reason}


def run(poll: bool = False, process: int = 0, db_path: str | None = None):
    target = Path(db_path) if db_path else ROOT / "newscheck.db"
    apply_migrations(str(target))
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row

    if poll:
        channels = conn.execute("SELECT id, username, name FROM channels WHERE enabled=1").fetchall()
        print(f"Polling {len(channels)} channels...")
        for channel in channels:
            result = list_messages(channel["username"])
            if result.kind == "UNAVAILABLE":
                print(f"  @{channel['username']}: UNAVAILABLE ({result.reason})")
                continue
            outcome = ingest_poll_result(result, channel["id"], str(target))
            print(
                f"  @{channel['username']}: {result.kind} "
                f"new={outcome.inserted} dup={outcome.duplicates} edited={outcome.updated}"
            )

    if process > 0:
        client = build_llm_client()
        pipeline = NewsCheckPipeline(str(target))
        destination = ConsoleDestination()

        messages = conn.execute(
            "SELECT id FROM messages WHERE processing_status='NEW' AND length(original_text) > 80 ORDER BY id LIMIT ?",
            (process,),
        ).fetchall()
        print(f"Processing {len(messages)} messages...")

        for message in messages:
            row = conn.execute("SELECT original_text FROM messages WHERE id=?", (message["id"],)).fetchone()
            if not should_process(row["original_text"]):
                conn.execute("UPDATE messages SET processing_status='IGNORED' WHERE id=?", (message["id"],))
                conn.commit()
                print(f"  message {message['id']}: IGNORED (prefilter)")
                continue

            try:
                outcome = pipeline.process_pending_message(
                    message["id"],
                    analyzer_fn(client),
                    searcher_fn(),
                    verifier_fn(client),
                    calculator_fn,
                    destination,
                )
                print(f"  message {message['id']}: {outcome.status} (event {outcome.event_id})")
            except Exception as exc:
                print(f"  message {message['id']}: ERROR {exc}")
                conn.execute("UPDATE messages SET processing_status='ERROR' WHERE id=?", (message["id"],))
                conn.commit()

    conn.close()


def main():
    parser = argparse.ArgumentParser(prog="newscheck-run")
    parser.add_argument("--poll", action="store_true", help="poll all channels for new messages")
    parser.add_argument("--process", type=int, default=0, help="process N pending messages")
    parser.add_argument("--db", default=None)
    args = parser.parse_args()
    run(args.poll, args.process, args.db)


if __name__ == "__main__":
    main()
