-- Append-heavy write lab: heap + B-tree secondary index (see README).
CREATE TABLE IF NOT EXISTS events (
    id uuid PRIMARY KEY,
    bucket text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_bucket ON events (bucket);
