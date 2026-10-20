# -*- coding: utf-8 -*-
"""Publication formatter v7 — strict template.

Template per user spec:
  1. photo/video from original post  (sent via sendPhoto/sendVideo, caption = rest)
  2. original text
  3. ─── NewsCheck ───
  4. МИФ / НЕ МИФ line
  5. argument why (if myth / partial)
  6. Подтверждения: [links]
  7. Оригинал: @username
  8. Пост: [exact post url]
"""
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
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def _domain_label(url: str) -> str:
    try:
        from urllib.parse import urlsplit
        parts = urlsplit(url)
        host = parts.netloc.replace("www.", "")
        if "t.me" in host and parts.path:
            seg = [p for p in parts.path.split("/") if p]
            if len(seg) >= 2:
                return f"@{seg[0]}"
        return host or url[:30]
    except Exception:
        return url[:30]


def _verdict_line(status: str) -> str:
    """Map event status to myth/not-myth verdict."""
    s = status.upper()
    if "ОПРОВЕРГНУТО" in s:
        return "МИФ"
    if "ПОДТВЕРЖ" in s and "ЧАСТИЧНО" not in s:
        return "НЕ МИФ"
    if "ЧАСТИЧНО" in s:
        return "ЧАСТИЧНЫЙ МИФ"
    if "CONFLICT" in s or "ПРОТИВОРЕЧ" in s:
        return "ПРОТИВОРЕЧИВО"
    if "ТРЕБУЕТ" in s or "INSUFFICIENT" in s:
        return "ТРЕБУЕТ ПРОВЕРКИ"
    return "НЕ ПОДТВЕРЖДЕНО"


def format_post(post: EventPost, updated_at: str | None = None) -> str:
    icon = STATUS_ICONS.get(post.status, "❔")
    verdict = _verdict_line(post.status)

    lines = [
        escape(post.original_text),
        "",
        "─── NewsCheck ───",
        f"{icon} {verdict}",
    ]

    # Argument: always show for non-confirmed; for confirmed show brief confirmation
    if verdict == "НЕ МИФ":
        lines.append(f"✅ Подтверждено независимыми источниками ({len(post.source_links)})")
    elif post.reason:
        lines.append(f"Аргумент: {escape(post.reason)}")
    else:
        lines.append("Аргумент: недостаточно подтверждений по ключевым утверждениям")

    if post.source_links:
        lines.append("")
        lines.append("Подтверждения:")
        for idx, link in enumerate(post.source_links[:5], 1):
            lines.append(_link(f"Подтверждение {idx} · {_domain_label(link)}", link))

    lines.append("")
    lines.append(f"Оригинал: @{escape(post.source_channel)}")

    post_url = post.original_url or f"https://t.me/{post.source_channel}"
    lines.append(f"Пост: {_link(post_url, post_url)}")
    lines.append(f"ID: #{post.event_id}")

    if post.tags:
        lines.append("")
        lines.append(" ".join(f"#{t.lstrip('#')}" for t in post.tags[:5]))

    return "\n".join(lines)
