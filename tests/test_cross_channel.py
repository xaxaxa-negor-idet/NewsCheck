from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3

from database.migrate import apply_migrations
from matching.cross_channel import _extract_keywords, _similarity, find_cross_channel_matches


def prepare_db(tmp_path):
    db = str(tmp_path / "cross.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO channels (name, username) VALUES ('First', 'first')")
    conn.execute("INSERT INTO channels (name, username) VALUES ('Second', 'second')")
    conn.execute("INSERT INTO messages (channel_id, source_message_id, original_text, content_hash, source_url) VALUES (1, '1', 'Moskva happened DTP na Sadovom koltce s tremya mashinami', 'h1', 'https://t.me/first/1')")
    conn.execute("INSERT INTO messages (channel_id, source_message_id, original_text, content_hash, source_url, processing_status) VALUES (2, '2', 'Na Sadovom koltce v Moskve DTP: stolknulis tri avtomobilya', 'h2', 'https://t.me/second/2', 'PROCESSED')")
    conn.execute("INSERT INTO messages (channel_id, source_message_id, original_text, content_hash, source_url) VALUES (2, '3', 'Sovsem drugaya novost pro ekonomiku', 'h3', 'https://t.me/second/3')")
    conn.commit()
    conn.close()
    return db


def test_finds_cross_channel_match(tmp_path):
    db = prepare_db(tmp_path)
    matches = find_cross_channel_matches(1, 1, "DTP na Sadovom koltce v Moskve", ["Moskva", "Sadovom", "DTP"], db)
    assert len(matches) == 1
    assert matches[0].channel_username == "second"
    assert matches[0].similarity > 0.5


def test_no_self_match(tmp_path):
    db = prepare_db(tmp_path)
    matches = find_cross_channel_matches(1, 1, "DTP", ["DTP"], db)
    assert all(m.channel_id != 1 for m in matches)


def test_similarity():
    kws = ["moskve", "dtp", "sadovom"]
    assert _similarity(kws, "V Moskve DTP na Sadovom koltce") >= 0.6
    assert _similarity(kws, "DTP v Kazani") < 1.0
    assert _similarity(kws, "Sovsem drugoe") == 0.0


def test_extract_keywords():
    kws = _extract_keywords("V Moskve proizoshlo krupnoe DTP na Sadovom koltce")
    assert "moskve" in kws
    assert "dtp" in kws
    assert "v" not in kws
