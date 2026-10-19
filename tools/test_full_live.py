# -*- coding: utf-8 -*-
"""Full live verification test with Google News search."""
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from analysis.analyzer import analyze_message
from analysis.llm_client import LLMClient
from search.google_news import search as google_search
from verification.llm_verifier import verify_claims

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = LLMClient(
    api_key=os.getenv("LLM_API_KEY"),
    endpoint=os.getenv("LLM_ENDPOINT"),
    model=os.getenv("LLM_MODEL", "claude-opus-5.5"),
)

text = "В Хакасии 21-летняя девушка убила 16-летнюю подругу ударом ножа в сердце. Трагедия произошла ночью 16 октября возле ночного клуба в Абакане."

print("1. Analysis...")
analysis = analyze_message(client, text)
print(f"   event: {analysis.payload['event']['title']}")
print(f"   claims: {len(analysis.payload['claims'])}")
for claim in analysis.payload["claims"]:
    print(f"   - [{'KEY' if claim['is_key'] else '   '}] {claim['text'][:70]}")

print("\n2. Search...")
all_sources = []
source_id = 1
for query in analysis.payload["search_queries"][:2]:
    print(f"   query: {query}")
    results = google_search(query, max_results=5)
    for result in results:
        print(f"     found: {result.title[:60]} ({result.domain})")
        all_sources.append({
            "id": source_id,
            "title": result.title,
            "text": result.snippet if result.snippet else result.title,
            "domain": result.domain,
            "url": result.url,
        })
        source_id += 1

print(f"\n3. Verification with {len(all_sources)} sources...")
try:
    verification = verify_claims(
        client,
        claims=[{"id": i + 1, "text": claim["text"]} for i, claim in enumerate(analysis.payload["claims"])],
        sources=all_sources,
    )
    print("4. Verdicts:")
    for verdict in verification.payload["claim_verdicts"]:
        print(f"   claim {verdict['claim_id']}: {verdict['status']}")
        for evidence in verdict.get("evidence", []):
            print(f"     source {evidence['source_id']}: {evidence['quote'][:70]}")
except Exception as exc:
    print(f"Verification failed: {exc}")
