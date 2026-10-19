"""Console destination: SPEC 11.4, 11.5 — dry-run publication target."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderedPost:
    event_id: int
    text: str


@dataclass(frozen=True)
class PublicationResult:
    destination: str
    external_id: str
    text: str


class ConsoleDestination:
    name = "console"

    def publish(self, rendered: RenderedPost) -> PublicationResult:
        print(rendered.text)
        return PublicationResult("console", f"event-{rendered.event_id}", rendered.text)

    def edit(self, publication_id: str, rendered: RenderedPost) -> PublicationResult:
        print(rendered.text)
        return PublicationResult("console", publication_id, rendered.text)

    def delete(self, publication_id: str) -> None:
        print(f"deleted publication {publication_id}")
