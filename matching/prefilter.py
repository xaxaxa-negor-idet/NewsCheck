"""Cheap event matcher prefilter: SPEC 10.1 step 1."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class EventCandidate:
    event_id: int
    location: str | None
    event_date: date | None
    event_type: str | None
    entities: set[str]


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def cheap_filter(
    candidate: EventCandidate,
    new_location: str | None,
    new_date: date | None,
    new_event_type: str | None,
    new_entities: set[str],
    window_days: int = 3,
) -> bool:
    if candidate.event_date is None or new_date is None:
        return False
    if abs((candidate.event_date - new_date).days) > window_days:
        return False
    if not candidate.event_type or not new_event_type or candidate.event_type.lower() != new_event_type.lower():
        return False
    if not candidate.location or not new_location or candidate.location.lower() != new_location.lower():
        return False
    return bool(candidate.entities & new_entities)
