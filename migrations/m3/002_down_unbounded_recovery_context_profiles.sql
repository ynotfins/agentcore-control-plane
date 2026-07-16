-- M3 002 DOWN — guarded rollback for recovery/profile additions.
-- Refuses rollback after summary correction or snapshot/recovery evidence exists.

BEGIN;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM agentcore.context_summaries WHERE supersedes_summary_id IS NOT NULL)
       OR EXISTS (SELECT 1 FROM agentcore.recovery_operations)
       OR EXISTS (SELECT 1 FROM agentcore.project_snapshots) THEN
        RAISE EXCEPTION
            'm3.002 rollback refused: durable recovery/snapshot/correction records exist';
    END IF;
END;
$$;

DROP FUNCTION IF EXISTS agentcore.supersede_context_summary(uuid, uuid, text, integer, text, text);
DROP TABLE IF EXISTS agentcore.project_snapshots;
DROP TABLE IF EXISTS agentcore.recovery_operations;

DROP INDEX IF EXISTS agentcore.idx_context_summary_supersedes;
DROP INDEX IF EXISTS agentcore.uq_context_summary_current_source_version;

ALTER TABLE agentcore.context_summaries
    DROP COLUMN IF EXISTS superseded_at,
    DROP COLUMN IF EXISTS is_current,
    DROP COLUMN IF EXISTS correction_reason,
    DROP COLUMN IF EXISTS supersedes_summary_id;

ALTER TABLE agentcore.context_summaries
    ADD CONSTRAINT uq_context_summary_source_algorithm
    UNIQUE (project_id, level, source_digest, algorithm_version);

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
    SELECT agentcore.sha256_text(string_agg(id::text, ',' ORDER BY id))
      INTO v_source_digest FROM unnest(p_source_event_ids) AS id;
    v_summary_hash := agentcore.sha256_text(p_summary_text);
    INSERT INTO agentcore.context_summaries (
        project_id, session_id, compaction_run_id, level, bucket, title,
        summary_text, summary_sha256, token_count, importance,
        algorithm_version, source_digest
    ) VALUES (
        p_project_id, p_session_id, p_compaction_run_id, p_level, p_bucket, p_title,
        p_summary_text, v_summary_hash, p_token_count, p_importance,
        p_algorithm_version, v_source_digest
    )
    ON CONFLICT (project_id, level, source_digest, algorithm_version) DO UPDATE
      SET summary_text = EXCLUDED.summary_text,
          summary_sha256 = EXCLUDED.summary_sha256,
          token_count = EXCLUDED.token_count,
          importance = EXCLUDED.importance,
          revision = agentcore.context_summaries.revision + 1
    RETURNING id INTO v_summary_id;
    FOREACH v_event_id IN ARRAY p_source_event_ids LOOP
        INSERT INTO agentcore.context_source_edges (summary_id, source_event_id)
        VALUES (v_summary_id, v_event_id)
        ON CONFLICT DO NOTHING;
    END LOOP;
    RETURN v_summary_id;
END;
$$;

DELETE FROM agentcore.model_context_budgets
WHERE budget_name IN (
    'acceptance-small',
    'legacy-4096',
    'standard-context',
    'large-context',
    'one-million-context',
    'future-above-million'
);
ALTER TABLE agentcore.sessions DROP COLUMN IF EXISTS context_profile_name;
DROP TABLE IF EXISTS agentcore.model_context_profile_aliases;
DROP TABLE IF EXISTS agentcore.model_context_profiles;

DELETE FROM agentcore.schema_migrations WHERE version = 'm3.002';

COMMIT;
