from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from search.google_news import SearchResult, search


class FakeResponse:
    status_code = 200
    content = b'''<?xml version="1.0"?>
<rss version="2.0"><channel>
<item>
<title>Test article</title>
<link>https://example.com/news</link>
<description>Test description</description>
<pubDate>Mon, 20 Oct 2026 12:00:00 +0000</pubDate>
<source url="https://example.com">Example News</source>
</item>
</channel></rss>'''
    def raise_for_status(self):
        pass


class FakeSession:
    def get(self, url, params, timeout, headers=None):
        assert "news.google.com" in url
        return FakeResponse()


def test_google_news_search():
    results = search("test query", FakeSession())
    assert len(results) == 1
    assert results[0].title == "Test article"
    assert results[0].url == "https://example.com/news"
    assert results[0].snippet == "Test description"
    assert results[0].domain == "Example News"
    assert results[0].published_at is not None
