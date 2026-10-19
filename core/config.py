"""Config contract: SPEC 2.2.4 — single access point for table config and .env."""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "dry_run": "true",
    "destination": "console",
    "poll_interval_seconds": "300",
    "poll_overlap_minutes": "10",
    "retry_delays_minutes": "1,5,30",
    "max_task_attempts": "3",
    "llm_endpoint": "",
    "telegram_bot_token": "",
}


@dataclass(frozen=True)
class Settings:
    dry_run: bool
    destination: str
    poll_interval_seconds: int
    poll_overlap_minutes: int
    retry_delays_minutes: tuple[int, ...]
    max_task_attempts: int
    llm_endpoint: str
    telegram_bot_token: str


def load_settings(db_path: str | None = None) -> Settings:
    path = Path(db_path) if db_path else ROOT / "newscheck.db"
    values = dict(DEFAULTS)

    if path.exists():
        conn = sqlite3.connect(path)
        try:
            rows = conn.execute("SELECT key, value FROM config").fetchall()
        finally:
            conn.close()
        values.update({key: value for key, value in rows})

    env = {
        "llm_endpoint": os.getenv("LLM_ENDPOINT"),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
    }
    values.update({key: value for key, value in env.items() if value})

    return Settings(
        dry_run=str(values["dry_run"]).lower() == "true",
        destination=values["destination"],
        poll_interval_seconds=int(values["poll_interval_seconds"]),
        poll_overlap_minutes=int(values["poll_overlap_minutes"]),
        retry_delays_minutes=tuple(int(item) for item in str(values["retry_delays_minutes"]).split(",")),
        max_task_attempts=int(values["max_task_attempts"]),
        llm_endpoint=values["llm_endpoint"],
        telegram_bot_token=values["telegram_bot_token"],
    )
