from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from search.page_fetcher import fetch_page


class FakeResponse:
    status_code = 200
    content = b"<html><head><title>Title</title></head><body><script>bad()</script><p>Paragraph</p></body></html>"
    def raise_for_status(self):
        pass


class FakeSession:
    def get(self, url, timeout=30, headers=None):
        return FakeResponse()


def test_extracts_title_and_text():
    snapshot = fetch_page("https://example.com/news", FakeSession())
    assert snapshot.title == "Title"
    assert "Paragraph" in snapshot.text
    assert "bad()" not in snapshot.text
    assert snapshot.domain == "example.com"
