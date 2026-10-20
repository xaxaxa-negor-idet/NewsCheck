# -*- coding: utf-8 -*-
"""Continuous mode v3: bulletproof daemon.

- per-channel poll retries
- per-message isolation (one failure never kills the cycle)
- LLM auto-rebuild on repeated failures
- publish retries
- fresh-lock release on exit
"""
from __future__ import annotations

import argparse
import functools
import os
import sqlite3
import sys
import time
import traceback
from pathlib import Path

print = functools.partial(print, flush=True)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from analysis.analyzer import analyze_message
from analysis.llm_client import LLMClient
from analysis.prefilter import should_process
from core.pipeline import NewsCheckPipeline
from database.migrate import apply_migrations
from search.google_news import search as google_news_search
from verification.llm_verifier import verify_claims
from sources.collector import ingest_poll_result
from sources.telegram_web import list_messages
from tools.publish import publish_pending_events
from tools.daemon_lock import acquire_lock, release_lock

load_dotenv(ROOT / ".env")

LLM_FAILURE_THRESHOLD = 5


def build_llm_client() -> LLMClient:
    return LLMClient(
        api_key=os.getenv("LLM_API_KEY", ""),
        endpoint=os.getenv("LLM_ENDPOINT", ""),
        model=os.getenv("LLM_MODEL", "gpt-5.6-sol"),
    )


def analyzer_fn(client):
    def analyze(text: str) -> dict:
        return analyze_message(client, text).payload
    return analyze


def searcher_fn():
    def search(query: str) -> list[dict]:
        for attempt in range(3):
            try:
                results = google_news_search(query, max_results=4)
                return [
                    {
                        "id": idx,
                        "title": r.title,
                        "text": (r.snippet or "")[:1000] or r.title,
                        "domain": r.domain,
                        "url": r.url,
                        "published_at": str(r.published_at) if r.published_at else None,
                    }
                    for idx, r in enumerate(results, start=1)
                ]
            except Exception:
                if attempt == 2:
                    return []
                time.sleep(3 * (attempt + 1))
    return search


def verifier_fn(client):
    def verify(claims, sources):
        return verify_claims(client, claims, sources).payload
    return verify


def calculator_fn(verdicts, source_count=0):
    from verification.status_calculator import ClaimStatus, ClaimVerdict, calculate_status
    claim_verdicts = []
    for verdict in verdicts:
        status = ClaimStatus(verdict["status"])
        is_key = bool(verdict.get("is_key", True))
        claim_verdicts.append(
            ClaimVerdict(status=status, is_key=is_key, direct_refutation=status == ClaimStatus.REFUTED)
        )
    result = calculate_status(claim_verdicts, source_count=source_count)
    return {"status": result.status.value, "reason": result.reason}


def poll_channels(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    channels = conn.execute("SELECT id, username, name FROM channels WHERE enabled=1").fetchall()
    conn.close()

    total_new = 0
    for channel in channels:
        ok = False
        for attempt in range(3):
            try:
                result = list_messages(channel["username"])
                if result.kind == "UNAVAILABLE":
                    print(f"  @{channel['username']}: retry {attempt+1}")
                    time.sleep(3 * (attempt + 1))
                    continue
                outcome = ingest_poll_result(result, channel["id"], db_path)
                total_new += outcome.inserted
                if outcome.inserted or outcome.updated:
                    print(f"  @{channel['username']}: +{outcome.inserted} new, {outcome.updated} edited")
                ok = True
                break
            except Exception:
                time.sleep(3 * (attempt + 1))
        if not ok:
            print(f"  @{channel['username']}: unavailable this cycle")
    return total_new


def process_new_messages(db_path: str, pipeline, fns, limit: int, llm_failures: list) -> int:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "UPDATE messages SET processing_status='ERROR' "
        "WHERE processing_status='PROCESSING' AND received_at < datetime('now', '-10 minutes')"
    )
    conn.execute(
        "UPDATE messages SET processing_status='IGNORED' "
        "WHERE processing_status='NEW' AND length(original_text) > 40 "
        "AND published_at < datetime('now', '-1 hours')"
    )
    conn.commit()

    messages = conn.execute(
        """SELECT id FROM messages
           WHERE processing_status='NEW' AND length(original_text) > 40
           ORDER BY published_at DESC, id LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()

    processed = 0
    for message in messages:
        mid = message["id"]
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT original_text FROM messages WHERE id=?", (mid,)).fetchone()
        conn.close()
        if not row or not should_process(row["original_text"] or ""):
            conn = sqlite3.connect(db_path)
            conn.execute("UPDATE messages SET processing_status='IGNORED' WHERE id=?", (mid,))
            conn.commit()
            conn.close()
            continue
        try:
            outcome = pipeline.process_pending_message(
                mid, fns["analyzer"], fns["searcher"], fns["verifier"], fns["calculator"]
            )
            print(f"  msg {mid}: {outcome.status} (event {outcome.event_id})")
            processed += 1
        except Exception as exc:
            print(f"  msg {mid}: ERROR {type(exc).__name__}: {exc}")
            traceback.print_exc()
            llm_failures.append(1)
            conn = sqlite3.connect(db_path)
            conn.execute("UPDATE messages SET processing_status='ERROR' WHERE id=?", (mid,))
            conn.commit()
            conn.close()
    return processed


def run_daemon(interval: int = 60, max_per_cycle: int = 5, db_path: str | None = None):
    db = db_path or str(ROOT / "newscheck.db")
    apply_migrations(db)

    client = build_llm_client()
    pipeline = NewsCheckPipeline(db)
    llm_failures: list[int] = []
    fns = {
        "analyzer": analyzer_fn(client),
        "searcher": searcher_fn(),
        "verifier": verifier_fn(client),
        "calculator": calculator_fn,
    }

    print("NewsCheck daemon v3 started")
    print(f"  poll interval: {interval}s")
    print(f"  max messages per cycle: {max_per_cycle}")
    print(f"  db: {db}")
    token_ok = bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHANNEL_ID"))
    print(f"  telegram: {'enabled' if token_ok else 'dry-run'}")

    if not acquire_lock():
        print("ERROR: another daemon is already running (daemon.lock). Exiting.")
        return
    print("Press Ctrl+C to stop")

    cycle = 0
    try:
        while True:
            cycle += 1
            try:
                print(f"\n--- cycle {cycle} [{time.strftime('%H:%M:%S')}] ---")
                new_count = poll_channels(db)
                print(f"  collected: {new_count} new messages")

                conn = sqlite3.connect(db)
                pending = conn.execute(
                    "SELECT COUNT(*) FROM messages WHERE processing_status='NEW' AND length(original_text) > 40"
                ).fetchone()[0]
                conn.close()

                if new_count > 0 or pending > 0:
                    processed = process_new_messages(db, pipeline, fns, max_per_cycle, llm_failures)
                    print(f"  processed: {processed}")

                    if processed > 0:
                        for attempt in range(3):
                            published = publish_pending_events(limit=max_per_cycle)
                            if published:
                                for item in published:
                                    print(f"  published: event {item.get('event_id')} -> {item.get('status')}")
                            if not published or all(i.get("status") == "PUBLISHED" for i in published):
                                break
                            time.sleep(5)
                else:
                    print("  nothing new, sleeping")

                if len(llm_failures) >= LLM_FAILURE_THRESHOLD:
                    print("  rebuilding LLM client after repeated failures")
                    client = build_llm_client()
                    fns["analyzer"] = analyzer_fn(client)
                    fns["verifier"] = verifier_fn(client)
                    llm_failures.clear()

            except Exception as exc:
                print(f"  cycle error: {type(exc).__name__}: {exc}")
                traceback.print_exc()

            time.sleep(min(interval, 30))
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        release_lock()


def main():
    parser = argparse.ArgumentParser(prog="newscheck-daemon")
    parser.add_argument("--interval", type=int, default=60, help="poll interval in seconds")
    parser.add_argument("--max-per-cycle", type=int, default=5, help="max messages to process per cycle")
    parser.add_argument("--db", default=None)
    args = parser.parse_args()
    run_daemon(args.interval, args.max_per_cycle, args.db)


if __name__ == "__main__":
    main()
