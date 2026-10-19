from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from search.url import canonicalize_url, url_hash


def test_scheme_host_and_slashes():
    assert canonicalize_url("HTTP://Example.com/news/") == "https://example.com/news"


def test_utm_removed_and_params_sorted():
    assert canonicalize_url("https://example.com/news?utm_source=x&b=2&a=1") == "https://example.com/news?a=1&b=2"


def test_hash_is_stable_for_equivalent_urls():
    assert url_hash("http://example.com/news/?utm_source=x") == url_hash("https://example.com/news")
