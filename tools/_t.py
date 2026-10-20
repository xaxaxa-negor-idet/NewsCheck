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
        status="ОПРОВЕРГНУТО",
        reason="Источник опроверг заявление",
        claims=[],
        source_links=["https://example.com/a"],
        source_channel="topor",
        original_url="https://t.me/topor/53123",
        tags=[],
    )
    text = format_post(post)
    assert lines_ok(text)


def lines_ok(text):
    assert "─── NewsCheck ───" in text
    assert "МИФ" in text
    assert "Аргумент:" in text
    assert "Подтверждения:" in text
    assert "Оригинал: @topor" in text
    assert "Пост:" in text
    assert "ID: #1" in text
    assert '<a href=' in text
    return True


def test_template_confirmed():
    post = EventPost(
        event_id=1,
        original_text="Text",
        status="ПОДТВЕРЖДЕНО",
        reason="",
        claims=[],
        source_links=["https://a.com", "https://b.com"],
        source_channel="chan",
        original_url="https://t.me/chan/9",
        tags=[],
    )
    text = format_post(post)
    assert "НЕ МИФ" in text
    assert "Оригинал: @chan" in text
    assert "Пост:" in text
"""
Path("tests/test_formatter.py").write_bytes(test.encode("utf-8"))
print('ok')
