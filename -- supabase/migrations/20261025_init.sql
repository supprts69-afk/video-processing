-- supabase/migrations/20261025_init.sql

CREATE TYPE worker_status AS ENUM ('offline', 'idle', 'busy', 'draining', 'error');
CREATE TYPE job_status AS ENUM ('queued', 'preparing', 'processing', 'finalizing', 'completed', 'failed', 'cancelled');
CREATE TYPE task_status AS ENUM ('queued', 'leased', 'completed', 'failed', 'cancelled');

CREATE TABLE workers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    status worker_status DEFAULT 'offline',
    capabilities JSONB DEFAULT '{}'::jsonb,
    last_heartbeat_at TIMESTAMPTZ DEFAULT now(),
    registered_at TIMESTAMPTZ DEFAULT now(),
    software_version TEXT,
    api_token_hash TEXT NOT NULL
);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status job_status DEFAULT 'queued',
    source_url TEXT NOT NULL,
    processing_profile JSONB NOT NULL,
    expected_task_count INT DEFAULT 0,
    completed_task_count INT DEFAULT 0,
    final_video_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    task_index INT NOT NULL,
    status task_status DEFAULT 'queued',
    worker_id UUID REFERENCES workers(id),
    lease_expires_at TIMESTAMPTZ,
    attempt_count INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    processing_params JSONB NOT NULL,
    output_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for efficient queue polling
CREATE INDEX idx_tasks_queue ON tasks(status) WHERE status = 'queued';
CREATE INDEX idx_workers_heartbeat ON workers(last_heartbeat_at);
