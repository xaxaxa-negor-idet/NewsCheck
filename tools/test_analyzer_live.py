# -*- coding: utf-8 -*-
"""Live analyzer smoke test against configured LLM endpoint."""
from pathlib import Path
import json
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_ENDPOINT"),
)
system_prompt = Path("analysis/prompts/analyzer_v1.md").read_text(encoding="utf-8-sig")
news = "В Москве на Садовом кольце произошло ДТП с участием трёх автомобилей, один человек погиб, движение перекрыто."
user_prompt = "Разбери сообщение:\n" + news

completion = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "claude-opus-5.5"),
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    max_tokens=2000,
)
content = completion.choices[0].message.content or ""
print(content)
