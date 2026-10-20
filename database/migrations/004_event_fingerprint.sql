ALTER TABLE events ADD COLUMN fingerprint TEXT;
CREATE INDEX IF NOT EXISTS idx_events_fingerprint ON events(fingerprint);
