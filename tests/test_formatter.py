from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from publication.formatter import ClaimLine, EventPost, format_post


def test_format_post_blocks():
    post = EventPost(
        event_id=1,
        original_text="News text",
        status="PARTIAL",
        reason="reason",
        claims=[],
        source_links=["https://example.com"],
        source_channel="topor",
        original_url="https://t.me/topor/100",
        tags=["news"],
    )
    text = format_post(post)
    assert "NewsCheck" in text
    assert "[1]" in text
    assert "https://t.me/topor/100" in text
    assert "@topor" in text


def test_no_claims():
    post = EventPost(
        event_id=1,
        original_text="Test",
        status="CONFIRMED",
        reason="",
        claims=[ClaimLine("thesis", "CONFIRMED")],
        source_links=["https://example.com"],
        source_channel="topor",
        original_url="",
        tags=[],
    )
    text = format_post(post)
    assert "thesis" not in text
