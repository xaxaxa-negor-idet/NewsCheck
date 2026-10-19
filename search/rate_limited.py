"""Search provider with rate limiting: SPEC 8.1, 17.19."""
from __future__ import annotations

import time
from typing import Callable

from search.gdelt import SearchResult, search as gdelt_search


class RateLimitedGdelt:
    """GDELT allows only 1 request per 5+ seconds."""

    def __init__(self, min_interval_seconds: float = 6.0):
        self.min_interval = min_interval_seconds
        self._last_request = 0.0

    def search(self, query: str) -> list[SearchResult]:
        elapsed = time.time() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request = time.time()
        return gdelt_search(query)

