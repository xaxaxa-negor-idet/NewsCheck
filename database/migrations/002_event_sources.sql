-- 002: event sources link table
CREATE TABLE IF NOT EXISTS event_sources (
    event_id INTEGER NOT NULL REFERENCES events(id),
    source_id INTEGER NOT NULL REFERENCES sources(id),
    UNIQUE(event_id, source_id)
);
CREATE INDEX IF NOT EXISTS idx_event_sources_event ON event_sources(event_id);
