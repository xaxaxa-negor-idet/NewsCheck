CREATE TABLE channels (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    url TEXT,
    category TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    poll_interval INTEGER NOT NULL DEFAULT 300,
    last_success_poll_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    source_message_id TEXT NOT NULL,
    original_text TEXT,
    media TEXT,
    source_url TEXT,
    published_at TEXT,
    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'NEW',
    availability TEXT NOT NULL DEFAULT 'AVAILABLE',
    edited_at TEXT,
    UNIQUE(channel_id, source_message_id)
);

CREATE INDEX idx_messages_status ON messages(processing_status);
CREATE INDEX idx_messages_channel_status ON messages(channel_id, processing_status);

CREATE TABLE message_versions (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id),
    text TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_message_versions_message ON message_versions(message_id);

CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id),
    file_path TEXT,
    file_hash TEXT,
    mime TEXT,
    size INTEGER,
    position INTEGER,
    downloaded INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_media_message ON media(message_id);

CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT,
    location TEXT,
    event_date TEXT,
    event_type TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
    current_status TEXT,
    recheck_count INTEGER NOT NULL DEFAULT 0,
    next_recheck_at TEXT,
    max_rechecks INTEGER NOT NULL DEFAULT 4,
    lifecycle TEXT NOT NULL DEFAULT 'ACTIVE',
    manual_override INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_events_lifecycle_recheck ON events(lifecycle, next_recheck_at);

CREATE TABLE event_messages (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id),
    message_id INTEGER NOT NULL REFERENCES messages(id),
    relation_confidence REAL,
    relation_type TEXT NOT NULL DEFAULT 'AUTO_MERGE',
    decided_by TEXT NOT NULL DEFAULT 'system',
    UNIQUE(event_id, message_id)
);

CREATE TABLE claims (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id),
    message_id INTEGER NOT NULL REFERENCES messages(id),
    claim_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'NOT_CHECKED',
    is_key INTEGER NOT NULL DEFAULT 0,
    manual_override INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_claims_event ON claims(event_id);

CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    canonical_url TEXT NOT NULL,
    url TEXT,
    title TEXT,
    source_name TEXT,
    source_type TEXT,
    domain TEXT,
    published_at TEXT,
    retrieved_at TEXT,
    content TEXT,
    is_primary_hint INTEGER
);
CREATE INDEX idx_sources_canonical ON sources(canonical_url);

CREATE TABLE claim_sources (
    id INTEGER PRIMARY KEY,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    source_id INTEGER NOT NULL REFERENCES sources(id),
    relation TEXT NOT NULL,
    evidence TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(claim_id, source_id, relation)
);

CREATE TABLE verifications (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id),
    started_at TEXT,
    finished_at TEXT,
    status TEXT,
    reason TEXT,
    model_name TEXT,
    model_version TEXT,
    prompt_version TEXT,
    queries_used INTEGER,
    provider_errors TEXT
);

CREATE TABLE verification_history (
    id INTEGER PRIMARY KEY,
    verification_id INTEGER REFERENCES verifications(id),
    event_id INTEGER NOT NULL REFERENCES events(id),
    old_status TEXT,
    new_status TEXT,
    reason TEXT,
    mode TEXT NOT NULL DEFAULT 'AUTO',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE published_messages (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id),
    destination TEXT NOT NULL DEFAULT 'telegram',
    telegram_message_id TEXT,
    published_at TEXT,
    current_version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'PUBLISHED'
);

CREATE TABLE publication_history (
    id INTEGER PRIMARY KEY,
    published_message_id INTEGER NOT NULL REFERENCES published_messages(id),
    version INTEGER NOT NULL,
    text TEXT NOT NULL,
    status TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_decisions (
    id INTEGER PRIMARY KEY,
    event_id INTEGER REFERENCES events(id),
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL,
    payload TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    priority INTEGER NOT NULL DEFAULT 5,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    finished_at TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    next_retry_at TEXT
);
CREATE INDEX idx_tasks_status_priority_retry ON tasks(status, priority, next_retry_at);

CREATE TABLE source_dedup (
    url_hash TEXT PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id)
);

CREATE TABLE llm_calls (
    id INTEGER PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id),
    step TEXT,
    model_name TEXT,
    model_version TEXT,
    prompt_version TEXT,
    request_summary TEXT,
    ok INTEGER,
    error TEXT,
    tokens INTEGER,
    duration_ms INTEGER
);

CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    version REAL NOT NULL DEFAULT 1.0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE search_quota (
    id INTEGER PRIMARY KEY,
    provider TEXT NOT NULL,
    day TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    UNIQUE(provider, day)
);
