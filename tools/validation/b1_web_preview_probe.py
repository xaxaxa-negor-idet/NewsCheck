# -*- coding: utf-8 -*-
"""B1: Telegram public web preview probe.

Protocol: SPEC 18.1 — poll candidate services, log each request
(success/code/latency). Public t.me/s pages are a viable fallback
adapter; RSSHub/rss.app require per-deployment configuration.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

@dataclass
class ProbeResult:
    service: str
    channel: str
    url: str
    ok: bool
    http_status: int | None
    entries: int
    latency_ms: int
    error: str | None
    checked_at: str

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def probe(channel: str) -> ProbeResult:
    url = f"https://t.me/s/{channel}"
    started = time.perf_counter()
    status: int | None = None
    error: str | None = None
    entries = 0
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsCheck/0.1"},
        )
        status = response.status_code
        response.raise_for_status()
        entries = len(re.findall(r'class="tgme_widget_message', response.text))
        if entries == 0:
            error = "EMPTY_FEED"
    except requests.RequestException as exc:
        error = f"{type(exc).__name__}: {exc}"
    latency = int((time.perf_counter() - started) * 1000)
    return ProbeResult(
        service="t.me_public_web",
        channel=channel,
        url=url,
        ok=error is None,
        http_status=status,
        entries=entries,
        latency_ms=latency,
        error=error,
        checked_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channels", nargs="*", default=["durov", "telegram", "bbbreaking"])
    parser.add_argument("--out", default="validation/b1_rss_probe.jsonl")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = [probe(channel) for channel in args.channels]
    with out_path.open("a", encoding="utf-8") as stream:
        for result in results:
            stream.write(result.to_jsonl() + "\n")
    print("\n".join(result.to_jsonl() for result in results))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
