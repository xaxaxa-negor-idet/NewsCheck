# -*- coding: utf-8 -*-
"""B1: Telegram RSS service probe (multi-service).

Protocol: SPEC 18.1 — poll candidate services, log each request
(success/code/latency). One-shot writes JSONL; long-run mode is reserved
for the 7-day availability series.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import feedparser
import requests

SERVICES = {
    "rsshub": "https://rsshub.app/telegram/channel/{channel}",
    "tgstat": "https://rss.app/feeds/{channel}.xml",
}


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


def probe(channel: str, service: str, url_template: str) -> ProbeResult:
    url = url_template.format(channel=channel)
    started = time.perf_counter()
    status: int | None = None
    error: str | None = None
    entries = 0
    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": "NewsCheck/0.1 (+validation)"})
        status = response.status_code
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        entries = len(parsed.entries)
        if entries == 0:
            error = "EMPTY_FEED"
    except requests.RequestException as exc:
        error = f"{type(exc).__name__}: {exc}"
    latency = int((time.perf_counter() - started) * 1000)
    return ProbeResult(
        service=service,
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
    parser.add_argument("--services", nargs="*", default=list(SERVICES))
    parser.add_argument("--out", default="validation/b1_rss_probe.jsonl")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = [
        probe(channel, service, SERVICES[service])
        for service in args.services
        for channel in args.channels
    ]
    with out_path.open("a", encoding="utf-8") as stream:
        for result in results:
            stream.write(result.to_jsonl() + "\n")
    print("\n".join(result.to_jsonl() for result in results))
    return 0 if any(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
