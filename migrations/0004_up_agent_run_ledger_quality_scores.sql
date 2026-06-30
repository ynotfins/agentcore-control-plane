-- 0004_up_agent_run_ledger_quality_scores.sql
-- AgentCore Unified Memory Catalog migration 0004 (UP): agent run ledger + quality scores.
-- Design authority: database-plan.md sec 6.3. Additive only. Target DB: agent_core @ 127.0.0.1:55432.
-- Depends on 0003 (context_packs, memory_retrieval_events) and existing projects table.

CREATE TABLE IF NOT EXISTS agent_run_ledger (
    id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id           text        NOT NULL UNIQUE,
    project_id       uuid        REFERENCES projects(id) ON DELETE SET NULL,
    agent_id         text,
    ide_platform     text,           -- cursor|codex|openclaw|minimax|claude|antigravity|open-interpreter
    task_summary     text,
    tools_used       text[]      NOT NULL DEFAULT '{}',
    files_changed    text[]      NOT NULL DEFAULT '{}',
    tests_run        text[]      NOT NULL DEFAULT '{}',
    errors           text[],
    result           text,           -- completed|partial|failed|blocked
    pr_url           text,
    follow_up_needed boolean     NOT NULL DEFAULT false,
    durable_lessons  text[],
    source_evidence  text[],         -- paths to evidence files in D:\AgentSwarm\runs\<run_id>\
    created_at       timestamptz NOT NULL DEFAULT now(),
    completed_at     timestamptz
);

CREATE INDEX IF NOT EXISTS idx_arl_project_id ON agent_run_ledger (project_id);
CREATE INDEX IF NOT EXISTS idx_arl_agent_id   ON agent_run_ledger (agent_id);
CREATE INDEX IF NOT EXISTS idx_arl_created_at ON agent_run_ledger (created_at DESC);

CREATE TABLE IF NOT EXISTS agent_quality_scores (
    id                   uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    context_pack_id      uuid        REFERENCES context_packs(id) ON DELETE CASCADE,
    retrieval_event_id   uuid        REFERENCES memory_retrieval_events(id) ON DELETE CASCADE,
    run_id               text        REFERENCES agent_run_ledger(run_id) ON DELETE SET NULL,
    answer_usefulness    numeric(4,3),   -- 0.0-1.0 if available; null if not assessed
    hallucination_flag   boolean     NOT NULL DEFAULT false,
    drift_flag           boolean     NOT NULL DEFAULT false,
    missing_info_flag    boolean     NOT NULL DEFAULT false,
    notes                text,
    scored_by            text,           -- agent_self|validator|operator
    created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aqs_pack_id         ON agent_quality_scores (context_pack_id);
CREATE INDEX IF NOT EXISTS idx_aqs_retrieval_event ON agent_quality_scores (retrieval_event_id);
