# -*- coding: utf-8 -*-
"""LLM client: SPEC 7.3 — strict JSON with retry, logging, and validation."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "analysis" / "prompts"


@dataclass(frozen=True)
class LLMResponse:
    payload: dict
    model: str
    duration_ms: int
    attempts: int
    prompt_tokens: int | None
    completion_tokens: int | None


def extract_json(text: str) -> dict | None:
    """Extract first JSON object from model output, tolerating code fences."""
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    candidate = fenced.group(1) if fenced else text
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, re.S)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None


class LLMClient:
    def __init__(self, api_key: str, endpoint: str, model: str):
        if not api_key or not endpoint or not model:
            raise ValueError("api_key, endpoint, and model are required")
        self.client = OpenAI(api_key=api_key, base_url=endpoint)
        self.model = model

    def complete_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000, max_attempts: int = 3, error_feedback: str = "") -> dict:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt if not error_feedback else user_prompt + "\n\nПредыдущий ответ был невалиден. Исправь ошибку:\n" + error_feedback},
        ]
        last_error = ""
        for attempt in range(1, max_attempts + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            payload = extract_json(content)
            if payload is not None:
                return payload
            last_error = f"invalid JSON after attempt {attempt}: {content[:200]}"
        raise ValueError(last_error)
