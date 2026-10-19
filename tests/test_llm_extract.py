import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.llm_client import extract_json


def test_extract_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_fenced_json():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_text():
    assert extract_json('Ответ:\n{"a": 1}') == {"a": 1}


def test_invalid_returns_none():
    assert extract_json('no json here') is None
    assert extract_json('[1,2,3]') is None
