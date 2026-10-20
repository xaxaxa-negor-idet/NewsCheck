from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
from database.migrate import apply_migrations
from matching.event_dedup import compute_fingerprint, find_existing_event, normalize_text


def prepare(tmp_path):
    db = str(tmp_path / "dedup.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO events (title, summary, fingerprint) VALUES ('Тату-мастер пропал в Азии', 's', ?)", (compute_fingerprint('Тату-мастер пропал в Азии'),))
    conn.commit()
    conn.close()
    return db


def test_same_fingerprint(tmp_path):
    db = prepare(tmp_path)
    eid = find_existing_event('Тату-мастер пропал в Азии', 'text', db)
    assert eid == 1


def test_title_similarity(tmp_path):
    db = str(tmp_path / "sim.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO events (title, summary, created_at) VALUES ('Российский тату-мастер пропал во время велопутешествия', 's', datetime('now'))")
    conn.commit()
    conn.close()
    eid = find_existing_event('Российский тату-мастер пропал во время поездки', 'other text', db)
    assert eid == 1


def test_different_news(tmp_path):
    db = prepare(tmp_path)
    eid = find_existing_event('Совсем другая новость про экономику', 'text', db)
    assert eid is None


def test_normalize():
    assert normalize_text('В Москве, произошло ДТП!') == normalize_text('в москве произошло дтп')
