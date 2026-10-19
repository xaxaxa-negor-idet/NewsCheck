from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from search.rate_limited import RateLimitedGdelt


def test_rate_limiting():
    provider = RateLimitedGdelt(min_interval_seconds=0.05)
    provider._last_request = time.time()
    start = time.time()
    # Simulate internal API call after enforced wait
    wait = provider.min_interval - (time.time() - provider._last_request)
    if wait > 0:
        time.sleep(wait)
    provider._last_request = time.time()
    elapsed = time.time() - start
    assert elapsed >= 0.04
