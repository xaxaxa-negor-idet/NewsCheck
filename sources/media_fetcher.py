"""Media fetcher: SPEC 6.3, 17.1 — idempotent photo downloads by hash."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent


def download_media(url: str, media_dir: Path | None = None, session: requests.Session | None = None) -> tuple[Path, str, int]:
    if not url.startswith(("http://", "https://")):
        raise ValueError("only absolute http(s) URLs are supported")

    requester = session or requests
    response = requester.get(url, timeout=30)
    response.raise_for_status()

    payload = response.content
    digest = hashlib.sha256(payload).hexdigest()
    suffix = Path(urlparse(url).path).suffix or ".bin"

    base_dir = media_dir or ROOT / "media"
    directory = base_dir / digest[:2]
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{digest}{suffix}"

    if not target.exists():
        target.write_bytes(payload)
    return target, digest, len(payload)
