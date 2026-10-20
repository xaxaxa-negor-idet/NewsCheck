from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sources.telegram_web import parse_public_page


def test_inline_links_preserved():
    html = (
        '<div class="tgme_widget_message_wrap">'
        '<div class="tgme_widget_message" data-post="ch/1">'
        '<div class="tgme_widget_message_text js-message_text">Bet here <a href="https://example.com/promo">https://example.com/promo</a></div>'
        '<time datetime="2026-10-20T12:00:00+00:00"></time>'
        '</div></div>'
    )
    msgs = parse_public_page(html, "ch")
    assert len(msgs) == 1
    assert "https://example.com/promo" in msgs[0].text


def test_no_link_no_change():
    html = (
        '<div class="tgme_widget_message_wrap">'
        '<div class="tgme_widget_message" data-post="ch/2">'
        '<div class="tgme_widget_message_text js-message_text">Plain text only</div>'
        '</div></div>'
    )
    msgs = parse_public_page(html, "ch")
    assert msgs[0].text == "Plain text only"
