from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime

from search.gdelt import SearchResult, search


class FakeResponse:
    status_code = 200
    def json(self):
        return {
            "articles": [
                {
                    "url": "https://example.com/news",
                    "title": "Title",
                    "snippet": "Snippet",
                    "domain": "example.com",
                    "seendate": "20261020T120000Z",
                },
                {"title": "broken", "seendate": "bad"},
            ]
        }
    def raise_for_status(self):
        pass


class FakeSession:
    def get(self, url, params, timeout):
        assert params["query"] == "test"
        return FakeResponse()


def test_parses_gdelt_response():
    results = search("test", FakeSession())
    assert results == [SearchResult(
        url="https://example.com/news",
        title="Title",
        snippet="Snippet",
        domain="example.com",
        published_at=datetime(2026, 10, 20, 12, 0),
    )]
