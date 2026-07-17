-- M2 001 UP — Canonical Identity and Immutable Evidence
--
-- Authority: BLUEPRINT.md M2 and docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md M2.
-- Target: PostgreSQL 18 agent_core on 127.0.0.1:55433.
-- Scope: identities, immutable evidence, content-addressed artifacts, project isolation,
--        queue/claim/lease/dead-letter primitives.
--
-- Intentionally NOT included: LangGraph checkpoint tables (M6), context compaction hierarchy
-- (M3), Cognee schema (M5), or memory gateway implementation (M4).

BEGIN;

CREATE SCHEMA IF NOT EXISTS agentcore;

CREATE TABLE IF NOT EXISTS agentcore.schema_migrations (
    version         text PRIMARY KEY,
    description     text NOT NULL,
    applied_at      timestamptz NOT NULL DEFAULT now(),
    applied_by      text NOT NULL DEFAULT current_user,
    blueprint_level text NOT NULL DEFAULT 'M2'
);

CREATE TYPE agentcore.trust_class AS ENUM (
    'operator_verified',
    'system_verified',
    'project_verified',
    'raw_untrusted',
    'quarantined',
    'rejected'
);

CREATE TYPE agentcore.event_kind AS ENUM (
    'prompt',
    'message',
    'tool_event',
    'decision',
    'output',
    'accepted_evidence',
    'state_transition',
    'test_result',
    'handoff'
);

CREATE TYPE agentcore.queue_status AS ENUM (
    'pending',
    'claimed',
    'done',
    'dead'
);

CREATE TYPE agentcore.claim_status AS ENUM (
    'active',
    'released',
    'expired'
);

CREATE TYPE agentcore.capability_lease_status AS ENUM (
    'active',
    'revoked',
    'expired'
);

CREATE TABLE IF NOT EXISTS agentcore.machines (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_name    text NOT NULL UNIQUE,
    hardware_ref    text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.users (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username        text NOT NULL UNIQUE,
    display_name    text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.repositories (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_key        text NOT NULL UNIQUE,
    canonical_path  text NOT NULL UNIQUE,
    remote_url      text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.worktrees (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id   uuid NOT NULL REFERENCES agentcore.repositories(id) ON DELETE RESTRICT,
    worktree_path   text NOT NULL UNIQUE,
    branch_name     text,
    head_commit     text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.projects (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_key          text NOT NULL UNIQUE,
    project_name         text NOT NULL,
    repository_id        uuid REFERENCES agentcore.repositories(id) ON DELETE RESTRICT,
    primary_worktree_id  uuid REFERENCES agentcore.worktrees(id) ON DELETE RESTRICT,
    root_path            text NOT NULL,
    current_milestone    text,
    trust_class          agentcore.trust_class NOT NULL DEFAULT 'project_verified',
    created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.project_worktrees (
    project_id      uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE CASCADE,
    worktree_id     uuid NOT NULL REFERENCES agentcore.worktrees(id) ON DELETE CASCADE,
    is_primary      boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (project_id, worktree_id)
);

CREATE TABLE IF NOT EXISTS agentcore.ide_clients (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    client_key      text NOT NULL UNIQUE,
    display_name    text NOT NULL,
    profile_id      text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.agents (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_key       text NOT NULL UNIQUE,
    display_name    text NOT NULL,
    model_hint      text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.sessions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    client_id       uuid NOT NULL REFERENCES agentcore.ide_clients(id) ON DELETE RESTRICT,
    agent_id        uuid NOT NULL REFERENCES agentcore.agents(id) ON DELETE RESTRICT,
    session_key     text NOT NULL UNIQUE,
    started_at      timestamptz NOT NULL DEFAULT now(),
    ended_at        timestamptz
);

CREATE TABLE IF NOT EXISTS agentcore.runs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      uuid NOT NULL REFERENCES agentcore.sessions(id) ON DELETE RESTRICT,
    run_key         text NOT NULL UNIQUE,
    started_at      timestamptz NOT NULL DEFAULT now(),
    ended_at        timestamptz
);

CREATE TABLE IF NOT EXISTS agentcore.workflows (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    workflow_key    text NOT NULL UNIQUE,
    display_name    text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.workflow_threads (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id     uuid NOT NULL REFERENCES agentcore.workflows(id) ON DELETE RESTRICT,
    thread_key      text NOT NULL UNIQUE,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.source_identities (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id          uuid NOT NULL REFERENCES agentcore.machines(id) ON DELETE RESTRICT,
    user_id             uuid NOT NULL REFERENCES agentcore.users(id) ON DELETE RESTRICT,
    project_id          uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    repository_id       uuid NOT NULL REFERENCES agentcore.repositories(id) ON DELETE RESTRICT,
    worktree_id         uuid NOT NULL REFERENCES agentcore.worktrees(id) ON DELETE RESTRICT,
    client_id           uuid NOT NULL REFERENCES agentcore.ide_clients(id) ON DELETE RESTRICT,
    agent_id            uuid NOT NULL REFERENCES agentcore.agents(id) ON DELETE RESTRICT,
    session_id          uuid NOT NULL REFERENCES agentcore.sessions(id) ON DELETE RESTRICT,
    run_id              uuid NOT NULL REFERENCES agentcore.runs(id) ON DELETE RESTRICT,
    workflow_thread_id  uuid NOT NULL REFERENCES agentcore.workflow_threads(id) ON DELETE RESTRICT,
    source_label        text NOT NULL,
    trust_class         agentcore.trust_class NOT NULL DEFAULT 'project_verified',
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agentcore.artifact_objects (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    sha256              text NOT NULL CHECK (sha256 ~ '^[A-Fa-f0-9]{64}$'),
    bytes               bigint NOT NULL CHECK (bytes >= 0),
    storage_uri         text NOT NULL,
    mime_type           text,
    trust_class         agentcore.trust_class NOT NULL DEFAULT 'raw_untrusted',
    source_identity_id  uuid REFERENCES agentcore.source_identities(id) ON DELETE RESTRICT,
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, sha256)
);

CREATE TABLE IF NOT EXISTS agentcore.evidence_events (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    source_identity_id  uuid NOT NULL REFERENCES agentcore.source_identities(id) ON DELETE RESTRICT,
    event_kind          agentcore.event_kind NOT NULL,
    idempotency_key     text NOT NULL,
    payload             jsonb NOT NULL DEFAULT '{}'::jsonb,
    artifact_id         uuid REFERENCES agentcore.artifact_objects(id) ON DELETE RESTRICT,
    schema_version      text NOT NULL DEFAULT 'm2.v1',
    trust_class         agentcore.trust_class NOT NULL DEFAULT 'project_verified',
    provenance          jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at         timestamptz NOT NULL DEFAULT now(),
    accepted_at         timestamptz NOT NULL DEFAULT now(),
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_identity_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_evidence_project_time
    ON agentcore.evidence_events (project_id, accepted_at DESC);

CREATE INDEX IF NOT EXISTS idx_artifact_project_sha
    ON agentcore.artifact_objects (project_id, sha256);

CREATE TABLE IF NOT EXISTS agentcore.work_queue (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    dedupe_key          text NOT NULL,
    work_kind           text NOT NULL,
    payload             jsonb NOT NULL DEFAULT '{}'::jsonb,
    status              agentcore.queue_status NOT NULL DEFAULT 'pending',
    attempts            integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    max_attempts        integer NOT NULL DEFAULT 3 CHECK (max_attempts > 0),
    available_at        timestamptz NOT NULL DEFAULT now(),
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, dedupe_key)
);

CREATE TABLE IF NOT EXISTS agentcore.work_claims (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    work_item_id        uuid NOT NULL REFERENCES agentcore.work_queue(id) ON DELETE RESTRICT,
    claimant_identity_id uuid NOT NULL REFERENCES agentcore.source_identities(id) ON DELETE RESTRICT,
    status              agentcore.claim_status NOT NULL DEFAULT 'active',
    claimed_at          timestamptz NOT NULL DEFAULT now(),
    lease_expires_at    timestamptz NOT NULL,
    released_at         timestamptz
);

CREATE TABLE IF NOT EXISTS agentcore.dead_letters (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    work_item_id        uuid NOT NULL REFERENCES agentcore.work_queue(id) ON DELETE RESTRICT,
    reason              text NOT NULL,
    original_payload    jsonb NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (work_item_id)
);

CREATE TABLE IF NOT EXISTS agentcore.capability_leases (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    holder_identity_id  uuid NOT NULL REFERENCES agentcore.source_identities(id) ON DELETE RESTRICT,
    tool_name           text NOT NULL,
    step_id             text NOT NULL,
    status              agentcore.capability_lease_status NOT NULL DEFAULT 'active',
    permitted_operations text[] NOT NULL DEFAULT ARRAY[]::text[],
    justification       text NOT NULL,
    granted_at          timestamptz NOT NULL DEFAULT now(),
    lease_expires_at    timestamptz NOT NULL,
    revoked_at          timestamptz
);

CREATE INDEX IF NOT EXISTS idx_queue_project_status
    ON agentcore.work_queue (project_id, status, available_at);
CREATE INDEX IF NOT EXISTS idx_claims_work_status
    ON agentcore.work_claims (work_item_id, status);

CREATE UNIQUE INDEX IF NOT EXISTS uq_work_claims_one_active
    ON agentcore.work_claims (work_item_id)
    WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_leases_project_status
    ON agentcore.capability_leases (project_id, status, lease_expires_at);

CREATE OR REPLACE FUNCTION agentcore.current_project_id()
RETURNS uuid
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    raw text;
BEGIN
    raw := current_setting('agentcore.current_project_id', true);
    IF raw IS NULL OR raw = '' THEN
        RETURN NULL;
    END IF;
    RETURN raw::uuid;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.enforce_event_immutable()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'immutable evidence event % cannot be %', OLD.id, TG_OP
        USING ERRCODE = '42501';
END;
$$;

DROP TRIGGER IF EXISTS trg_evidence_immutable ON agentcore.evidence_events;
CREATE TRIGGER trg_evidence_immutable
    BEFORE UPDATE OR DELETE ON agentcore.evidence_events
    FOR EACH ROW
    EXECUTE FUNCTION agentcore.enforce_event_immutable();

CREATE OR REPLACE FUNCTION agentcore.touch_queue_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_work_queue_touch ON agentcore.work_queue;
CREATE TRIGGER trg_work_queue_touch
    BEFORE UPDATE ON agentcore.work_queue
    FOR EACH ROW
    EXECUTE FUNCTION agentcore.touch_queue_updated_at();

ALTER TABLE agentcore.evidence_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE agentcore.artifact_objects ENABLE ROW LEVEL SECURITY;
ALTER TABLE agentcore.work_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE agentcore.capability_leases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS p_evidence_project_scope ON agentcore.evidence_events;
CREATE POLICY p_evidence_project_scope ON agentcore.evidence_events
    USING (project_id = agentcore.current_project_id())
    WITH CHECK (project_id = agentcore.current_project_id());

DROP POLICY IF EXISTS p_artifact_project_scope ON agentcore.artifact_objects;
CREATE POLICY p_artifact_project_scope ON agentcore.artifact_objects
    USING (project_id = agentcore.current_project_id())
    WITH CHECK (project_id = agentcore.current_project_id());

DROP POLICY IF EXISTS p_queue_project_scope ON agentcore.work_queue;
CREATE POLICY p_queue_project_scope ON agentcore.work_queue
    USING (project_id = agentcore.current_project_id())
    WITH CHECK (project_id = agentcore.current_project_id());

DROP POLICY IF EXISTS p_lease_project_scope ON agentcore.capability_leases;
CREATE POLICY p_lease_project_scope ON agentcore.capability_leases
    USING (project_id = agentcore.current_project_id())
    WITH CHECK (project_id = agentcore.current_project_id());

CREATE OR REPLACE FUNCTION agentcore.assert_project_scope(p_project_id uuid)
RETURNS void
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF agentcore.current_project_id() IS NULL THEN
        RAISE EXCEPTION 'agentcore.current_project_id is not set'
            USING ERRCODE = '42501';
    END IF;
    IF agentcore.current_project_id() <> p_project_id THEN
        RAISE EXCEPTION 'cross-project write rejected: current project %, target project %',
            agentcore.current_project_id(), p_project_id
            USING ERRCODE = '42501';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.append_evidence_event(
    p_project_id uuid,
    p_source_identity_id uuid,
    p_event_kind agentcore.event_kind,
    p_idempotency_key text,
    p_payload jsonb DEFAULT '{}'::jsonb,
    p_artifact_id uuid DEFAULT NULL,
    p_trust_class agentcore.trust_class DEFAULT 'project_verified',
    p_provenance jsonb DEFAULT '{}'::jsonb
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    existing_id uuid;
    inserted_id uuid;
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    SELECT id INTO existing_id
    FROM agentcore.evidence_events
    WHERE source_identity_id = p_source_identity_id
      AND idempotency_key = p_idempotency_key;

    IF existing_id IS NOT NULL THEN
        RETURN existing_id;
    END IF;

    INSERT INTO agentcore.evidence_events (
        project_id, source_identity_id, event_kind, idempotency_key, payload,
        artifact_id, trust_class, provenance
    )
    VALUES (
        p_project_id, p_source_identity_id, p_event_kind, p_idempotency_key,
        p_payload, p_artifact_id, p_trust_class, p_provenance
    )
    RETURNING id INTO inserted_id;

    RETURN inserted_id;
EXCEPTION WHEN unique_violation THEN
    SELECT id INTO existing_id
    FROM agentcore.evidence_events
    WHERE source_identity_id = p_source_identity_id
      AND idempotency_key = p_idempotency_key;
    RETURN existing_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.enqueue_work(
    p_project_id uuid,
    p_dedupe_key text,
    p_work_kind text,
    p_payload jsonb DEFAULT '{}'::jsonb,
    p_max_attempts integer DEFAULT 3
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    work_id uuid;
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    INSERT INTO agentcore.work_queue (project_id, dedupe_key, work_kind, payload, max_attempts)
    VALUES (p_project_id, p_dedupe_key, p_work_kind, p_payload, p_max_attempts)
    ON CONFLICT (project_id, dedupe_key) DO UPDATE
        SET payload = EXCLUDED.payload
        WHERE agentcore.work_queue.status = 'pending'
    RETURNING id INTO work_id;

    IF work_id IS NULL THEN
        SELECT id INTO work_id
        FROM agentcore.work_queue
        WHERE project_id = p_project_id AND dedupe_key = p_dedupe_key;
    END IF;

    RETURN work_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.claim_work(
    p_project_id uuid,
    p_claimant_identity_id uuid,
    p_lease_seconds integer DEFAULT 30
)
RETURNS TABLE(work_item_id uuid, claim_id uuid)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    selected_id uuid;
    new_claim_id uuid;
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    SELECT id INTO selected_id
    FROM agentcore.work_queue
    WHERE project_id = p_project_id
      AND status = 'pending'
      AND available_at <= now()
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1;

    IF selected_id IS NULL THEN
        RETURN;
    END IF;

    UPDATE agentcore.work_queue
    SET status = 'claimed',
        attempts = attempts + 1
    WHERE id = selected_id;

    INSERT INTO agentcore.work_claims (work_item_id, claimant_identity_id, lease_expires_at)
    VALUES (selected_id, p_claimant_identity_id, now() + make_interval(secs => p_lease_seconds))
    RETURNING id INTO new_claim_id;

    work_item_id := selected_id;
    claim_id := new_claim_id;
    RETURN NEXT;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.complete_work(
    p_project_id uuid,
    p_work_item_id uuid,
    p_claim_id uuid
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    UPDATE agentcore.work_claims
    SET status = 'released', released_at = now()
    WHERE id = p_claim_id
      AND work_item_id = p_work_item_id
      AND status = 'active';

    UPDATE agentcore.work_queue
    SET status = 'done'
    WHERE id = p_work_item_id
      AND project_id = p_project_id
      AND status = 'claimed';
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.create_capability_lease(
    p_project_id uuid,
    p_holder_identity_id uuid,
    p_tool_name text,
    p_step_id text,
    p_lease_seconds integer,
    p_justification text,
    p_permitted_operations text[] DEFAULT ARRAY[]::text[]
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    new_id uuid;
BEGIN
    PERFORM agentcore.assert_project_scope(p_project_id);

    INSERT INTO agentcore.capability_leases (
        project_id, holder_identity_id, tool_name, step_id, permitted_operations,
        justification, lease_expires_at
    )
    VALUES (
        p_project_id, p_holder_identity_id, p_tool_name, p_step_id,
        p_permitted_operations, p_justification, now() + make_interval(secs => p_lease_seconds)
    )
    RETURNING id INTO new_id;

    RETURN new_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.recover_expired_work()
RETURNS TABLE(recovered_pending integer, moved_to_dead integer, expired_leases integer)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    r record;
    pending_count integer := 0;
    dead_count integer := 0;
    lease_count integer := 0;
BEGIN
    UPDATE agentcore.work_claims
    SET status = 'expired', released_at = now()
    WHERE status = 'active' AND lease_expires_at <= now();

    FOR r IN
        SELECT q.*
        FROM agentcore.work_queue q
        WHERE q.status = 'claimed'
          AND NOT EXISTS (
              SELECT 1 FROM agentcore.work_claims c
              WHERE c.work_item_id = q.id AND c.status = 'active'
          )
        ORDER BY q.created_at
    LOOP
        IF r.attempts >= r.max_attempts THEN
            UPDATE agentcore.work_queue
            SET status = 'dead'
            WHERE id = r.id;

            INSERT INTO agentcore.dead_letters (work_item_id, reason, original_payload)
            VALUES (r.id, 'max_attempts_exceeded_after_expired_claim', r.payload)
            ON CONFLICT (work_item_id) DO NOTHING;

            dead_count := dead_count + 1;
        ELSE
            UPDATE agentcore.work_queue
            SET status = 'pending', available_at = now()
            WHERE id = r.id;
            pending_count := pending_count + 1;
        END IF;
    END LOOP;

    UPDATE agentcore.capability_leases
    SET status = 'expired'
    WHERE status = 'active' AND lease_expires_at <= now();

    GET DIAGNOSTICS lease_count = ROW_COUNT;

    recovered_pending := pending_count;
    moved_to_dead := dead_count;
    expired_leases := lease_count;
    RETURN NEXT;
END;
$$;

GRANT USAGE ON SCHEMA agentcore TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_admin, agentcore_backup, agentcore_cognee;

GRANT SELECT ON ALL TABLES IN SCHEMA agentcore TO agentcore_read, agentcore_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA agentcore TO agentcore_ingest, agentcore_worker;
GRANT INSERT ON agentcore.artifact_objects TO agentcore_ingest, agentcore_worker;
GRANT ALL ON ALL TABLES IN SCHEMA agentcore TO agentcore_admin;

GRANT EXECUTE ON FUNCTION agentcore.append_evidence_event(uuid, uuid, agentcore.event_kind, text, jsonb, uuid, agentcore.trust_class, jsonb) TO agentcore_ingest, agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.enqueue_work(uuid, text, text, jsonb, integer) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.claim_work(uuid, uuid, integer) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.complete_work(uuid, uuid, uuid) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.create_capability_lease(uuid, uuid, text, text, integer, text, text[]) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.recover_expired_work() TO agentcore_worker, agentcore_admin;

REVOKE UPDATE, DELETE ON ALL TABLES IN SCHEMA agentcore FROM agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup, agentcore_cognee;
REVOKE ALL ON agentcore.evidence_events FROM agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup, agentcore_cognee;
GRANT SELECT ON agentcore.evidence_events TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;

INSERT INTO agentcore.schema_migrations (version, description)
VALUES ('m2.001', 'canonical identity, immutable evidence, queue claim lease dead-letter primitives')
ON CONFLICT (version) DO NOTHING;

COMMIT;
