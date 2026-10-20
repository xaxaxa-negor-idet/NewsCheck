# -*- coding: utf-8 -*-
"""Publication formatter: SPEC 11.1 — compact thesis output v2."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape


@dataclass(frozen=True)
class ClaimLine:
    text: str
    status: str
    sources: list[str] = None


@dataclass(frozen=True)
class EventPost:
    event_id: int
    original_text: str
    status: str
    reason: str
    claims: list[ClaimLine]
    source_links: list[str]
    source_channel: str
    original_url: str
    tags: list[str]

    def __post_init__(self):
        object.__setattr__(self, "claims", self.claims or [])
        object.__setattr__(self, "source_links", self.source_links or [])
        object.__setattr__(self, "tags", self.tags or [])


STATUS_ICONS = {
    "ПОДТВЕРЖДЕНО": "✅",
    "ЧАСТИЧНО ПОДТВЕРЖДЕНО": "🟡",
    "ОПРОВЕРГНУТО": "❌",
    "НЕ ПОДТВЕРЖДЕНО": "⚪",
    "CONFLICTING": "⚠️",
    "ТРЕБУЕТ ДОПОЛНИТЕЛЬНОЙ ПРОВЕРКИ": "❔",
    "INSUFFICIENT_DATA": "❔",
}


def format_post(post: EventPost, updated_at: str | None = None) -> str:
    icon = STATUS_ICONS.get(post.status, "❔")
    lines = [
        escape(post.original_text),
        "",
        "─── NewsCheck ───",
        f"{icon} {escape(post.status)}",
    ]

    # Compact claims: if all same status, one line; else list only differing ones
    if post.claims:
        statuses = {claim.status for claim in post.claims}
        if len(statuses) == 1 and post.status in ("ПОДТВЕРЖДЕНО", "ОПРОВЕРГНУТО"):
            # All claims same verdict — no need to list each
            lines.append(f"Тезисы: {escape(post.status)}")
        else:
            lines.append("Тезисы:")
            for claim in post.claims:
                sources = ", ".join(claim.sources or [])
                suffix = f" ({sources})" if sources else ""
                lines.append(f"• {escape(claim.text)}: {escape(claim.status)}{suffix}")

    if post.source_links:
        lines.append("Источники:")
        for link in post.source_links[:5]:
            lines.append(f"• {escape(link)}")

    lines.append(f"@{escape(post.source_channel)}")

    if post.tags:
        lines.append(" ".join(f"#{tag.lstrip('#')}" for tag in post.tags[:5]))

    if updated_at:
        lines.append(f"Обновлено {escape(updated_at)}")
    return "\n".join(lines)
