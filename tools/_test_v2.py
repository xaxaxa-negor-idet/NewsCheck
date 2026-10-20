# -*- coding: utf-8 -*-
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import os
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from analysis.llm_client import LLMClient
from analysis.analyzer import analyze_message

client = LLMClient(
    api_key=os.getenv("LLM_API_KEY"),
    endpoint=os.getenv("LLM_ENDPOINT"),
    model=os.getenv("LLM_MODEL", "gpt-5.6-sol"),
)

text = "Эндрю Маккарти, бывший федеральный прокурор, призвал Конгресс расследовать действия Трампа. В статье для National Review он указал на ослабление санкций против России и отключение связи с Украиной. По его мнению, обстоятельства вызывают серьёзные вопросы."
result = analyze_message(client, text)
print(f"Claims: {len(result.payload['claims'])}")
for c in result.payload["claims"]:
    print(f"  [{c['is_key']}] {c['text']}")
