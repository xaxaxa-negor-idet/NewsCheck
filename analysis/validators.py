"""LLM response validator: SPEC 7.3, 7.4, 17.16."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "core" / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / f"{name}.json").read_text(encoding="utf-8-sig"))


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]

    def error_text(self) -> str:
        return "; ".join(self.errors)


def validate_schema(payload: dict, schema_name: str) -> ValidationResult:
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    errors = [
        f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
        for error in validator.iter_errors(payload)
    ]
    return ValidationResult(ok=not errors, errors=errors)


def validate_verifier_references(payload: dict, allowed_claim_ids: set[int], allowed_source_ids: set[int]) -> ValidationResult:
    errors = []
    for verdict in payload.get("claim_verdicts", []):
        claim_id = verdict.get("claim_id")
        if claim_id not in allowed_claim_ids:
            errors.append(f"claim_verdicts: unknown claim_id {claim_id}")
        for source_id in verdict.get("supporting_source_ids", []) + verdict.get("refuting_source_ids", []):
            if source_id not in allowed_source_ids:
                errors.append(f"claim_verdicts: unknown source_id {source_id}")
        for evidence in verdict.get("evidence", []):
            if evidence.get("source_id") not in allowed_source_ids:
                errors.append(f"evidence: unknown source_id {evidence.get('source_id')}")
    for relation in payload.get("source_relations", []):
        if relation.get("source_id") not in allowed_source_ids:
            errors.append(f"source_relations: unknown source_id {relation.get('source_id')}")
        refers = relation.get("refers_to_source_id")
        if refers is not None and refers not in allowed_source_ids:
            errors.append(f"source_relations: unknown refers_to_source_id {refers}")
    return ValidationResult(ok=not errors, errors=errors)


def validate_verifier_quotes(payload: dict, source_texts: dict[int, str]) -> ValidationResult:
    errors = []
    for verdict in payload.get("claim_verdicts", []):
        if verdict.get("status") in ("CONFIRMED", "REFUTED", "CONFLICTING") and not verdict.get("evidence"):
            errors.append(f"claim {verdict.get('claim_id')}: status {verdict.get('status')} requires evidence")
        for evidence in verdict.get("evidence", []):
            source_id = evidence.get("source_id")
            quote = evidence.get("quote", "")
            text = source_texts.get(source_id)
            if text is None:
                errors.append(f"claim {verdict.get('claim_id')}: no text for source {source_id}")
            elif quote not in text:
                errors.append(f"claim {verdict.get('claim_id')}: quote is not substring of source {source_id}")
    return ValidationResult(ok=not errors, errors=errors)

