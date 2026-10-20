"""Telegram public web-preview source adapter. SPEC 5.2, 5.5."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from html import unescape
from typing import Literal

import requests

BASE_URL = "https://t.me/s/{channel}"


@dataclass(frozen=True)
class SourceMessage:
    source_channel: str
    source_message_id: str
    text: str
    media: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    source_url: str = ""
    edited_at: datetime | None = None
    received_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class PollResult:
    kind: Literal["OK", "EMPTY", "UNAVAILABLE"]
    messages: list[SourceMessage] = field(default_factory=list)
    reason: str | None = None


def _text_to_plain(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _extract_links(html: str) -> list[str]:
    return re.findall(r'<a[^>]+href="([^"]+)"', html)


def parse_public_page(html: str, channel: str) -> list[SourceMessage]:
    messages = []
    blocks = re.split(r'(?=<div class="tgme_widget_message_wrap)', html)
    for block in blocks[1:]:
        id_match = re.search(r'data-post="' + re.escape(channel) + r'/(\d+)"', block)
        if not id_match:
            continue
        message_id = id_match.group(1)

        text_match = re.search(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', block, re.S
        )
        text = _text_to_plain(text_match.group(1)) if text_match else ""

        # Links inside message text must survive to the final post
        inline_links = _extract_links(text_match.group(1)) if text_match else []
        text = _merge_links_into_text(text, inline_links)

        # Inline text links are part of content, not media
        media = [u for u in _extract_links(block) if "cdn" in u]
        media += re.findall(r"background-image:url\('([^']+)'\)", block)

        # Extract <video> sources (mp4 links) ? public preview videos
        video_matches = re.findall(r'<video[^>]+src="([^"]+\.mp4[^"]*)"', block)
        for video_url in video_matches:
            if video_url not in media:
                media.append(video_url)

        # Extract <source> tags inside <video>
        source_matches = re.findall(r'<source[^>]+src="([^"]+\.mp4[^"]*)"', block)
        for video_url in source_matches:
            if video_url not in media:
                media.append(video_url)

        time_match = re.search(r'<time[^>]+datetime="([^"]+)"', block)
        published_at = datetime.fromisoformat(time_match.group(1)) if time_match else None

        edited_match = re.search(r'<span class="tgme_widget_message_edited[^"]*"[^>]*>edited', block)
        edited_at = published_at if edited_match else None

        messages.append(
            SourceMessage(
                source_channel=channel,
                source_message_id=message_id,
                text=text,
                media=media,
                published_at=published_at,
                source_url=f"https://t.me/{channel}/{message_id}",
                edited_at=edited_at,
            )
        )
    return messages


def list_messages(
    channel: str,
    since: datetime | None = None,
    session: requests.Session | None = None,
) -> PollResult:
    url = BASE_URL.format(channel=channel)
    try:
        requester = session or requests
        response = requester.get(
            url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 NewsCheck/0.1"},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return PollResult(kind="UNAVAILABLE", reason=f"{type(exc).__name__}: {exc}")

    messages = parse_public_page(response.text, channel)
    if since is not None:
        messages = [message for message in messages if message.published_at and message.published_at > since]
    return PollResult(kind="OK" if messages else "EMPTY", messages=messages)


def _merge_links_into_text(text: str, links: list[str]) -> str:
    """Keep links that were words in the original post: append if not already present."""
    for link in links:
        if link and link not in text:
            text = text.rstrip() + "\n" + link
    return text
