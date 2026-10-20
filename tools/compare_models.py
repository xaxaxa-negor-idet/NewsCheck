# -*- coding: utf-8 -*-
"""Compare available models for speed and JSON quality."""
from pathlib import Path
import json
import os
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_ENDPOINT"))

system_prompt = "Ты — парсер новостей. Отвечай строго валидным JSON."
user_prompt = 'Извлеки событие и 2 утверждения. Ответ JSON: {"title": "...", "claims": ["...", "..."]}\nНовость: В Москве произошло ДТП с тремя машинами, один погиб.'

models = ["claude-opus-5.5", "gpt-5.6-sol", "gpt-5.6-luna", "gpt-6-astra"]
for model in models:
    start = time.time()
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            max_tokens=1000,
        )
        elapsed = time.time() - start
        content = completion.choices[0].message.content or ""
        valid = content.strip().startswith("{")
        print(f"{model}: {elapsed:.1f}s, valid={valid}, tokens={completion.usage.completion_tokens}")
        print(f"  answer: {content[:100]}")
    except Exception as exc:
        elapsed = time.time() - start
        print(f"{model}: {elapsed:.1f}s, ERROR: {exc}")
