-- M3 001 UP — Lossless Context and STATE Projections
--
-- Authority: BLUEPRINT.md M3 and docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md M3.
-- Target: PostgreSQL 18 agent_core on 127.0.0.1:55433.
-- Scope: L0/L1/L2/L3 context hierarchy, source edges, compaction runs,
--        deterministic projection revisions, artifact archive locations,
--        contradiction review path, and token-budget assembly.
--
-- Intentionally NOT included: memory gateway expansion (M4), Cognee integration
-- (M5), LangGraph checkpoints (M6), dynamic Bifrost leases (M6).

BEGIN;

CREATE SCHEMA IF NOT EXISTS agentcore;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = 'agentcore'::regnamespace AND typname = 'context_level') THEN
    CREATE TYPE agentcore.context_level AS ENUM ('L0', 'L1', 'L2', 'L3', 'L4');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = 'agentcore'::regnamespace AND typname = 'context_bucket') THEN
    CREATE TYPE agentcore.context_bucket AS ENUM ('static_stable', 'active_dynamic', 'archived');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = 'agentcore'::regnamespace AND typname = 'compaction_status') THEN
    CREATE TYPE agentcore.compaction_status AS ENUM ('pending', 'in_progress', 'completed', 'interrupted_recovered', 'failed');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = 'agentcore'::regnamespace AND typname = 'projection_kind') THEN
    CREATE TYPE agentcore.projection_kind AS ENUM ('global_state', 'project_state', 'decisions', 'context_index');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = 'agentcore'::regnamespace AND typname = 'proposal_status') THEN
    CREATE TYPE agentcore.proposal_status AS ENUM ('proposed', 'accepted', 'rejected', 'superseded');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = 'agentcore'::regnamespace AND typname = 'storage_tier') THEN
    CREATE TYPE agentcore.storage_tier AS ENUM ('hot_h', 'cold_e');
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS agentcore.compaction_runs (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    session_id          uuid REFERENCES agentcore.sessions(id) ON DELETE RESTRICT,
    source_level        agentcore.context_level NOT NULL,
    target_level        agentcore.context_level NOT NULL,
    idempotency_key     text NOT NULL,
    algorithm_version   text NOT NULL DEFAULT 'm3.native.v1',
    input_digest        text NOT NULL,
    output_digest       text,
    status              agentcore.compaction_status NOT NULL DEFAULT 'in_progress',
    started_at          timestamptz NOT NULL DEFAULT now(),
    completed_at        timestamptz,
    recovered_at        timestamptz,
    UNIQUE (project_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS agentcore.context_summaries (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    session_id          uuid REFERENCES agentcore.sessions(id) ON DELETE RESTRICT,
    compaction_run_id   uuid REFERENCES agentcore.compaction_runs(id) ON DELETE RESTRICT,
    level               agentcore.context_level NOT NULL,
    bucket              agentcore.context_bucket NOT NULL DEFAULT 'active_dynamic',
    title               text NOT NULL,
    summary_text        text NOT NULL,
    summary_sha256      text NOT NULL CHECK (summary_sha256 ~ '^[A-Fa-f0-9]{64}$'),
    token_count         integer NOT NULL CHECK (token_count >= 0),
    importance          numeric(5,4) NOT NULL DEFAULT 0.5000 CHECK (importance >= 0 AND importance <= 1),
    algorithm_version   text NOT NULL DEFAULT 'm3.native.v1',
    source_digest       text NOT NULL,
    revision            integer NOT NULL DEFAULT 1,
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, level, source_digest, algorithm_version)
);

CREATE TABLE IF NOT EXISTS agentcore.context_source_edges (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    summary_id          uuid NOT NULL REFERENCES agentcore.context_summaries(id) ON DELETE CASCADE,
    source_event_id     uuid NOT NULL REFERENCES agentcore.evidence_events(id) ON DELETE RESTRICT,
    edge_kind           text NOT NULL DEFAULT 'summarizes',
    source_span         jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (summary_id, source_event_id, edge_kind)
);

CREATE TABLE IF NOT EXISTS agentcore.event_dedupe_links (
    duplicate_event_id  uuid PRIMARY KEY REFERENCES agentcore.evidence_events(id) ON DELETE RESTRICT,
    canonical_event_id  uuid NOT NULL REFERENCES agentcore.evidence_events(id) ON DELETE RESTRICT,
    project_id          uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    reason              text NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CHECK (duplicate_event_id <> canonical_event_id)
);

CREATE TABLE IF NOT EXISTS agentcore.artifact_locations (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id         uuid NOT NULL REFERENCES agentcore.artifact_objects(id) ON DELETE RESTRICT,
    storage_tier        agentcore.storage_tier NOT NULL,
    storage_uri         text NOT NULL,
    sha256              text NOT NULL CHECK (sha256 ~ '^[A-Fa-f0-9]{64}$'),
    is_active           boolean NOT NULL DEFAULT true,
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (artifact_id, storage_tier, storage_uri)
);

CREATE TABLE IF NOT EXISTS agentcore.model_context_budgets (
    budget_name         text PRIMARY KEY,
    max_tokens          integer NOT NULL CHECK (max_tokens > 0),
    preserve_recent     integer NOT NULL DEFAULT 5 CHECK (preserve_recent >= 0),
    notes               text
);

CREATE TABLE IF NOT EXISTS agentcore.fact_proposals (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    fact_key            text NOT NULL,
    proposed_value      jsonb NOT NULL,
    contradicts_event_id uuid REFERENCES agentcore.evidence_events(id) ON DELETE RESTRICT,
    status              agentcore.proposal_status NOT NULL DEFAULT 'proposed',
    trust_class         agentcore.trust_class NOT NULL DEFAULT 'raw_untrusted',
    provenance          jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.projection_revisions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    kind                agentcore.projection_kind NOT NULL,
    target_path         text NOT NULL,
    revision            integer NOT NULL,
    content_sha256      text NOT NULL CHECK (content_sha256 ~ '^[A-Fa-f0-9]{64}$'),
    source_revision     text NOT NULL,
    generated_at        timestamptz NOT NULL DEFAULT now(),
    previous_revision_id uuid REFERENCES agentcore.projection_revisions(id) ON DELETE SET NULL,
    is_current          boolean NOT NULL DEFAULT true,
    UNIQUE (target_path, revision)
);

CREATE INDEX IF NOT EXISTS idx_context_project_level
    ON agentcore.context_summaries (project_id, level, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_edges_summary
    ON agentcore.context_source_edges (summary_id);
CREATE INDEX IF NOT EXISTS idx_context_edges_event
    ON agentcore.context_source_edges (source_event_id);
CREATE INDEX IF NOT EXISTS idx_projection_target_current
    ON agentcore.projection_revisions (target_path, is_current);
CREATE INDEX IF NOT EXISTS idx_fact_proposals_project_status
    ON agentcore.fact_proposals (project_id, status, created_at DESC);

INSERT INTO agentcore.model_context_budgets (budget_name, max_tokens, preserve_recent, notes)
VALUES
  ('small', 512, 3, 'M3 acceptance-test budget'),
  ('default', 4096, 10, 'Default startup context'),
  ('large', 16000, 20, 'Large-context model budget')
ON CONFLICT (budget_name) DO UPDATE
SET max_tokens = EXCLUDED.max_tokens,
    preserve_recent = EXCLUDED.preserve_recent,
    notes = EXCLUDED.notes;

CREATE OR REPLACE FUNCTION agentcore.sha256_text(p_text text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
SELECT encode(digest(convert_to(coalesce(p_text, ''), 'UTF8'), 'sha256'), 'hex')
$$;

CREATE OR REPLACE FUNCTION agentcore.start_compaction_run(
    p_project_id uuid,
    p_session_id uuid,
    p_source_level agentcore.context_level,
    p_target_level agentcore.context_level,
    p_idempotency_key text,
    p_input_digest text,
    p_algorithm_version text DEFAULT 'm3.native.v1'
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    run_id uuid;
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    INSERT INTO agentcore.compaction_runs (
        project_id, session_id, source_level, target_level, idempotency_key,
        input_digest, algorithm_version, status
    )
    VALUES (
        p_project_id, p_session_id, p_source_level, p_target_level,
        p_idempotency_key, p_input_digest, p_algorithm_version, 'in_progress'
    )
    ON CONFLICT (project_id, idempotency_key) DO UPDATE
      SET status = CASE
          WHEN agentcore.compaction_runs.status IN ('failed', 'interrupted_recovered') THEN 'in_progress'::agentcore.compaction_status
          ELSE agentcore.compaction_runs.status
      END
    RETURNING id INTO run_id;

    RETURN run_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.complete_compaction_run(
    p_project_id uuid,
    p_compaction_run_id uuid,
    p_output_digest text
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    UPDATE agentcore.compaction_runs
    SET status = 'completed',
        output_digest = p_output_digest,
        completed_at = now()
    WHERE id = p_compaction_run_id
      AND project_id = p_project_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.recover_interrupted_compactions()
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    recovered integer;
BEGIN
    UPDATE agentcore.compaction_runs
    SET status = 'interrupted_recovered',
        recovered_at = now()
    WHERE status = 'in_progress';

    GET DIAGNOSTICS recovered = ROW_COUNT;
    RETURN recovered;
END;
$$;

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
    summary_id uuid;
    event_id uuid;
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    IF array_length(p_source_event_ids, 1) IS NULL THEN
        RAISE EXCEPTION 'context summary requires at least one source event'
            USING ERRCODE = '23514';
    END IF;

    IF EXISTS (
        SELECT 1 FROM agentcore.evidence_events e
        WHERE e.id = ANY(p_source_event_ids)
          AND e.project_id <> p_project_id
    ) THEN
        RAISE EXCEPTION 'summary source edge crosses project boundary'
            USING ERRCODE = '42501';
    END IF;

    SELECT agentcore.sha256_text(string_agg(id::text, ',' ORDER BY id))
    INTO v_source_digest
    FROM unnest(p_source_event_ids) AS id;

    v_summary_hash := agentcore.sha256_text(p_summary_text);

    INSERT INTO agentcore.context_summaries (
        project_id, session_id, compaction_run_id, level, bucket, title,
        summary_text, summary_sha256, token_count, importance,
        algorithm_version, source_digest
    )
    VALUES (
        p_project_id, p_session_id, p_compaction_run_id, p_level, p_bucket,
        p_title, p_summary_text, v_summary_hash, p_token_count, p_importance,
        p_algorithm_version, v_source_digest
    )
    ON CONFLICT (project_id, level, source_digest, algorithm_version) DO UPDATE
      SET summary_text = EXCLUDED.summary_text,
          summary_sha256 = EXCLUDED.summary_sha256,
          token_count = EXCLUDED.token_count,
          importance = EXCLUDED.importance,
          revision = agentcore.context_summaries.revision + 1
    RETURNING id INTO summary_id;

    FOREACH event_id IN ARRAY p_source_event_ids LOOP
        INSERT INTO agentcore.context_source_edges (summary_id, source_event_id)
        VALUES (summary_id, event_id)
        ON CONFLICT DO NOTHING;
    END LOOP;

    RETURN summary_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.expand_summary(p_summary_id uuid)
RETURNS TABLE(
    summary_id uuid,
    source_event_id uuid,
    event_kind agentcore.event_kind,
    payload jsonb,
    artifact_id uuid,
    storage_uri text,
    trust_class agentcore.trust_class,
    provenance jsonb
)
LANGUAGE sql
STABLE
AS $$
SELECT
    s.id,
    e.id,
    e.event_kind,
    e.payload,
    e.artifact_id,
    COALESCE(loc.storage_uri, a.storage_uri) AS storage_uri,
    e.trust_class,
    e.provenance
FROM agentcore.context_summaries s
JOIN agentcore.context_source_edges edge ON edge.summary_id = s.id
JOIN agentcore.evidence_events e ON e.id = edge.source_event_id
LEFT JOIN agentcore.artifact_objects a ON a.id = e.artifact_id
LEFT JOIN LATERAL (
    SELECT l.storage_uri
    FROM agentcore.artifact_locations l
    WHERE l.artifact_id = a.id
      AND l.is_active
    ORDER BY CASE l.storage_tier WHEN 'cold_e' THEN 0 ELSE 1 END, l.created_at DESC
    LIMIT 1
) loc ON true
WHERE s.id = p_summary_id
ORDER BY edge.created_at, e.accepted_at
$$;

CREATE OR REPLACE FUNCTION agentcore.mark_event_duplicate(
    p_project_id uuid,
    p_duplicate_event_id uuid,
    p_canonical_event_id uuid,
    p_reason text
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    IF EXISTS (
        SELECT 1 FROM agentcore.evidence_events e
        WHERE e.id IN (p_duplicate_event_id, p_canonical_event_id)
          AND e.project_id <> p_project_id
    ) THEN
        RAISE EXCEPTION 'dedupe link crosses project boundary'
            USING ERRCODE = '42501';
    END IF;

    INSERT INTO agentcore.event_dedupe_links (
        duplicate_event_id, canonical_event_id, project_id, reason
    )
    VALUES (p_duplicate_event_id, p_canonical_event_id, p_project_id, p_reason)
    ON CONFLICT (duplicate_event_id) DO UPDATE
      SET canonical_event_id = EXCLUDED.canonical_event_id,
          reason = EXCLUDED.reason;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.register_artifact_location(
    p_project_id uuid,
    p_artifact_id uuid,
    p_storage_tier agentcore.storage_tier,
    p_storage_uri text,
    p_sha256 text
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    location_id uuid;
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    IF NOT EXISTS (
        SELECT 1 FROM agentcore.artifact_objects
        WHERE id = p_artifact_id
          AND project_id = p_project_id
          AND lower(sha256) = lower(p_sha256)
    ) THEN
        RAISE EXCEPTION 'artifact location does not match project/artifact/hash'
            USING ERRCODE = '42501';
    END IF;

    IF p_storage_tier = 'cold_e' THEN
        UPDATE agentcore.artifact_locations
        SET is_active = false
        WHERE artifact_id = p_artifact_id
          AND storage_tier = 'hot_h';
    END IF;

    INSERT INTO agentcore.artifact_locations (
        artifact_id, storage_tier, storage_uri, sha256, is_active
    )
    VALUES (p_artifact_id, p_storage_tier, p_storage_uri, lower(p_sha256), true)
    ON CONFLICT (artifact_id, storage_tier, storage_uri) DO UPDATE
      SET is_active = true
    RETURNING id INTO location_id;

    RETURN location_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.propose_fact_review(
    p_project_id uuid,
    p_fact_key text,
    p_proposed_value jsonb,
    p_contradicts_event_id uuid,
    p_trust_class agentcore.trust_class DEFAULT 'raw_untrusted',
    p_provenance jsonb DEFAULT '{}'::jsonb
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    proposal_id uuid;
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    INSERT INTO agentcore.fact_proposals (
        project_id, fact_key, proposed_value, contradicts_event_id,
        trust_class, provenance
    )
    VALUES (
        p_project_id, p_fact_key, p_proposed_value, p_contradicts_event_id,
        p_trust_class, p_provenance
    )
    RETURNING id INTO proposal_id;

    RETURN proposal_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.assemble_context_window(
    p_project_id uuid,
    p_budget_name text
)
RETURNS TABLE(
    item_type text,
    item_id uuid,
    level agentcore.context_level,
    bucket agentcore.context_bucket,
    body text,
    token_count integer,
    importance numeric,
    cumulative_tokens bigint
)
LANGUAGE sql
STABLE
AS $$
WITH budget AS (
    SELECT max_tokens FROM agentcore.model_context_budgets WHERE budget_name = p_budget_name
),
items AS (
    SELECT
        'summary'::text AS item_type,
        id AS item_id,
        level,
        bucket,
        summary_text AS body,
        token_count,
        importance,
        created_at
    FROM agentcore.context_summaries
    WHERE project_id = p_project_id
    UNION ALL
    SELECT
        'raw_event'::text,
        id,
        'L0'::agentcore.context_level,
        'active_dynamic'::agentcore.context_bucket,
        payload::text,
        greatest(1, ceil(length(payload::text) / 4.0))::integer,
        1.0::numeric,
        accepted_at
    FROM agentcore.evidence_events
    WHERE project_id = p_project_id
    ORDER BY importance DESC, created_at DESC
),
ranked AS (
    SELECT
        *,
        sum(token_count) OVER (
            ORDER BY
              CASE bucket WHEN 'static_stable' THEN 0 ELSE 1 END,
              CASE level WHEN 'L3' THEN 0 WHEN 'L2' THEN 1 WHEN 'L1' THEN 2 ELSE 3 END,
              importance DESC,
              created_at DESC
        ) AS cumulative_tokens
    FROM items
)
SELECT item_type, item_id, level, bucket, body, token_count, importance, cumulative_tokens
FROM ranked, budget
WHERE cumulative_tokens <= budget.max_tokens
ORDER BY cumulative_tokens
$$;

CREATE OR REPLACE FUNCTION agentcore.record_projection_revision(
    p_project_id uuid,
    p_kind agentcore.projection_kind,
    p_target_path text,
    p_content_sha256 text,
    p_source_revision text
)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    previous_id uuid;
    next_revision integer;
BEGIN
    SELECT id, revision
    INTO previous_id, next_revision
    FROM agentcore.projection_revisions
    WHERE target_path = p_target_path
      AND is_current
    ORDER BY revision DESC
    LIMIT 1;

    next_revision := coalesce(next_revision, 0) + 1;

    UPDATE agentcore.projection_revisions
    SET is_current = false
    WHERE target_path = p_target_path
      AND is_current;

    INSERT INTO agentcore.projection_revisions (
        project_id, kind, target_path, revision, content_sha256,
        source_revision, previous_revision_id, is_current
    )
    VALUES (
        p_project_id, p_kind, p_target_path, next_revision,
        lower(p_content_sha256), p_source_revision, previous_id, true
    );

    RETURN next_revision;
END;
$$;

GRANT SELECT ON ALL TABLES IN SCHEMA agentcore TO agentcore_read, agentcore_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA agentcore TO agentcore_ingest, agentcore_worker;
GRANT INSERT ON agentcore.event_dedupe_links TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.compaction_runs TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.context_summaries TO agentcore_worker, agentcore_admin;
GRANT INSERT ON agentcore.context_source_edges TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.artifact_locations TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.fact_proposals TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.projection_revisions TO agentcore_worker, agentcore_admin;
GRANT ALL ON ALL TABLES IN SCHEMA agentcore TO agentcore_admin;

GRANT EXECUTE ON FUNCTION agentcore.start_compaction_run(uuid, uuid, agentcore.context_level, agentcore.context_level, text, text, text) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.complete_compaction_run(uuid, uuid, text) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.recover_interrupted_compactions() TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.create_context_summary(uuid, uuid, agentcore.context_level, agentcore.context_bucket, text, text, integer, numeric, uuid[], uuid, text) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.expand_summary(uuid) TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.mark_event_duplicate(uuid, uuid, uuid, text) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.register_artifact_location(uuid, uuid, agentcore.storage_tier, text, text) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.propose_fact_review(uuid, text, jsonb, uuid, agentcore.trust_class, jsonb) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.assemble_context_window(uuid, text) TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.record_projection_revision(uuid, agentcore.projection_kind, text, text, text) TO agentcore_worker, agentcore_admin;

INSERT INTO agentcore.schema_migrations (version, description, blueprint_level)
VALUES ('m3.001', 'lossless context hierarchy, exact expansion, COMB projections', 'M3')
ON CONFLICT (version) DO NOTHING;

COMMIT;
