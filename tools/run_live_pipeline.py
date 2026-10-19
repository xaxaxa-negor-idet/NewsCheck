# -*- coding: utf-8 -*-
"""Run live pipeline on real messages with real LLM and GDELT search."""
from pathlib import Path
import json
import os
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

from analysis.llm_client import LLMClient, extract_json
from analysis.analyzer import analyze_message
from analysis.validators import validate_schema, validate_verifier_quotes, validate_verifier_references
from search.gdelt import search as gdelt_search

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = LLMClient(
    api_key=os.getenv("LLM_API_KEY"),
    endpoint=os.getenv("LLM_ENDPOINT"),
    model=os.getenv("LLM_MODEL", "claude-opus-5.5"),
)

# Take 3 real messages from database
import sqlite3
conn = sqlite3.connect(Path(__file__).resolve().parent.parent / "newscheck.db")
conn.row_factory = sqlite3.Row
messages = conn.execute(
    "SELECT m.id, m.original_text, c.username FROM messages m JOIN channels c ON c.id=m.channel_id WHERE m.processing_status='NEW' AND length(m.original_text) > 80 ORDER BY m.id LIMIT 3"
).fetchall()
conn.close()

print(f"Processing {len(messages)} messages...")

for message in messages:
    print(f"\n=== Message {message['id']} from @{message['username']} ===")
    print(f"Text: {message['original_text'][:120]}...")

    try:
        result = analyze_message(client, message["original_text"])
        print(f"Analysis: event='{result.payload['event']['title']}' is_news={result.payload['is_news']} claims={len(result.payload['claims'])}")

        if not result.payload["is_news"]:
            print("→ IGNORED (not news)")
            continue

        queries = result.payload["search_queries"][:2]
        print(f"Search queries: {queries}")
        search_results = []
        for query in queries:
            try:
                results = gdelt_search(query)
                search_results.extend(results)
                print(f"  query '{query[:40]}': {len(results)} results")
                time.sleep(6)
            except Exception as exc:
                print(f"  query failed: {exc}")

        if not search_results:
            print("→ No sources found, would be UNCONFIRMED")
            continue

        print(f"Total sources: {len(search_results)}")
        print("→ Would proceed to verification")
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
