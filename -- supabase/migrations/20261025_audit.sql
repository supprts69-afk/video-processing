-- supabase/migrations/20261025_audit.sql

CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL, -- 'job', 'task', 'worker'
    entity_id UUID NOT NULL,
    event_type TEXT NOT NULL, -- 'created', 'leased', 'failed', 'completed'
    worker_id UUID REFERENCES workers(id),
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for efficient querying by job or task
CREATE INDEX idx_audit_entity ON audit_events(entity_id, entity_type);
