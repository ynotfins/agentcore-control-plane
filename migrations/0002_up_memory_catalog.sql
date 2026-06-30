-- 0002_up_memory_catalog.sql
-- AgentCore Unified Memory Catalog migration 0002 (UP) -- the discovery spine.
-- Design authority: database-plan.md sec 6.3. Additive only. Target DB: agent_core @ 127.0.0.1:55432.
-- Requires: extension `vector` (pgvector 0.8.2), pgcrypto. Depends on 0001 (memory_source_systems) and existing projects table.
-- Postgres stores pointers/summaries/provenance only -- never raw SwarmVault pages, Obsidian bodies, or full SwarmRecall content.

CREATE TABLE IF NOT EXISTS memory_catalog (
    id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id       uuid        REFERENCES projects(id) ON DELETE SET NULL,  -- nullable for global/cross-project facts
    source_system    text        NOT NULL REFERENCES memory_source_systems(slug),
    source_uri       text        NOT NULL,  -- exact path / memory-id / URL / tool ref in the backend
    external_id      text,                  -- backend-native ID (e.g. SwarmRecall memory UUID)
    memory_type      text        NOT NULL,  -- fact|decision|source|context_pack|transcript|run|incident|doc|handoff|skill
    title            text        NOT NULL,
    summary          text,                  -- short distillation; Postgres does NOT store raw content
    tags             text[]      NOT NULL DEFAULT '{}',
    privacy_zone     text        NOT NULL DEFAULT 'project-private',  -- public|project-private|operator-only
    confidence       numeric(4,3) NOT NULL DEFAULT 0.8
                                    CHECK (confidence BETWEEN 0 AND 1),
    content_hash     text,                  -- SHA-256 of source content when available
    embedding        vector(1536),          -- pgvector embedding of summary
    embedding_provider text,               -- openai_text_embedding_3_small | local_hash_v1
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now(),
    last_verified_at timestamptz,

    CONSTRAINT ck_mc_privacy_zone
        CHECK (privacy_zone IN ('public', 'project-private', 'operator-only')),
    CONSTRAINT ck_mc_memory_type
        CHECK (memory_type IN (
            'fact', 'decision', 'source', 'context_pack',
            'transcript', 'run', 'incident', 'doc', 'handoff', 'skill'
        )),
    CONSTRAINT uq_mc_source
        UNIQUE (source_system, source_uri)
);

CREATE INDEX IF NOT EXISTS idx_mc_project_id    ON memory_catalog (project_id);
CREATE INDEX IF NOT EXISTS idx_mc_source_system ON memory_catalog (source_system);
CREATE INDEX IF NOT EXISTS idx_mc_memory_type   ON memory_catalog (memory_type);
CREATE INDEX IF NOT EXISTS idx_mc_privacy_zone  ON memory_catalog (privacy_zone);
CREATE INDEX IF NOT EXISTS idx_mc_created_at    ON memory_catalog (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mc_embedding     ON memory_catalog
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
