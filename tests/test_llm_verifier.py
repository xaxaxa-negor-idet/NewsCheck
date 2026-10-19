from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verification.llm_verifier import verify_claims
from analysis.llm_client import LLMClient


class FakeLLMClient(LLMClient):
    def __init__(self):
        self.model = "test-model"

    def complete_json(self, system_prompt, user_prompt, max_tokens=2000, max_attempts=3, error_feedback=""):
        assert "Утверждения:" in user_prompt
        return {
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


def test_verify_claims_valid_payload():
    client = FakeLLMClient()
    result = verify_claims(
        client,
        claims=[{"id": 1, "text": "Авария произошла"}],
        sources=[{"id": 10, "title": "News", "text": "Авария произошла утром", "domain": "news.com"}],
    )
    assert result.payload["claim_verdicts"][0]["status"] == "CONFIRMED"
    assert result.prompt_version == "verifier_v1"
