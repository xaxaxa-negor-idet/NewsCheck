"""Status Calculator: SPEC 9 / 17.6 — deterministic, no LLM."""
from __future__ import annotations

from dataclasses import dataclass

from enum import Enum


class ClaimStatus(str, Enum):
    NOT_CHECKED = "NOT_CHECKED"
    CONFIRMED = "CONFIRMED"
    REFUTED = "REFUTED"
    CONFLICTING = "CONFLICTING"
    UNCONFIRMED = "UNCONFIRMED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class EventStatus(str, Enum):
    CONFIRMED = "ПОДТВЕРЖДЕНО"
    PARTIAL = "ЧАСТИЧНО ПОДТВЕРЖДЕНО"
    REFUTED = "ОПРОВЕРГНУТО"
    UNCONFIRMED = "НЕ ПОДТВЕРЖДЕНО"
    CONFLICTING = "CONFLICTING"
    NEEDS_CHECK = "ТРЕБУЕТ ДОПОЛНИТЕЛЬНОЙ ПРОВЕРКИ"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class ClaimVerdict:
    status: ClaimStatus
    is_key: bool
    independent_support: int = 0
    direct_refutation: bool = False


@dataclass(frozen=True)
class StatusExplanation:
    status: EventStatus
    reason: str


def calculate_status(claims: list[ClaimVerdict]) -> StatusExplanation:
    key_claims = [claim for claim in claims if claim.is_key]

    if key_claims and all(claim.status == ClaimStatus.INSUFFICIENT_DATA for claim in key_claims):
        return StatusExplanation(EventStatus.INSUFFICIENT_DATA, "Недостаточно данных для ключевых утверждений")

    if any(claim.status == ClaimStatus.REFUTED and claim.direct_refutation for claim in key_claims):
        return StatusExplanation(EventStatus.REFUTED, "Ключевое утверждение прямо опровергнуто источником")

    if any(claim.status == ClaimStatus.CONFLICTING for claim in key_claims):
        return StatusExplanation(EventStatus.CONFLICTING, "Источники противоречат друг другу по ключевому утверждению")

    confirmed = [claim for claim in key_claims if claim.status == ClaimStatus.CONFIRMED]
    unresolved = [claim for claim in key_claims if claim.status in (ClaimStatus.NOT_CHECKED, ClaimStatus.INSUFFICIENT_DATA)]

    if unresolved:
        return StatusExplanation(EventStatus.NEEDS_CHECK, "Часть ключевых утверждений ещё не проверена")

    if confirmed and len(confirmed) == len(key_claims):
        return StatusExplanation(EventStatus.CONFIRMED, "Все ключевые утверждения подтверждены")

    if confirmed:
        return StatusExplanation(EventStatus.PARTIAL, "Подтверждена часть ключевых утверждений")

    return StatusExplanation(EventStatus.UNCONFIRMED, "Подтверждений по ключевым утверждениям не найдено")
