"""Simple prefilter: SPEC 5.6 — cheap rules before LLM."""
from __future__ import annotations

import re

AD_MARKERS = re.compile(
    r"(#\w+.*#\w+|реклама|подпишись|подписывайтесь|казино|ставк[аи]|промокод|telegram\s*premium)",
    re.IGNORECASE,
)


def should_process(text: str, min_length: int = 25, ad_markers: str | None = None) -> bool:
    if len(text.strip()) < min_length:
        return False
    if ad_markers and re.search(ad_markers, text, re.IGNORECASE):
        return False
    if AD_MARKERS.search(text):
        return False
    return True
