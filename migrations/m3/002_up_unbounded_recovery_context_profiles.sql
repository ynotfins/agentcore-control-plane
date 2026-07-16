-- M3 002 UP — Effectively-Unbounded Recovery and Model-Aware Active Context
--
-- Authority: BLUEPRINT.md §§5-6, M3 and the operator clarification dated 2026-07-16.
-- This is additive within the locked architecture. Durable evidence remains immutable;
-- model limits bound only one active packet or retrieval page.

BEGIN;

CREATE TABLE IF NOT EXISTS agentcore.model_context_profiles (
    profile_name                         text PRIMARY KEY,
    provider                             text NOT NULL,
    model_id                             text NOT NULL,
    client_ids                           text[] NOT NULL DEFAULT '{}'::text[],
    hard_context_limit                   bigint NOT NULL CHECK (hard_context_limit > 0),
    safe_active_context_ceiling          bigint NOT NULL CHECK (safe_active_context_ceiling > 0),
    reserved_output_tokens               bigint NOT NULL CHECK (reserved_output_tokens >= 0),
    reserved_tool_schema_tokens          bigint NOT NULL CHECK (reserved_tool_schema_tokens >= 0),
    reserved_tool_result_tokens          bigint NOT NULL CHECK (reserved_tool_result_tokens >= 0),
    safety_reserve_tokens                bigint NOT NULL CHECK (safety_reserve_tokens >= 0),
    soft_compaction_threshold_tokens     bigint NOT NULL CHECK (soft_compaction_threshold_tokens > 0),
    hard_compaction_threshold_tokens     bigint NOT NULL CHECK (hard_compaction_threshold_tokens > 0),
    retrieval_page_size                  integer NOT NULL CHECK (retrieval_page_size > 0),
    tokenizer                            text NOT NULL,
    last_validated_date                  date NOT NULL,
    validation_source                    text NOT NULL,
    production_profile                   boolean NOT NULL DEFAULT true,
    created_at                           timestamptz NOT NULL DEFAULT now(),
    updated_at                           timestamptz NOT NULL DEFAULT now(),
    CHECK (
        safe_active_context_ceiling <= hard_context_limit
          - reserved_output_tokens
          - reserved_tool_schema_tokens
          - reserved_tool_result_tokens
          - safety_reserve_tokens
    ),
    CHECK (
        soft_compaction_threshold_tokens < hard_compaction_threshold_tokens
        AND hard_compaction_threshold_tokens <= safe_active_context_ceiling
    )
);

CREATE TABLE IF NOT EXISTS agentcore.model_context_profile_aliases (
    alias_name       text PRIMARY KEY,
    profile_name     text NOT NULL REFERENCES agentcore.model_context_profiles(profile_name) ON DELETE RESTRICT,
    legacy_only      boolean NOT NULL DEFAULT false,
    notes            text
);

ALTER TABLE agentcore.sessions
    ADD COLUMN IF NOT EXISTS context_profile_name text
        REFERENCES agentcore.model_context_profiles(profile_name) ON DELETE RESTRICT;

INSERT INTO agentcore.model_context_profiles (
    profile_name, provider, model_id, client_ids, hard_context_limit,
    safe_active_context_ceiling, reserved_output_tokens, reserved_tool_schema_tokens,
    reserved_tool_result_tokens, safety_reserve_tokens,
    soft_compaction_threshold_tokens, hard_compaction_threshold_tokens,
    retrieval_page_size, tokenizer, last_validated_date, validation_source,
    production_profile
)
VALUES
  ('acceptance-small', 'agentcore', 'acceptance/small-context', ARRAY['test'], 4096, 3072, 512, 128, 256, 128, 2304, 2880, 50, 'cl100k_base-estimate', DATE '2026-07-16', 'AgentCore bounded acceptance profile; never a production default', false),
  ('legacy-4096', 'agentcore', 'legacy/4096-alias', ARRAY[]::text[], 6144, 4096, 1024, 256, 512, 256, 3072, 3840, 50, 'cl100k_base-estimate', DATE '2026-07-16', 'Backward-compatible M3 budget alias; not a production ceiling', false),
  ('standard-context', 'generic', 'capability/standard-128k', ARRAY['cursor','codex','claude-code','claude-desktop','minimax','mavis','antigravity','open-interpreter'], 131072, 98304, 8192, 4096, 8192, 4096, 73728, 92160, 200, 'provider-reported-or-cl100k-estimate', DATE '2026-07-16', 'Capability-class fallback; selected provider/model profile overrides it', true),
  ('large-context', 'generic', 'capability/large-256k', ARRAY[]::text[], 262144, 196608, 16384, 8192, 16384, 8192, 147456, 184320, 500, 'provider-reported-or-o200k-estimate', DATE '2026-07-16', 'Extensible large-context capability profile', true),
  ('one-million-context', 'generic', 'capability/one-million', ARRAY[]::text[], 1000000, 880000, 32768, 16384, 32768, 32768, 660000, 825000, 1000, 'provider-reported-model-tokenizer', DATE '2026-07-16', 'One-million-token active-context capability profile; not a durable-memory cap', true),
  ('future-above-million', 'generic', 'capability/future-above-million', ARRAY[]::text[], 2000000, 1750000, 65536, 32768, 65536, 65536, 1312500, 1640625, 2000, 'provider-reported-model-tokenizer', DATE '2026-07-16', 'Forward-compatibility proof above one million', false)
ON CONFLICT (profile_name) DO UPDATE
SET provider = EXCLUDED.provider,
    model_id = EXCLUDED.model_id,
    client_ids = EXCLUDED.client_ids,
    hard_context_limit = EXCLUDED.hard_context_limit,
    safe_active_context_ceiling = EXCLUDED.safe_active_context_ceiling,
    reserved_output_tokens = EXCLUDED.reserved_output_tokens,
    reserved_tool_schema_tokens = EXCLUDED.reserved_tool_schema_tokens,
    reserved_tool_result_tokens = EXCLUDED.reserved_tool_result_tokens,
    safety_reserve_tokens = EXCLUDED.safety_reserve_tokens,
    soft_compaction_threshold_tokens = EXCLUDED.soft_compaction_threshold_tokens,
    hard_compaction_threshold_tokens = EXCLUDED.hard_compaction_threshold_tokens,
    retrieval_page_size = EXCLUDED.retrieval_page_size,
    tokenizer = EXCLUDED.tokenizer,
    last_validated_date = EXCLUDED.last_validated_date,
    validation_source = EXCLUDED.validation_source,
    production_profile = EXCLUDED.production_profile,
    updated_at = now();

INSERT INTO agentcore.model_context_profile_aliases (alias_name, profile_name, legacy_only, notes)
VALUES
  ('small', 'acceptance-small', true, 'M3 acceptance alias'),
  ('default', 'standard-context', true, 'Former 4096 default now resolves to model-aware standard context'),
  ('large', 'large-context', true, 'Former 16000 alias'),
  ('4096', 'legacy-4096', true, 'Explicit compatibility profile only')
ON CONFLICT (alias_name) DO UPDATE
SET profile_name = EXCLUDED.profile_name,
    legacy_only = EXCLUDED.legacy_only,
    notes = EXCLUDED.notes;

-- Keep the M3 assembler backward-compatible. These rows are active-packet ceilings,
-- never durable-retention limits.
INSERT INTO agentcore.model_context_budgets (budget_name, max_tokens, preserve_recent, notes)
SELECT profile_name, safe_active_context_ceiling::integer, 20,
       'Compatibility row for model_context_profiles; active packet only'
FROM agentcore.model_context_profiles
WHERE safe_active_context_ceiling <= 2147483647
ON CONFLICT (budget_name) DO UPDATE
SET max_tokens = EXCLUDED.max_tokens,
    preserve_recent = EXCLUDED.preserve_recent,
    notes = EXCLUDED.notes;

CREATE TABLE IF NOT EXISTS agentcore.recovery_operations (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id              uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    session_id              uuid REFERENCES agentcore.sessions(id) ON DELETE RESTRICT,
    recovery_mode           text NOT NULL,
    context_profile_name    text REFERENCES agentcore.model_context_profiles(profile_name) ON DELETE RESTRICT,
    request_scope           jsonb NOT NULL DEFAULT '{}'::jsonb,
    chronological_start     timestamptz,
    chronological_end       timestamptz,
    continuation_digest     text,
    source_event_ids        uuid[] NOT NULL DEFAULT '{}'::uuid[],
    omitted_item_count      bigint NOT NULL DEFAULT 0 CHECK (omitted_item_count >= 0),
    result_sha256           text NOT NULL CHECK (result_sha256 ~ '^[A-Fa-f0-9]{64}$'),
    created_at              timestamptz NOT NULL DEFAULT now(),
    CHECK (recovery_mode IN (
        'current_state',
        'current_milestone',
        'session_replay',
        'milestone_replay',
        'time_range_replay',
        'decision_history',
        'failure_fix_reconstruction',
        'complete_project_chronology',
        'summary_correction'
    ))
);

CREATE INDEX IF NOT EXISTS idx_recovery_operations_project_time
    ON agentcore.recovery_operations (project_id, created_at DESC);

CREATE TABLE IF NOT EXISTS agentcore.project_snapshots (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id              uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    repository_id           uuid NOT NULL REFERENCES agentcore.repositories(id) ON DELETE RESTRICT,
    worktree_id             uuid REFERENCES agentcore.worktrees(id) ON DELETE RESTRICT,
    snapshot_kind           text NOT NULL CHECK (snapshot_kind IN ('milestone','release','migration','recovery','final')),
    milestone               text,
    release_ref             text,
    commit_sha              text NOT NULL,
    branch_name             text,
    changed_file_manifest   jsonb NOT NULL DEFAULT '[]'::jsonb,
    source_hashes           jsonb NOT NULL DEFAULT '{}'::jsonb,
    patch_artifact_id       uuid REFERENCES agentcore.artifact_objects(id) ON DELETE RESTRICT,
    archive_artifact_id     uuid REFERENCES agentcore.artifact_objects(id) ON DELETE RESTRICT,
    test_evidence_event_ids uuid[] NOT NULL DEFAULT '{}'::uuid[],
    trust_class             agentcore.trust_class NOT NULL DEFAULT 'project_verified',
    created_at              timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, snapshot_kind, commit_sha, milestone, release_ref)
);

CREATE INDEX IF NOT EXISTS idx_project_snapshots_project_time
    ON agentcore.project_snapshots (project_id, created_at DESC);

ALTER TABLE agentcore.context_summaries
    ADD COLUMN IF NOT EXISTS supersedes_summary_id uuid REFERENCES agentcore.context_summaries(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS correction_reason text,
    ADD COLUMN IF NOT EXISTS is_current boolean NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS superseded_at timestamptz;

ALTER TABLE agentcore.context_summaries
    DROP CONSTRAINT IF EXISTS context_summaries_project_id_level_source_digest_algorithm__key;
ALTER TABLE agentcore.context_summaries
    DROP CONSTRAINT IF EXISTS uq_context_summary_source_algorithm;

CREATE UNIQUE INDEX IF NOT EXISTS uq_context_summary_current_source_version
    ON agentcore.context_summaries (project_id, level, source_digest, algorithm_version)
    WHERE is_current;

CREATE INDEX IF NOT EXISTS idx_context_summary_supersedes
    ON agentcore.context_summaries (supersedes_summary_id);

-- Creation is idempotent but never overwrites an existing summary body.
CREATE OR REPLACE FUNCTION agentcore.create_context_summary(
    p_project_id uuid,
    p_session_id uuid,
    p_level agentcore.context_level,
    p_bucket agentcore.context_bucket,
    p_title text,
    p_summary_text text,
    p_token_count integer,
    p_importance numeric,
    p_source_event_ids uuid[],
    p_compaction_run_id uuid DEFAULT NULL,
    p_algorithm_version text DEFAULT 'm3.native.v1'
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    v_source_digest text;
    v_summary_hash text;
    v_summary_id uuid;
    v_event_id uuid;
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);
    IF array_length(p_source_event_ids, 1) IS NULL THEN
        RAISE EXCEPTION 'context summary requires at least one source event' USING ERRCODE = '23514';
    END IF;
    IF EXISTS (
        SELECT 1 FROM agentcore.evidence_events e
        WHERE e.id = ANY(p_source_event_ids) AND e.project_id <> p_project_id
    ) THEN
        RAISE EXCEPTION 'summary source edge crosses project boundary' USING ERRCODE = '42501';
    END IF;

    SELECT agentcore.sha256_text(string_agg(id::text, ',' ORDER BY id))
      INTO v_source_digest
      FROM unnest(p_source_event_ids) AS id;
    v_summary_hash := agentcore.sha256_text(p_summary_text);

    SELECT id INTO v_summary_id
      FROM agentcore.context_summaries
     WHERE project_id = p_project_id
       AND level = p_level
       AND source_digest = v_source_digest
       AND algorithm_version = p_algorithm_version
       AND is_current
     FOR UPDATE;
    IF v_summary_id IS NOT NULL THEN
        RETURN v_summary_id;
    END IF;

    INSERT INTO agentcore.context_summaries (
        project_id, session_id, compaction_run_id, level, bucket, title,
        summary_text, summary_sha256, token_count, importance,
        algorithm_version, source_digest, revision, is_current
    ) VALUES (
        p_project_id, p_session_id, p_compaction_run_id, p_level, p_bucket, p_title,
        p_summary_text, v_summary_hash, p_token_count, p_importance,
        p_algorithm_version, v_source_digest, 1, true
    )
    RETURNING id INTO v_summary_id;

    FOREACH v_event_id IN ARRAY p_source_event_ids LOOP
        INSERT INTO agentcore.context_source_edges (summary_id, source_event_id)
        VALUES (v_summary_id, v_event_id)
        ON CONFLICT DO NOTHING;
    END LOOP;
    RETURN v_summary_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.supersede_context_summary(
    p_project_id uuid,
    p_summary_id uuid,
    p_corrected_summary_text text,
    p_token_count integer,
    p_correction_reason text,
    p_algorithm_version text DEFAULT 'm3.native.v2-correction'
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    v_old agentcore.context_summaries%ROWTYPE;
    v_new_id uuid;
    v_source_event_ids uuid[];
    v_result_hash text;
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);
    SELECT * INTO v_old
      FROM agentcore.context_summaries
     WHERE id = p_summary_id AND project_id = p_project_id
     FOR UPDATE;
    IF v_old.id IS NULL THEN
        RAISE EXCEPTION 'summary not found in project scope' USING ERRCODE = 'P0002';
    END IF;
    IF NOT v_old.is_current THEN
        RAISE EXCEPTION 'summary is already superseded' USING ERRCODE = '23514';
    END IF;

    SELECT array_agg(source_event_id ORDER BY source_event_id)
      INTO v_source_event_ids
      FROM agentcore.context_source_edges
     WHERE summary_id = p_summary_id;
    IF array_length(v_source_event_ids, 1) IS NULL THEN
        RAISE EXCEPTION 'summary correction requires original source edges' USING ERRCODE = '23514';
    END IF;

    UPDATE agentcore.context_summaries
       SET is_current = false, superseded_at = now()
     WHERE id = p_summary_id;

    INSERT INTO agentcore.context_summaries (
        project_id, session_id, compaction_run_id, level, bucket, title,
        summary_text, summary_sha256, token_count, importance,
        algorithm_version, source_digest, revision, supersedes_summary_id,
        correction_reason, is_current
    ) VALUES (
        v_old.project_id, v_old.session_id, v_old.compaction_run_id, v_old.level,
        v_old.bucket, v_old.title, p_corrected_summary_text,
        agentcore.sha256_text(p_corrected_summary_text), p_token_count, v_old.importance,
        p_algorithm_version, v_old.source_digest, v_old.revision + 1, v_old.id,
        p_correction_reason, true
    )
    RETURNING id INTO v_new_id;

    INSERT INTO agentcore.context_source_edges (summary_id, source_event_id, edge_kind, source_span)
    SELECT v_new_id, source_event_id, 'corrects', source_span
      FROM agentcore.context_source_edges
     WHERE summary_id = p_summary_id;

    v_result_hash := agentcore.sha256_text(
        p_summary_id::text || ':' || v_new_id::text || ':' || p_corrected_summary_text
    );
    INSERT INTO agentcore.recovery_operations (
        project_id, session_id, recovery_mode, request_scope, source_event_ids,
        omitted_item_count, result_sha256
    ) VALUES (
        p_project_id, v_old.session_id, 'summary_correction',
        jsonb_build_object('superseded_summary_id', p_summary_id, 'new_summary_id', v_new_id,
                           'reason', p_correction_reason),
        v_source_event_ids, 0, v_result_hash
    );
    RETURN v_new_id;
END;
$$;

-- Explicitly preserve the projection graph as recovery input. The projection worker
-- continues to regenerate GLOBAL_STATE.md and project STATE.md from canonical rows.
COMMENT ON TABLE agentcore.projection_revisions IS
    'Versioned generated STATE/DECISIONS/CONTEXT projections; recovery input, never hand-edited authority.';
COMMENT ON TABLE agentcore.recovery_operations IS
    'Auditable recovery and summary-correction metadata. Source evidence remains in evidence_events.';
COMMENT ON TABLE agentcore.project_snapshots IS
    'Governed Git plus artifact references at milestone/release/migration/recovery/final boundaries.';

GRANT SELECT ON agentcore.model_context_profiles, agentcore.model_context_profile_aliases
    TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT, INSERT ON agentcore.recovery_operations
    TO agentcore_ingest, agentcore_worker, agentcore_admin;
GRANT SELECT ON agentcore.project_snapshots
    TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT INSERT ON agentcore.project_snapshots TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.supersede_context_summary(uuid, uuid, text, integer, text, text)
    TO agentcore_worker, agentcore_admin;

INSERT INTO agentcore.schema_migrations (version, description, blueprint_level)
VALUES ('m3.002', 'effectively-unbounded recovery, versioned summary correction, model-aware context profiles, governed project snapshots', 'M3')
ON CONFLICT (version) DO NOTHING;

COMMIT;
