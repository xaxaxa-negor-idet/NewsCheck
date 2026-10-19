"""Telegram Bot API destination: SPEC 11.4."""
from __future__ import annotations

from dataclasses import dataclass

import requests

from publication.console import PublicationResult, RenderedPost


class TelegramChannelDestination:
    name = "telegram"

    def __init__(self, bot_token: str, channel_id: str, timeout: int = 30):
        if not bot_token:
            raise ValueError("bot token is required")
        if not channel_id:
            raise ValueError("channel id is required")
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.timeout = timeout
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def _post(self, method: str, payload: dict) -> dict:
        response = requests.post(f"{self.base_url}/{method}", json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")
        return data["result"]

    def publish(self, rendered: RenderedPost) -> PublicationResult:
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
