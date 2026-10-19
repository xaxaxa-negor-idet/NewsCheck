# -*- coding: utf-8 -*-
"""Recheck scheduler: SPEC 12.1, 12.2, 12.3."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


DEFAULT_RECHECK_DELAYS_HOURS = (1, 2, 6, 12)


@dataclass(frozen=True)
class RecheckSchedule:
    next_recheck_at: datetime | None
    recheck_count: int
    status: str


def schedule_recheck(
    current_count: int,
    max_rechecks: int = 4,
    delays_hours: tuple[int, ...] = DEFAULT_RECHECK_DELAYS_HOURS,
    now: datetime | None = None,
) -> RecheckSchedule:
    base = now or datetime.now()
    if current_count >= max_rechecks:
        return RecheckSchedule(None, current_count, "RECHECK_LIMIT_REACHED")

    delay_index = min(current_count, len(delays_hours) - 1)
    delay = delays_hours[delay_index]
    next_at = base + timedelta(hours=delay)
    return RecheckSchedule(next_at, current_count + 1, "ACTIVE")


def should_archive(last_updated: datetime, now: datetime | None = None, days: int = 7) -> bool:
    current = now or datetime.now()
    return (current - last_updated).days >= days
