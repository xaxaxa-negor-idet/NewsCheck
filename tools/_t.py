# -*- coding: utf-8 -*-
from pathlib import Path
test = """from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from publication.formatter import ClaimLine, EventPost, format_post


def test_template_structure():
    post = EventPost(
        event_id=1,
        original_text="Original news text",
        status="\\u041e\\u041f\\u0420\\u041e\\u0412\\u0415\\u0420\\u0413\\u041d\\u0423\\u0422\\u041e",
        reason="arg",
        claims=[],
        source_links=["https://example.com/a"],
        source_channel="topor",
        original_url="https://t.me/topor/53123",
        tags=[],
    )
    text = format_post(post)
    assert "─── NewsCheck ───" in text
    assert "\\u041c\\u0418\\u0424" in text
    assert "\\u041f\\u043e\\u0434\\u0442\\u0432\\u0435\\u0440\\u0436\\u0434\\u0435\\u043d\\u0438\\u044f:" in text
    assert "\\u041e\\u0440\\u0438\\u0433\\u0438\\u043d\\u0430\\u043b: @topor" in text
    assert "\\u041f\\u043e\\u0441\\u0442:" in text
    assert "ID: #1" in text


def test_template_confirmed():
    post = EventPost(
        event_id=1,
        original_text="Text",
        status="\\u041f\\u041e\\u0414\\u0422\\u0412\\u0415\\u0420\\u0416\\u0414\\u0415\\u041d\\u041e",
        reason="",
        claims=[],
        source_links=["https://a.com"],
        source_channel="chan",
        original_url="https://t.me/chan/9",
        tags=[],
    )
    text = format_post(post)
    assert "\\u041d\\u0415 \\u041c\\u0418\\u0424" in text
    assert "\\u041f\\u043e\\u0441\\u0442:" in text
"""
Path("tests/test_formatter.py").write_bytes(test.encode("utf-8"))
print('ok')
