from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from publication.formatter import ClaimLine, EventPost, format_post


def test_template_structure():
    post = EventPost(
        event_id=1,
        original_text="Original news text",
        status="????????????",
        reason="???????? ???????? ?????????",
        claims=[],
        source_links=["https://example.com/a"],
        source_channel="topor",
        original_url="https://t.me/topor/53123",
        tags=[],
    )
    text = format_post(post)
    assert "??? NewsCheck ???" in text
    assert "???" in text
    assert "????????:" in text
    assert "?????????????:" in text
    assert "????????: @topor" in text
    assert "????:" in text
    assert "ID: #1" in text
    assert '<a href=' in text


def test_template_confirmed():
    post = EventPost(
        event_id=1,
        original_text="Text",
        status="????????????",
        reason="",
        claims=[],
        source_links=["https://a.com", "https://b.com"],
        source_channel="chan",
        original_url="https://t.me/chan/9",
        tags=[],
    )
    text = format_post(post)
    assert "?? ???" in text
    assert "????????: @chan" in text
    assert "????:" in text
