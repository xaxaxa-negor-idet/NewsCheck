# -*- coding: utf-8 -*-
"""Debug LLM response to see what is actually returned."""
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_ENDPOINT"))
system_prompt = Path("analysis/prompts/analyzer_v1.md").read_text(encoding="utf-8-sig")
news = "В Китае представили четырёхметрового робота-титана весом больше тонны. Компания NeodraDynamics показала гуманоида Neo1."

completion = client.chat.completions.create(
    model=os.getenv("LLM_MODEL"),
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Разбери сообщение:\n" + news},
    ],
    max_tokens=3000,
)
content = completion.choices[0].message.content or ""
print("=== RAW CONTENT ===")
print(repr(content[:500]))
print("=== LENGTH ===", len(content))
print("=== FINISH REASON ===", completion.choices[0].finish_reason)
print("=== USAGE ===", completion.usage)
