from pathlib import Path
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.migrate import apply_migrations
from search.sources import SourceRecord, classify_independence, domain_of, save_source


def test_domain_extraction():
    assert domain_of("https://Example.com/News?utm_source=x") == "example.com"


def test_independence_rules():
    sources = [
        SourceRecord(1, "agency.com", datetime(2026, 10, 1, tzinfo=timezone.utc), None, True),
        SourceRecord(2, "news.com", datetime(2026, 10, 1, 1, tzinfo=timezone.utc), 1, False),
        SourceRecord(3, "independent.com", datetime(2026, 10, 1, 2, tzinfo=timezone.utc), None, False),
    ]
    result = classify_independence(sources)
    assert result == {1: True, 2: False, 3: True}


def test_save_source_dedup(tmp_path):
    db = str(tmp_path / "sources.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    url = "https://example.com/news?utm_source=x"

    first = save_source(conn, url, "Title", "Content", None)
    second = save_source(conn, "https://example.com/news", "Title", "Content", None)
    count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    conn.close()

    assert first == second and count == 1
