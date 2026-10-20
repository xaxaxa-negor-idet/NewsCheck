from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from publication.formatter import ClaimLine, EventPost, format_post


def test_format_post_hyperlinks():
    post = EventPost(
        event_id=1,
        original_text="News text",
        status="PARTIAL",
        reason="reason",
        claims=[],
        source_links=["https://example.com/a", "https://t.me/chan/123"],
        source_channel="topor",
        original_url="https://t.me/topor/100",
        tags=["news"],
    )
    text = format_post(post)
    assert '<a href="https://example.com/a">' in text
    assert 'Подтверждение 1' in text
    assert '<a href="https://t.me/topor/100">@topor</a>' in text


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
