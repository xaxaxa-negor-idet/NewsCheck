"""Query translation for English-first search: LLM translates RU → EN."""
from __future__ import annotations

from analysis.llm_client import LLMClient

SYSTEM_PROMPT = """Translate a Russian news search query to English.
Rules:
1. Keep place names in transliteration (Абакан → Abakan, Москва → Moscow)
2. Keep dates as-is (16 октября → October 16)
3. Return ONLY the translated query, nothing else
4. Preserve search intent (news events, crime, accidents)
"""


def translate_query(client: LLMClient, query: str) -> str:
    """Translate a Russian search query to English for better search results."""
    response = client.client.chat.completions.create(
        model=client.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        max_tokens=100,
    )
    return (response.choices[0].message.content or "").strip()
