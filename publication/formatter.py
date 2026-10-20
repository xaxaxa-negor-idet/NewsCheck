# -*- coding: utf-8 -*-
"""Publication formatter v6: HTML hyperlinks — short labels, hidden URLs."""
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


def _link(label: str, url: str) -> str:
    """HTML hyperlink: short clickable label, URL hidden."""
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def _domain_label(url: str) -> str:
    """Extract short readable domain from URL for label."""
    try:
        from urllib.parse import urlsplit
        host = urlsplit(url).netloc.replace("www.", "")
        if not host:
            return url[:30]
        # Telegram post: @channel
        if "t.me" in host:
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                return f"@{parts[-2]}"
        return host
    except Exception:
        return url[:30]


def format_post(post: EventPost, updated_at: str | None = None) -> str:
    icon = STATUS_ICONS.get(post.status, "❔")
    lines = [
        escape(post.original_text),
        "",
        "─── NewsCheck ───",
        f"{icon} {escape(post.status)}",
    ]

    if post.status in ("CONFLICTING", "ТРЕБУЕТ ДОПОЛНИТЕЛЬНОЙ ПРОВЕРКИ", "INSUFFICIENT_DATA") and post.reason:
        lines.append(escape(post.reason))

    if post.source_links:
        lines.append("Подтверждения:")
        for idx, link in enumerate(post.source_links[:5], 1):
            domain = _domain_label(link)
            lines.append(_link(f"Подтверждение {idx} · {domain}", link))

    lines.append(f"Оригинал: {_link('@' + escape(post.source_channel), post.original_url or 'https://t.me/' + post.source_channel)}")

    if post.tags:
        lines.append(" ".join(f"#{tag.lstrip('#')}" for tag in post.tags[:5]))

    if updated_at:
        lines.append(f"Обновлено {escape(updated_at)}")
    return "\n".join(lines)
