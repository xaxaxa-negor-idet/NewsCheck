# -*- coding: utf-8 -*-
"""Simplified fast pipeline test — one message, verbose output."""
from pathlib import Path
import os
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_ENDPOINT"))
system_prompt = Path("analysis/prompts/analyzer_v1.md").read_text(encoding="utf-8-sig")

text = "Италия ускорит выдачу виз россиянам. Срок рассмотрения заявлений сократили с 60 до 45 дней."
print("1. Single LLM call test...")
start = time.time()
completion = client.chat.completions.create(
    model=os.getenv("LLM_MODEL"),
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Разбери сообщение:\n" + text},
    ],
    max_tokens=4000,
)
elapsed = time.time() - start
content = completion.choices[0].message.content or ""
print(f"   time: {elapsed:.1f}s, length: {len(content)}")
print(f"   finish: {completion.choices[0].finish_reason}")
print(f"   content start: {content[:200]}")

# Try to parse
import json
try:
    payload = json.loads(content)
    print("2. JSON parse: OK")
    print(f"   is_news: {payload.get('is_news')}")
    print(f"   claims: {len(payload.get('claims', []))}")
except json.JSONDecodeError as e:
    print(f"2. JSON parse FAILED: {e}")
    # Try fenced extraction
    import re
    match = re.search(r'```(?:json)?\s*(.*?)```', content, re.S)
    if match:
        try:
            payload = json.loads(match.group(1))
            print("   Fenced extraction: OK")
        except:
            print("   Fenced extraction: FAILED")
