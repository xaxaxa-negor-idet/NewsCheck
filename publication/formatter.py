# -*- coding: utf-8 -*-
"""Publication formatter v8 — bulletproof template with guaranteed blocks."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from urllib.parse import urlsplit


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


def _domain(url: str) -> str:
    try:
        host = urlsplit(url).netloc.replace("www.", "")
        if "t.me" in host:
            parts = [p for p in urlsplit(url).path.split("/") if p]
            if parts:
                return f"@{parts[0]}"
        return host or url[:28]
    except Exception:
        return url[:28]


def _verdict(status: str) -> str:
    s = (status or "").upper()
    if "ОПРОВЕРГНУТО" in s:
        return "МИФ"
    if "ПОДТВЕРЖ" in s and "ЧАСТИЧНО" not in s:
        return "НЕ МИФ"
    if "ЧАСТИЧНО" in s:
        return "ЧАСТИЧНЫЙ МИФ"
    if "CONFLICT" in s or "ПРОТИВОРЕЧ" in s:
        return "ПРОТИВОРЕЧИВО"
    return "ТРЕБУЕТ ПРОВЕРКИ"


def format_post(post: EventPost, updated_at: str | None = None) -> str:
    icon = STATUS_ICONS.get(post.status, "❔")
    verdict = _verdict(post.status)

    # Block 1: original text — NEVER empty
    original = (post.original_text or "").strip() or "(без текста)"

    # Block 2: argument
    if verdict == "НЕ МИФ":
        argument = f"✅ Подтверждено {len(post.source_links)} независимыми источниками"
    elif post.reason:
        argument = f"Аргумент: {post.reason}"
    else:
        argument = "Аргумент: недостаточно надёжных подтверждений по ключевым фактам"

    # Block 3: sources — always the section header, links if any
    source_lines = []
    if post.source_links:
        for idx, url in enumerate(post.source_links[:5], 1):
            source_lines.append(_link(f"Подтверждение {idx} · {_domain(url)}", url))

    # Block 4: post URL — ALWAYS present, built from channel if missing
    post_url = post.original_url or f"https://t.me/{post.source_channel or 'unknown'}"

    lines = [
        escape(original),
        "",
        "─── NewsCheck ───",
        f"{icon} {verdict}",
        argument,
        "",
        "Подтверждения:",
    ]
    if source_lines:
        lines.extend(source_lines)
    else:
        lines.append("— не найдено надёжных источников")
    lines.extend([
        "",
        f"Оригинал: @{escape(post.source_channel or 'unknown')}",
        f"Пост: {_link(post_url, post_url)}",
        f"ID: #{post.event_id}",
    ])
    if post.tags:
        lines.append("")
        lines.append(" ".join(f"#{t.lstrip('#')}" for t in post.tags[:5]))
    if updated_at:
        lines.append(f"Обновлено {escape(updated_at)}")
    return "\n".join(lines)
