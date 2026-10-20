# -*- coding: utf-8 -*-
"""Fast live test with limited sources and single attempt."""
from pathlib import Path
import os
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_ENDPOINT"))

# Step 1: Analyze
print("1. Analysis...")
system_prompt = Path("analysis/prompts/analyzer_v1.md").read_text(encoding="utf-8-sig")
text = "Италия ускорит выдачу виз россиянам. Срок рассмотрения заявлений сократили с 60 до 45 дней."
start = time.time()
completion = client.chat.completions.create(
    model=os.getenv("LLM_MODEL"),
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Разбери сообщение:\n" + text},
    ],
    max_tokens=4000,
)
analysis = json.loads(completion.choices[0].message.content)
print(f"   {time.time()-start:.1f}s, claims: {len(analysis['claims'])}")

# Step 2: Search (only 3 sources)
print("2. Search...")
from search.google_news import search
start = time.time()
sources = search(analysis["search_queries"][0], max_results=3)
source_dicts = [
    {"id": i, "title": r.title, "text": r.snippet or r.title, "domain": r.domain, "url": r.url}
    for i, r in enumerate(sources, 1)
]
print(f"   {time.time()-start:.1f}s, sources: {len(source_dicts)}")

# Step 3: Verify (single attempt)
print("3. Verification...")
verifier_prompt = Path("analysis/prompts/verifier_v1.md").read_text(encoding="utf-8-sig")
claims_text = "\n".join(f"ID {i}: {c['text']}" for i, c in enumerate(analysis["claims"], 1))
sources_text = "\n\n".join(f"ID {s['id']} | {s['domain']} | {s['title']}\n{s['text']}" for s in source_dicts)

start = time.time()
completion = client.chat.completions.create(
    model=os.getenv("LLM_MODEL"),
    messages=[
        {"role": "system", "content": verifier_prompt},
        {"role": "user", "content": f"Утверждения:\n{claims_text}\n\nИсточники:\n{sources_text}\n\nВерни вердикты по схеме."},
    ],
    max_tokens=4000,
)
verification = json.loads(completion.choices[0].message.content)
print(f"   {time.time()-start:.1f}s")
for verdict in verification.get("claim_verdicts", []):
    print(f"   claim {verdict['claim_id']}: {verdict['status']}")
    for ev in verdict.get("evidence", []):
        quote = ev.get("quote", "")
        source_text = next((s["text"] for s in source_dicts if s["id"] == ev["source_id"]), "")
        is_valid = quote in source_text
        print(f"     quote valid: {is_valid}")
