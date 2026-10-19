# -*- coding: utf-8 -*-
"""LLM Analyzer: SPEC 7.2 — message to Event/Claims/Queries via LLM."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from analysis.llm_client import LLMClient
from analysis.validators import validate_schema

ROOT = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT / "prompts"
PROMPT_VERSION = "analyzer_v1"


@dataclass(frozen=True)
class AnalysisResult:
    payload: dict
    model: str
    prompt_version: str


def analyze_message(client: LLMClient, text: str) -> AnalysisResult:
    system_prompt = (PROMPTS_DIR / "analyzer_v1.md").read_text(encoding="utf-8-sig")
    user_prompt = "Разбери сообщение:\n" + text

    payload = client.complete_json(system_prompt, user_prompt)
    validation = validate_schema(payload, "analyzer")
    if not validation.ok:
        raise ValueError(f"analyzer schema validation failed: {validation.error_text()}")

    return AnalysisResult(payload=payload, model=client.model, prompt_version=PROMPT_VERSION)
