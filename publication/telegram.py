# -*- coding: utf-8 -*-
"""Telegram Bot API destination with multipart media upload, retry and link-format caption."""
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
    MAX_RETRIES = 3

    def __init__(self, bot_token: str, channel_id: str, timeout: int = 90):
        if not bot_token:
            raise ValueError("bot token is required")
        if not channel_id:
            raise ValueError("channel id is required")
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.timeout = timeout
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = requests.Session()

    def _post(self, method: str, payload: dict) -> dict:
        response = self.session.post(f"{self.base_url}/{method}", json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")
        return data["result"]

    def _post_multipart(self, method: str, data: dict, files: dict) -> dict | None:
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.post(
                    f"{self.base_url}/{method}",
                    data=data,
                    files=files,
                    timeout=self.timeout,
                )
                result = response.json()
                if result.get("ok"):
                    return result
            except Exception:
                pass
            time.sleep(2 * (attempt + 1))
        return None

    def _fetch_media(self, url: str) -> bytes | None:
        for attempt in range(2):
            try:
                r = self.session.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 NewsCheck/1.0"})
                if r.status_code == 200 and len(r.content) > 1000:
                    return r.content
            except Exception:
                pass
            time.sleep(2)
        return None

    def publish(self, rendered: RenderedPost) -> PublicationResult:
        media_url = getattr(rendered, "media_url", None)
        caption = rendered.text[:1024]

        if media_url:
            media_bytes = self._fetch_media(media_url)
            if media_bytes:
                kind = getattr(rendered, "media_kind", "photo")
                if kind == "video":
                    method, field = "sendVideo", "video"
                    fname, mime = "video.mp4", "video/mp4"
                else:
                    method, field = "sendPhoto", "photo"
                    fname, mime = "photo.jpg", "image/jpeg"
                result = self._post_multipart(
                    method,
                    {"chat_id": self.channel_id, "caption": caption, "parse_mode": "HTML"},
                    {field: (fname, media_bytes, mime)},
                )
                if result:
                    return PublicationResult("telegram", str(result["result"]["message_id"]), rendered.text)

        result = self._post(
            "sendMessage",
            {"chat_id": self.channel_id, "text": rendered.text, "parse_mode": "HTML"},
        )
        return PublicationResult("telegram", str(result["message_id"]), rendered.text)

    def edit(self, publication_id: str, rendered: RenderedPost) -> PublicationResult:
        self._post(
            "editMessageText",
            {"chat_id": self.channel_id, "message_id": int(publication_id), "text": rendered.text, "parse_mode": "HTML"},
        )
        return PublicationResult("telegram", publication_id, rendered.text)

    def delete(self, publication_id: str) -> None:
        self._post("deleteMessage", {"chat_id": self.channel_id, "message_id": int(publication_id)})
