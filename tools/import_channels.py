from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sources.collector import ensure_channel, ingest_poll_result
from sources.telegram_web import list_messages

CHANNELS = [
    ("topor", "ТОПОР - Горячие новости", "right"),
    ("zhestvideo18", "Жесть видео 18+", "incident"),
    ("readovka", "Важное в Смоленске", "right"),
    ("nexta_live", "NEXTA Live", "left"),
    ("rybar", "Рыбарь", "right"),
    ("breakingmash", "Mash", "incident"),
    ("shot_shot", "SHOT", "incident"),
]

for username, name, category in CHANNELS:
    channel_id = ensure_channel(username, name, category)
    result = list_messages(username)
    if result.kind == "UNAVAILABLE":
        print(username, "UNAVAILABLE", result.reason)
        continue
    outcome = ingest_poll_result(result, channel_id)
    print(username, result.kind, f"new={outcome.inserted} dup={outcome.duplicates} edited={outcome.updated}")
