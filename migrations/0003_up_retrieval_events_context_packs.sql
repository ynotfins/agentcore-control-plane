-- 0003_up_retrieval_events_context_packs.sql
-- AgentCore Unified Memory Catalog migration 0003 (UP): context packs + retrieval events.
-- Design authority: database-plan.md sec 6.3. Additive only. Target DB: agent_core @ 127.0.0.1:55432.
-- Depends on 0002 (memory_catalog) and existing projects table.
-- Order matters: context_packs before memory_retrieval_events (FK) before context_pack_items (FK).

CREATE TABLE IF NOT EXISTS context_packs (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      uuid        REFERENCES projects(id) ON DELETE SET NULL,
    name            text,                   -- optional human label, e.g. 'handoff-20260630'
    task_type       text,
    privacy_zone    text        NOT NULL DEFAULT 'project-private',
    token_count     int,
    build_latency_ms int,
    sources_used    text[]      NOT NULL DEFAULT '{}',
    quality_score   numeric(4,3),
    created_by      text,                   -- gateway | projector | operator
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cp_project_id ON context_packs (project_id);
CREATE INDEX IF NOT EXISTS idx_cp_created_at ON context_packs (created_at DESC);

CREATE TABLE IF NOT EXISTS memory_retrieval_events (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid        REFERENCES projects(id) ON DELETE SET NULL,
    agent_id            text,
    run_id              text,
    query_text          text,
    task_type           text,       -- general|architecture|debug|cross_project_research
    privacy_zone        text        NOT NULL DEFAULT 'project-private',
    token_budget        int,
    sources_searched    text[]      NOT NULL DEFAULT '{}',
    sources_used        text[]      NOT NULL DEFAULT '{}',
    items_returned      int         NOT NULL DEFAULT 0,
    token_count_used    int,
    retrieval_latency_ms int,
    context_pack_id     uuid        REFERENCES context_packs(id) ON DELETE SET NULL,
    embedding_provider  text,
    embedding_fallback  boolean     NOT NULL DEFAULT false,
    missing_info_flags  text[],
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mre_project_id ON memory_retrieval_events (project_id);
CREATE INDEX IF NOT EXISTS idx_mre_agent_id   ON memory_retrieval_events (agent_id);
CREATE INDEX IF NOT EXISTS idx_mre_run_id     ON memory_retrieval_events (run_id);
CREATE INDEX IF NOT EXISTS idx_mre_created_at ON memory_retrieval_events (created_at DESC);

CREATE TABLE IF NOT EXISTS context_pack_items (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    context_pack_id uuid        NOT NULL REFERENCES context_packs(id) ON DELETE CASCADE,
    catalog_id      uuid        REFERENCES memory_catalog(id) ON DELETE SET NULL,
    source_system   text        NOT NULL,
    source_uri      text        NOT NULL,
    memory_type     text,
    title           text,
    excerpt         text,           -- brief excerpt injected into context; not full content
    relevance_score numeric(5,4),
    rank_position   int,
    token_count     int,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cpi_pack_id    ON context_pack_items (context_pack_id);
CREATE INDEX IF NOT EXISTS idx_cpi_catalog_id ON context_pack_items (catalog_id);
