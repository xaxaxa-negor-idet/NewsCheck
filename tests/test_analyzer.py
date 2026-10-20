from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.analyzer import analyze_message
from analysis.llm_client import LLMClient


class FakeLLMClient(LLMClient):
    def __init__(self):
        self.model = "test-model"
        self.calls = []

    def complete_json(self, system_prompt, user_prompt, max_tokens=2000, max_attempts=3, error_feedback=""):
        self.calls.append((system_prompt, user_prompt))
        return {
            "event": {
                "title": "ДТП",
                "summary": "Авария",
                "location": "Москва",
                "event_date": "2026-10-01",
                "participants": [],
                "organizations": [],
                "roads_or_objects": [],
                "event_type": "ДТП",
            },
            "claims": [{"text": "произошло ДТП", "is_key": True}, {"text": "один погиб", "is_key": True}],
            "entities": ["Москва"],
            "search_queries": ["ДТП Москва"],
            "tags": ["ДТП"],
            "is_news": True,
            "ambiguity": "LOW",
        }


def test_analyze_message_returns_valid_payload():
    client = FakeLLMClient()
    result = analyze_message(client, "В Москве произошло ДТП")
    assert result.payload["event"]["title"] == "ДТП"
    assert result.model == "test-model"
    assert result.prompt_version == "analyzer_v2"
    assert "анализатор" in client.calls[0][0].lower()
