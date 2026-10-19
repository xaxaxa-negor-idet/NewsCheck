from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.validators import (
    validate_schema,
    validate_verifier_quotes,
    validate_verifier_references,
)


def test_valid_verifier_payload():
    payload = {
        "claim_verdicts": [{
            "claim_id": 1,
            "status": "CONFIRMED",
            "supporting_source_ids": [10],
            "refuting_source_ids": [],
            "evidence": [{"source_id": 10, "quote": "Авария произошла"}],
        }],
        "source_relations": [{"source_id": 10, "is_primary": True}],
        "notes": "ok",
    }
    assert validate_schema(payload, "verifier").ok
    assert validate_verifier_references(payload, {1}, {10}).ok
    assert validate_verifier_quotes(payload, {10: "Авария произошла утром"}).ok


def test_unknown_source_id_rejected():
    payload = {
        "claim_verdicts": [{
            "claim_id": 2,
            "status": "UNCONFIRMED",
            "supporting_source_ids": [99],
            "refuting_source_ids": [],
            "evidence": [],
        }],
        "source_relations": [],
        "notes": "",
    }
    assert not validate_verifier_references(payload, {1, 2}, {10}).ok


def test_fabricated_quote_rejected():
    payload = {
        "claim_verdicts": [{
            "claim_id": 1,
            "status": "CONFIRMED",
            "supporting_source_ids": [10],
            "refuting_source_ids": [],
            "evidence": [{"source_id": 10, "quote": "этой фразы нет в тексте"}],
        }],
        "source_relations": [],
        "notes": "",
    }
    assert not validate_verifier_quotes(payload, {10: "Авария произошла утром"}).ok


def test_schema_rejects_extra_fields():
    payload = {"unexpected": True}
    assert not validate_schema(payload, "verifier").ok
