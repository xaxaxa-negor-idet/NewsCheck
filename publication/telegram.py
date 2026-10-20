# -*- coding: utf-8 -*-
"""Bulletproof Telegram destination: media always via bytes, HTML always on, retries everywhere."""
from __future__ import annotations

import time

import requests

from publication.console import PublicationResult, RenderedPost


class RenderedPostWithMedia(RenderedPost):
    def __init__(self, event_id: int, text: str, media_url: str | None = None, media_kind: str = "photo"):
        super().__init__(event_id=event_id, text=text)
        object.__setattr__(self, "media_url", media_url)
        object.__setattr__(self, "media_kind", media_kind)


class TelegramChannelDestination:
    name = "telegram"
    MAX_RETRIES = 4

    def __init__(self, bot_token: str, channel_id: str, timeout: int = 120):
        if not bot_token:
            raise ValueError("bot token is required")
        if not channel_id:
            raise ValueError("channel id is required")
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.timeout = timeout
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "NewsCheck/1.0"})

    def _post(self, method: str, payload: dict) -> dict:
        last_exc = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.post(
                    f"{self.base_url}/{method}", json=payload, timeout=self.timeout
                )
                data = response.json()
                if data.get("ok"):
                    return data["result"]
                last_exc = RuntimeError(f"Telegram API error: {data.get('description', '')}")
                if data.get("error_code") == 400:
                    break
            except Exception as exc:
                last_exc = exc
            time.sleep(2 * (attempt + 1))
        raise last_exc or RuntimeError(f"telegram {method} failed")

    def _fetch_media(self, url: str) -> tuple[bytes, str] | None:
        """Download media bytes; detect kind by magic numbers."""
        for attempt in range(self.MAX_RETRIES):
            try:
                r = self.session.get(url, timeout=60)
                if r.status_code == 200 and len(r.content) > 5000:
                    head = r.content[:12]
                    if head[:3] == b"\xff\xd8\xff" or head[:4] == bytes([0x89, 0x50, 0x4E, 0x47]):
                        return r.content, "photo"
                    if head[:4] == b"\x00\x00\x00\x14" or b"ftyp" in head:
                        return r.content, "video"
                    if url.lower().endswith((".mp4", ".mov")) or ".mp4" in url.lower():
                        return r.content, "video"
                    return r.content, "photo"
            except Exception:
                pass
            time.sleep(2 * (attempt + 1))
        return None

    def publish(self, rendered: RenderedPost) -> PublicationResult:
        media_url = getattr(rendered, "media_url", None)
        caption = rendered.text[:1024]

        if media_url:
            media = self._fetch_media(media_url)
            if media:
                data_bytes, kind = media
                if kind == "video":
                    method, field, fname, mime = "sendVideo", "video", "video.mp4", "video/mp4"
                else:
                    method, field, fname, mime = "sendPhoto", "photo", "photo.jpg", "image/jpeg"
                for attempt in range(self.MAX_RETRIES):
                    try:
                        response = self.session.post(
                            f"{self.base_url}/{method}",
                            data={"chat_id": self.channel_id, "caption": caption, "parse_mode": "HTML"},
                            files={field: (fname, data_bytes, mime)},
                            timeout=self.timeout,
                        )
                        result = response.json()
                        if result.get("ok"):
                            return PublicationResult(
                                "telegram", str(result["result"]["message_id"]), rendered.text
                            )
                        if result.get("error_code") == 400:
                            break
                    except Exception:
                        pass
                    time.sleep(2 * (attempt + 1))

        result = self._post(
            "sendMessage",
            {"chat_id": self.channel_id, "text": rendered.text, "parse_mode": "HTML"},
        )
        return PublicationResult("telegram", str(result["message_id"]), rendered.text)

    def edit(self, publication_id: str, rendered: RenderedPost) -> PublicationResult:
        self._post(
            "editMessageText",
            {
                "chat_id": self.channel_id,
                "message_id": int(publication_id),
                "text": rendered.text,
                "parse_mode": "HTML",
            },
        )
        return PublicationResult("telegram", publication_id, rendered.text)

    def delete(self, publication_id: str) -> None:
        self._post("deleteMessage", {"chat_id": self.channel_id, "message_id": int(publication_id)})
