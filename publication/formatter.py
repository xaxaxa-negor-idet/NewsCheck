"""Publication formatter: SPEC 11.1."""
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
    lines = [escape(post.original_text), "", "─── NewsCheck ───", f"Статус: {icon} {escape(post.status)}", f"Почему: {escape(post.reason)}"]

    if post.claims:
        lines.append("Утверждения:")
        for claim in post.claims:
            sources = ", ".join(claim.sources or [])
            suffix = f" — {sources}" if sources else ""
            lines.append(f"{escape(claim.text)}: {escape(claim.status)}{suffix}")

    if post.source_links:
        lines.append("Источники: " + ", ".join(escape(link) for link in post.source_links))

    lines.append(f"Источник: @{escape(post.source_channel)} · {escape(post.original_url)}")

    if post.tags:
        lines.append(" ".join(f"#{tag.lstrip('#')}" for tag in post.tags))

    if updated_at:
        lines.append(f"Обновлено {escape(updated_at)}")
    return "\n".join(lines)
