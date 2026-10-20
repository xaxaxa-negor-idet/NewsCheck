# -*- coding: utf-8 -*-
"""Robust single-source freshness and relevance gate."""
from __future__ import annotations

import re

from datetime import datetime, timedelta, timezone


def parse_published(raw) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        dt = raw
    else:
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_fresh(published_at, max_age_hours: float = 24.0) -> bool:
    dt = parse_published(published_at)
    if dt is None:
        return True
    return datetime.now(timezone.utc) - dt <= timedelta(hours=max_age_hours)


def _stem(w: str) -> str:
    for suf in ("иями", "ями", "ами", "иях", "ях", "ах", "ов", "ев", "ей", "ой",
                "ая", "ое", "ее", "ый", "ий", "ем", "ом", "ам", "ум", "ых",
                "ие", "ии", "е", "у", "а", "я", "о", "ы", "и"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def same_incident_keywords(source_title: str, source_text: str, event_title: str) -> bool:
    def words(s):
        raw = re.sub(r"[^\w\sа-яё]", " ", (s or "").lower()).split()
        return set(_stem(w) for w in raw if len(w) > 2)
    ev = words(event_title)
    if not ev:
        return True
    src = words((source_title or "") + " " + (source_text or "")[:600])
    if not src:
        return False
    overlap = len(ev & src)
    if len(ev) <= 2:
        return overlap >= 1
    return overlap >= max(1, int(0.3 * len(ev)))
