"""URL canonicalization: SPEC 8.3 / 17.13."""
from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}


def canonicalize_url(url: str) -> str:
    split = urlsplit(url.strip())
    scheme = "https"
    host = split.netloc.lower()
    path = split.path.rstrip("/") or "/"

    query_pairs = sorted(
        (key, value)
        for key, value in parse_qsl(split.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    )
    query = urlencode(query_pairs, doseq=True)

    return urlunsplit((scheme, host, path, query, ""))


def url_hash(url: str) -> str:
    canonical = canonicalize_url(url)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
