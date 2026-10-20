# -*- coding: utf-8 -*-
from pathlib import Path
test = '''from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from publication.formatter import ClaimLine, EventPost, format_post


def test_format_post_contains_blocks():
    post = EventPost(
        event_id=1,
        original_text="Moskva proizoshlo DTP",
        status="CHASTICHNO",
        reason="fakt podtverzhden",
        claims=[ClaimLine("DTP proizoshlo", "CONFIRMED", ["https://example.com"])],
        source_links=["https://example.com"],
        source_channel="topor",
        original_url="https://t.me/topor/100",
        tags=["news"],
    )
    text = format_post(post)
    assert "NewsCheck" in text
    assert "DTP proizoshlo" in text
    assert "https://example.com" in text
    assert "@topor" in text


def test_partial_shows_claims():
    post = EventPost(
        event_id=1,
        original_text="Test",
        status="CHASTICHNO",
        reason="raznye verdikty",
        claims=[
            ClaimLine("tezis 1", "CONFIRMED"),
            ClaimLine("tezis 2", "UNCONFIRMED"),
        ],
        source_links=["https://example.com"],
        source_channel="topor",
        original_url="https://t.me/topor/1",
        tags=[],
    )
    text = format_post(post)
    assert "tezis 1" in text
    assert "tezis 2" in text
'''
Path("tests/test_formatter.py").write_bytes(test.encode("utf-8"))
print("ok")
