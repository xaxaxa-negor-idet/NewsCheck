from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = ROOT / "database" / "migrations"

def apply_migrations(db_path: str | None = None) -> list[str]:
    target = Path(db_path) if db_path else ROOT / "newscheck.db"
    conn = sqlite3.connect(target)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(id INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        applied = {row[0] for row in conn.execute("SELECT id FROM schema_migrations")}
        results = []
        for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            migration_id = int(file.stem.split("_", 1)[0])
            if migration_id in applied:
                continue
            conn.executescript(file.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (name) VALUES (?)", (file.name,))
            conn.commit()
            results.append(file.name)
        return results
    finally:
        conn.close()

if __name__ == "__main__":
    print(apply_migrations())
