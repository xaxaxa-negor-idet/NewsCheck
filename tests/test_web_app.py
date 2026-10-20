"""Web panel tests: auth, dashboard, messages, events."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3

from database.migrate import apply_migrations
from web.app import app


def make_client_with_data(tmp_path):
    db = str(tmp_path / "web.db")
    apply_migrations(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO channels (name, username) VALUES ('Тест', 'test')")
    conn.execute("INSERT INTO messages (channel_id, source_message_id, original_text, content_hash, processing_status) VALUES (1, '1', 'новость', 'h1', 'NEW')")
    conn.execute("INSERT INTO messages (channel_id, source_message_id, original_text, content_hash, processing_status) VALUES (1, '2', 'готовая', 'h2', 'PROCESSED')")
    conn.execute("INSERT INTO events (title, current_status, lifecycle) VALUES ('Событие', 'ТРЕБУЕТ ДОПОЛНИТЕЛЬНОЙ ПРОВЕРКИ', 'ACTIVE')")
    conn.commit()
    conn.close()
    return db


def test_login_required():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 302


def test_login_flow(tmp_path):
    client = app.test_client()
    response = client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200
    response = client.get('/')
    assert response.status_code == 200
    response = client.get('/messages')
    assert response.status_code == 200


def test_wrong_login():
    client = app.test_client()
    response = client.post('/login', data={'username': 'bad', 'password': 'bad'})
    assert response.status_code == 200


def test_health():
    client = app.test_client()
    response = client.get('/health')
    assert response.get_json() == {'status': 'ok'}
