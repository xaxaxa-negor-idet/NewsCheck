# -*- coding: utf-8 -*-
from pathlib import Path
test = """from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from publication.formatter import EventPost, format_post


def test_guaranteed_blocks():
    post = EventPost(
        event_id=7,
        original_text="",
        status="",
        reason="",
        claims=[],
        source_links=[],
        source_channel="",
        original_url="",
        tags=[],
    )
    text = format_post(post)
    assert "\\u0431\\u0435\\u0437 \\u0442\\u0435\\u043a\\u0441\\u0442\\u0430" in text
    assert "─── NewsCheck ───" in text
    assert "\\u0422\\u0420\\u0415\\u0411\\u0423\\u0415\\u0422 \\u041f\\u0420\\u041e\\u0412\\u0415\\u0420\\u041a\\u0418" in text
    assert "\\u0410\\u0440\\u0433\\u0443\\u043c\\u0435\\u043d\\u0442:" in text
    assert "\\u041f\\u043e\\u0434\\u0442\\u0432\\u0435\\u0440\\u0436\\u0434\\u0435\\u043d\\u0438\\u044f:" in text
    assert "\\u043d\\u0435 \\u043d\\u0430\\u0439\\u0434\\u0435\\u043d\\u043e" in text
    assert "\\u041e\\u0440\\u0438\\u0433\\u0438\\u043d\\u0430\\u043b: @unknown" in text
    assert "\\u041f\\u043e\\u0441\\u0442: <a href=" in text
    assert "ID: #7" in text


def test_full_blocks():
    post = EventPost(
        event_id=5,
        original_text="Full text",
        status="\\u041e\\u041f\\u0420\\u041e\\u0412\\u0415\\u0420\\u0413\\u041d\\u0423\\u0422\\u041e",
        reason="reason text",
        claims=[],
        source_links=["https://a.com/x", "https://b.com/y"],
        source_channel="chan",
        original_url="https://t.me/chan/9",
        tags=["tag"],
    )
    text = format_post(post)
    assert "\\u041c\\u0418\\u0424" in text
    assert "reason text" in text
    assert "Подтверждение 1 · a.com" in text
    assert "Подтверждение 2 · b.com" in text
    assert "ID: #5" in text
"""
Path("tests/test_formatter.py").write_bytes(test.encode("utf-8"))
print('ok')
