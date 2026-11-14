CREATE SCHEMA IF NOT EXISTS tracepath;
CREATE TABLE IF NOT EXISTS tracepath.sessions (
    session_scope text PRIMARY KEY CHECK (length(session_scope)=64),
    expires_at timestamptz NOT NULL,
    remaining integer NOT NULL CHECK (remaining >= 0)
);
CREATE TABLE IF NOT EXISTS tracepath.receipts (
    request_id uuid PRIMARY KEY,
    session_scope text NOT NULL REFERENCES tracepath.sessions(session_scope),
    operation_key text NOT NULL,
    payload_digest text NOT NULL,
    receipt jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL DEFAULT now() + interval '1 day',
    UNIQUE(session_scope, operation_key)
);
CREATE TABLE IF NOT EXISTS tracepath.attempts (
    attempt_id uuid PRIMARY KEY,
    request_id uuid NOT NULL,
    run_id text NOT NULL,
    attempt integer NOT NULL,
    observation jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS receipt_expiry ON tracepath.receipts(expires_at);
CREATE INDEX IF NOT EXISTS attempt_run ON tracepath.attempts(run_id);
