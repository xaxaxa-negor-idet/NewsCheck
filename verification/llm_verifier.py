# -*- coding: utf-8 -*-
"""LLM Verifier: SPEC 7.4 — claims + sources to verdicts with quotes."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from analysis.llm_client import LLMClient
from analysis.validators import (
    validate_schema,
    validate_verifier_quotes,
    validate_verifier_references,
)

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "analysis" / "prompts"
PROMPT_VERSION = "verifier_v2"


@dataclass(frozen=True)
class VerificationResult:
    payload: dict
    model: str
    prompt_version: str


def verify_claims(client: LLMClient, claims: list[dict], sources: list[dict], max_attempts: int = 2) -> VerificationResult:
    """claims: [{id, text}]; sources: [{id, title, text, domain, published_at}]"""
    system_prompt = (PROMPTS_DIR / "verifier_v2.md").read_text(encoding="utf-8-sig")
    user_prompt = (
        "Утверждения:\n"
        + "\n".join(f"ID {claim['id']}: {claim['text']}" for claim in claims)
        + "\n\nИсточники (полный текст, с датой публикации):\n"
        + "\n\n".join(
            f"=== SOURCE ID {source['id']} ===\nDomain: {source.get('domain', '')}\nTitle: {source.get('title', '')}\nPublished: {source.get('published_at', 'unknown')}\nText:\n{source.get('text', '')}"
            for source in sources
        )
        + "\n\nВерни вердикты по схеме. ВАЖНО:\n1. quote должен быть ТОЧНОЙ подстрокой из поля Text источника.\n2. Источник подтверждает утверждение ТОЛЬКО если описывает ТОТ ЖЕ САМЫЙ инцидент/событие, а не похожее другое событие в другое время.\n3. Если источник описывает другой случай (даже похожий) — это UNCONFIRMED, не CONFIRMED."
    )

    allowed_claim_ids = {claim["id"] for claim in claims}
    allowed_source_ids = {source["id"] for source in sources}
    source_texts = {source["id"]: source.get("text", "") for source in sources}

    error_feedback = ""
    last_errors = []
    for attempt in range(max_attempts):
        payload = client.complete_json(system_prompt, user_prompt, max_tokens=8000, error_feedback=error_feedback)

        errors = []
        for validator in (
            validate_schema(payload, "verifier"),
            validate_verifier_references(payload, allowed_claim_ids, allowed_source_ids),
            validate_verifier_quotes(payload, source_texts),
        ):
            if not validator.ok:
                errors.extend(validator.errors)

        if not errors:
            return VerificationResult(payload=payload, model=client.model, prompt_version=PROMPT_VERSION)

        last_errors = errors
        error_feedback = "Ошибки валидации:\n" + "\n".join(errors[:10])

    raise ValueError("verifier validation failed: " + "; ".join(last_errors))

