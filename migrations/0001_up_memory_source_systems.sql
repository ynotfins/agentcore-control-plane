-- 0001_up_memory_source_systems.sql
-- AgentCore Unified Memory Catalog migration 0001 (UP)
-- Design authority: database-plan.md sec 6.3. Additive only. Target DB: agent_core @ 127.0.0.1:55432.
-- PRE-MIGRATION: dry-run (BEGIN ... ROLLBACK) first; live apply requires operator sign-off (database-plan.md sec 13).
-- Requires pgcrypto (gen_random_uuid). pgcrypto is a declared required extension in the global memory database contract.

CREATE TABLE IF NOT EXISTS memory_source_systems (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            text        NOT NULL UNIQUE,   -- 'postgres','swarmrecall','swarmvault','obsidian','context-fabric','git','manual','lcm'
    display_name    text        NOT NULL,
    endpoint_uri    text,                          -- base URL or path; no credentials
    adapter_notes   text,                          -- implementation notes for the gateway adapter
    is_active       boolean     NOT NULL DEFAULT true,
    is_deferred     boolean     NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mss_slug ON memory_source_systems (slug);
