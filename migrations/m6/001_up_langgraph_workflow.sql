-- M6 001 UP - Durable LangGraph Autonomous Workflow
--
-- Authority: BLUEPRINT.md M6 and docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md M6.
-- Target: PostgreSQL 18 agent_core on 127.0.0.1:55433.
-- Scope: LangGraph workflow run state (wf_runs), milestone/macro/micro/checklist persistence,
--        gate evaluations, human pause queue, capability profiles, A/B decisions,
--        critic/scorer/judge runs, scope baselines.
--
-- Tables use the wf_ prefix to avoid conflicts with M2 identity tables
-- (agentcore.workflows, agentcore.workflow_threads).
--
-- LangGraph internal checkpoint tables are created by langgraph-checkpoint-postgres
-- setup() in a separate schema; this migration owns only AgentCore metadata.

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- ENUMS
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace='agentcore'::regnamespace AND typname='wf_run_status') THEN
    CREATE TYPE agentcore.wf_run_status AS ENUM (
      'running', 'paused_human', 'paused_gate', 'completed', 'failed', 'aborted'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace='agentcore'::regnamespace AND typname='wf_step_status') THEN
    CREATE TYPE agentcore.wf_step_status AS ENUM (
      'pending', 'running', 'blocked_gate', 'paused_human', 'completed', 'skipped', 'failed'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace='agentcore'::regnamespace AND typname='wf_gate_verdict') THEN
    CREATE TYPE agentcore.wf_gate_verdict AS ENUM ('pass', 'fail', 'warn');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace='agentcore'::regnamespace AND typname='wf_risk_class') THEN
    CREATE TYPE agentcore.wf_risk_class AS ENUM ('low', 'medium', 'high', 'critical');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace='agentcore'::regnamespace AND typname='wf_capability_state') THEN
    CREATE TYPE agentcore.wf_capability_state AS ENUM (
      'catalogued', 'core_active', 'milestone_active', 'jit_leased', 'dormant', 'operator_only', 'forbidden'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace='agentcore'::regnamespace AND typname='wf_pause_resolution') THEN
    CREATE TYPE agentcore.wf_pause_resolution AS ENUM (
      'pending', 'approved', 'rejected', 'overridden', 'timeout'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace='agentcore'::regnamespace AND typname='wf_ab_decision') THEN
    CREATE TYPE agentcore.wf_ab_decision AS ENUM (
      'skipped_low_risk', 'enabled', 'completed_a_wins', 'completed_b_wins', 'completed_tie'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace='agentcore'::regnamespace AND typname='wf_judge_verdict') THEN
    CREATE TYPE agentcore.wf_judge_verdict AS ENUM ('proceed', 'needs_operator', 'block');
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_RUNS  (LangGraph thread ↔ AgentCore project; one row per workflow run)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_runs (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    langgraph_thread  text NOT NULL UNIQUE,      -- LangGraph thread_id string
    project_id        uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    session_id        uuid REFERENCES agentcore.sessions(id),
    status            agentcore.wf_run_status NOT NULL DEFAULT 'running',
    current_milestone text,
    current_macro     text,
    current_micro     text,
    ab_enabled        boolean NOT NULL DEFAULT false,
    started_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    completed_at      timestamptz,
    metadata          jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_wf_runs_project ON agentcore.wf_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_wf_runs_status  ON agentcore.wf_runs(status);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_CHARTERS  (locked goals and acceptance criteria per project)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_charters (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    version             integer NOT NULL DEFAULT 1,
    title               text NOT NULL,
    goal                text NOT NULL,
    locked_milestones   jsonb NOT NULL DEFAULT '[]'::jsonb,
    acceptance_criteria jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at          timestamptz NOT NULL DEFAULT now(),
    locked_at           timestamptz,
    locked_by           text,
    UNIQUE (project_id, version)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_MILESTONES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_milestones (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id             uuid NOT NULL REFERENCES agentcore.wf_runs(id) ON DELETE CASCADE,
    project_id         uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    milestone_key      text NOT NULL,
    label              text NOT NULL,
    status             agentcore.wf_step_status NOT NULL DEFAULT 'pending',
    entry_gates_passed jsonb NOT NULL DEFAULT '[]'::jsonb,
    exit_gates_passed  jsonb NOT NULL DEFAULT '[]'::jsonb,
    exit_criteria      jsonb NOT NULL DEFAULT '[]'::jsonb,
    evidence           jsonb NOT NULL DEFAULT '[]'::jsonb,
    started_at         timestamptz,
    completed_at       timestamptz,
    created_at         timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, milestone_key)
);

CREATE INDEX IF NOT EXISTS idx_wf_milestones_run     ON agentcore.wf_milestones(run_id);
CREATE INDEX IF NOT EXISTS idx_wf_milestones_project ON agentcore.wf_milestones(project_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_MACRO_STEPS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_macro_steps (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    milestone_id uuid NOT NULL REFERENCES agentcore.wf_milestones(id) ON DELETE CASCADE,
    project_id   uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    step_key     text NOT NULL,
    label        text NOT NULL,
    ordinal      integer NOT NULL,
    status       agentcore.wf_step_status NOT NULL DEFAULT 'pending',
    risk_class   agentcore.wf_risk_class NOT NULL DEFAULT 'low',
    gates_passed jsonb NOT NULL DEFAULT '[]'::jsonb,
    evidence     jsonb NOT NULL DEFAULT '[]'::jsonb,
    started_at   timestamptz,
    completed_at timestamptz,
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (milestone_id, step_key)
);

CREATE INDEX IF NOT EXISTS idx_wf_macro_milestone ON agentcore.wf_macro_steps(milestone_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_MICRO_STEPS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_micro_steps (
    id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    macro_id                    uuid NOT NULL REFERENCES agentcore.wf_macro_steps(id) ON DELETE CASCADE,
    project_id                  uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    step_key                    text NOT NULL,
    label                       text NOT NULL,
    ordinal                     integer NOT NULL,
    status                      agentcore.wf_step_status NOT NULL DEFAULT 'pending',
    risk_class                  agentcore.wf_risk_class NOT NULL DEFAULT 'low',
    deterministic_checks_passed boolean,
    score                       numeric,
    judge_verdict               agentcore.wf_judge_verdict,
    jit_lease_id                uuid REFERENCES agentcore.capability_leases(id),
    evidence                    jsonb NOT NULL DEFAULT '[]'::jsonb,
    started_at                  timestamptz,
    completed_at                timestamptz,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (macro_id, step_key)
);

CREATE INDEX IF NOT EXISTS idx_wf_micro_macro ON agentcore.wf_micro_steps(macro_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_CHECKLIST_ITEMS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_checklist_items (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    micro_id     uuid NOT NULL REFERENCES agentcore.wf_micro_steps(id) ON DELETE CASCADE,
    project_id   uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    item_key     text NOT NULL,
    label        text NOT NULL,
    ordinal      integer NOT NULL,
    status       text NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending','in_progress','completed','failed','skipped')),
    evidence     text,
    completed_at timestamptz,
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (micro_id, item_key)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_GATE_EVALS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_gate_evals (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id       uuid NOT NULL REFERENCES agentcore.wf_runs(id) ON DELETE CASCADE,
    project_id   uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    gate_name    text NOT NULL,
    scope_key    text NOT NULL,
    verdict      agentcore.wf_gate_verdict NOT NULL,
    details      jsonb NOT NULL DEFAULT '{}'::jsonb,
    evaluated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_wf_gate_evals_run     ON agentcore.wf_gate_evals(run_id, gate_name);
CREATE INDEX IF NOT EXISTS idx_wf_gate_evals_project ON agentcore.wf_gate_evals(project_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_HUMAN_PAUSES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_human_pauses (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id            uuid NOT NULL REFERENCES agentcore.wf_runs(id) ON DELETE CASCADE,
    project_id        uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    scope_key         text NOT NULL,
    question          text NOT NULL,
    context_summary   text,
    resolution        agentcore.wf_pause_resolution NOT NULL DEFAULT 'pending',
    operator_decision text,
    operator_notes    text,
    requested_at      timestamptz NOT NULL DEFAULT now(),
    resolved_at       timestamptz,
    timeout_at        timestamptz NOT NULL DEFAULT now() + interval '24 hours'
);

CREATE INDEX IF NOT EXISTS idx_wf_human_pauses_run     ON agentcore.wf_human_pauses(run_id);
CREATE INDEX IF NOT EXISTS idx_wf_human_pauses_pending ON agentcore.wf_human_pauses(resolution)
    WHERE resolution = 'pending';

-- ─────────────────────────────────────────────────────────────────────────────
-- CAPABILITY_PROFILES  (per-project tool state, PostgreSQL-backed per M6)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.capability_profiles (
    id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id                uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    tool_name                 text NOT NULL,
    tool_state                agentcore.wf_capability_state NOT NULL DEFAULT 'catalogued',
    milestone_key             text,
    activation_reason         text,
    requires_operator_approval boolean NOT NULL DEFAULT false,
    last_audited_at           timestamptz,
    updated_at                timestamptz NOT NULL DEFAULT now(),
    created_at                timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, tool_name)
);

CREATE INDEX IF NOT EXISTS idx_capability_profiles_project ON agentcore.capability_profiles(project_id);
CREATE INDEX IF NOT EXISTS idx_capability_profiles_state   ON agentcore.capability_profiles(project_id, tool_state);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_AB_EXPERIMENTS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_ab_experiments (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id            uuid NOT NULL REFERENCES agentcore.wf_runs(id) ON DELETE CASCADE,
    project_id        uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    scope_key         text NOT NULL,
    risk_class        agentcore.wf_risk_class NOT NULL,
    uncertainty_score numeric NOT NULL DEFAULT 0,
    decision          agentcore.wf_ab_decision NOT NULL DEFAULT 'skipped_low_risk',
    justification     text,
    branch_a_result   jsonb,
    branch_b_result   jsonb,
    winner            text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    resolved_at       timestamptz
);

CREATE INDEX IF NOT EXISTS idx_wf_ab_experiments_run ON agentcore.wf_ab_experiments(run_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_CRITIC_RUNS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_critic_runs (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id         uuid NOT NULL REFERENCES agentcore.wf_runs(id) ON DELETE CASCADE,
    project_id     uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    scope_key      text NOT NULL,
    run_kind       text NOT NULL CHECK (run_kind IN ('deterministic_check','critic','scorer','judge')),
    risk_class     agentcore.wf_risk_class,
    input_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    result         jsonb NOT NULL DEFAULT '{}'::jsonb,
    passed         boolean,
    score          numeric,
    verdict        agentcore.wf_judge_verdict,
    ran_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_wf_critic_runs_run ON agentcore.wf_critic_runs(run_id, run_kind);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_EVIDENCE
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_evidence (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id        uuid NOT NULL REFERENCES agentcore.wf_runs(id) ON DELETE CASCADE,
    project_id    uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    scope_key     text NOT NULL,
    evidence_type text NOT NULL,
    summary       text NOT NULL,
    detail        jsonb NOT NULL DEFAULT '{}'::jsonb,
    trust_class   agentcore.trust_class NOT NULL DEFAULT 'system_verified',
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_wf_evidence_run ON agentcore.wf_evidence(run_id, scope_key);

-- ─────────────────────────────────────────────────────────────────────────────
-- WF_SCOPE_BASELINES  (hash of content at milestone start for drift detection)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agentcore.wf_scope_baselines (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id           uuid NOT NULL REFERENCES agentcore.wf_runs(id) ON DELETE CASCADE,
    project_id       uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    scope_aspect     text NOT NULL,
    baseline_hash    text NOT NULL,
    baseline_content text NOT NULL,
    recorded_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, scope_aspect)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- HELPER FUNCTIONS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION agentcore.assert_run_project_scope(p_run_id uuid, p_project_id uuid)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = agentcore, public
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM agentcore.wf_runs
        WHERE id = p_run_id AND project_id = p_project_id
    ) THEN
        RAISE EXCEPTION 'Run % does not belong to project % (isolation violation)', p_run_id, p_project_id;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.register_wf_run(
    p_project_id      uuid,
    p_langgraph_thread text,
    p_session_id      uuid DEFAULT NULL
)
RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path = agentcore, public
AS $$
DECLARE new_id uuid;
BEGIN
    INSERT INTO agentcore.wf_runs (project_id, langgraph_thread, session_id)
    VALUES (p_project_id, p_langgraph_thread, p_session_id)
    ON CONFLICT (langgraph_thread) DO UPDATE SET updated_at = now()
    RETURNING id INTO new_id;
    RETURN new_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.record_wf_gate(
    p_run_id     uuid,
    p_project_id uuid,
    p_gate_name  text,
    p_scope_key  text,
    p_verdict    agentcore.wf_gate_verdict,
    p_details    jsonb DEFAULT '{}'::jsonb
)
RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path = agentcore, public
AS $$
DECLARE new_id uuid;
BEGIN
    PERFORM agentcore.assert_run_project_scope(p_run_id, p_project_id);
    INSERT INTO agentcore.wf_gate_evals (run_id, project_id, gate_name, scope_key, verdict, details)
    VALUES (p_run_id, p_project_id, p_gate_name, p_scope_key, p_verdict, p_details)
    RETURNING id INTO new_id;
    RETURN new_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.create_wf_pause(
    p_run_id          uuid,
    p_project_id      uuid,
    p_scope_key       text,
    p_question        text,
    p_context_summary text DEFAULT NULL,
    p_timeout_hours   integer DEFAULT 24
)
RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path = agentcore, public
AS $$
DECLARE new_id uuid;
BEGIN
    PERFORM agentcore.assert_run_project_scope(p_run_id, p_project_id);
    INSERT INTO agentcore.wf_human_pauses (run_id, project_id, scope_key, question, context_summary, timeout_at)
    VALUES (p_run_id, p_project_id, p_scope_key, p_question, p_context_summary,
            now() + make_interval(hours => p_timeout_hours))
    RETURNING id INTO new_id;
    UPDATE agentcore.wf_runs SET status = 'paused_human', updated_at = now() WHERE id = p_run_id;
    RETURN new_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.resolve_wf_pause(
    p_pause_id         uuid,
    p_project_id       uuid,
    p_resolution       agentcore.wf_pause_resolution,
    p_operator_decision text,
    p_operator_notes   text DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = agentcore, public
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM agentcore.wf_human_pauses
        WHERE id = p_pause_id AND project_id = p_project_id AND resolution = 'pending'
    ) THEN
        RAISE EXCEPTION 'Pause % not found or already resolved', p_pause_id;
    END IF;
    UPDATE agentcore.wf_human_pauses
    SET resolution = p_resolution, operator_decision = p_operator_decision,
        operator_notes = p_operator_notes, resolved_at = now()
    WHERE id = p_pause_id;
    UPDATE agentcore.wf_runs wf
    SET status = 'running', updated_at = now()
    FROM agentcore.wf_human_pauses hp
    WHERE hp.id = p_pause_id AND wf.id = hp.run_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.set_capability_state(
    p_project_id               uuid,
    p_tool_name                text,
    p_state                    agentcore.wf_capability_state,
    p_milestone_key            text DEFAULT NULL,
    p_reason                   text DEFAULT NULL,
    p_requires_operator_approval boolean DEFAULT false
)
RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path = agentcore, public
AS $$
DECLARE profile_id uuid;
BEGIN
    INSERT INTO agentcore.capability_profiles
        (project_id, tool_name, tool_state, milestone_key, activation_reason,
         requires_operator_approval, last_audited_at, updated_at)
    VALUES
        (p_project_id, p_tool_name, p_state, p_milestone_key, p_reason,
         p_requires_operator_approval, now(), now())
    ON CONFLICT (project_id, tool_name) DO UPDATE
        SET tool_state = EXCLUDED.tool_state, milestone_key = EXCLUDED.milestone_key,
            activation_reason = EXCLUDED.activation_reason,
            requires_operator_approval = EXCLUDED.requires_operator_approval,
            last_audited_at = now(), updated_at = now()
    RETURNING id INTO profile_id;
    RETURN profile_id;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.get_project_tools(p_project_id uuid)
RETURNS TABLE(tool_name text, tool_state agentcore.wf_capability_state, requires_operator_approval boolean)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = agentcore, public
AS $$
    SELECT cp.tool_name, cp.tool_state, cp.requires_operator_approval
    FROM agentcore.capability_profiles cp
    WHERE cp.project_id = p_project_id
      AND cp.tool_state NOT IN ('catalogued', 'dormant', 'forbidden')
    ORDER BY cp.tool_name;
$$;

CREATE OR REPLACE FUNCTION agentcore.expire_wf_jit_leases(p_project_id uuid)
RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path = agentcore, public
AS $$
DECLARE expired_count integer := 0;
BEGIN
    UPDATE agentcore.capability_leases
    SET status = 'expired'
    WHERE project_id = p_project_id AND status = 'active' AND lease_expires_at <= now();
    GET DIAGNOSTICS expired_count = ROW_COUNT;

    UPDATE agentcore.capability_profiles cp
    SET tool_state = 'dormant', updated_at = now()
    FROM agentcore.capability_leases cl
    WHERE cl.project_id = p_project_id AND cl.status = 'expired'
      AND cp.project_id = p_project_id AND cp.tool_name = cl.tool_name
      AND cp.tool_state = 'jit_leased';

    RETURN expired_count;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.set_wf_scope_baseline(
    p_run_id     uuid,
    p_project_id uuid,
    p_scope_aspect text,
    p_content    text
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = agentcore, public
AS $$
BEGIN
    PERFORM agentcore.assert_run_project_scope(p_run_id, p_project_id);
    INSERT INTO agentcore.wf_scope_baselines
        (run_id, project_id, scope_aspect, baseline_hash, baseline_content)
    VALUES
        (p_run_id, p_project_id, p_scope_aspect,
         encode(sha256(p_content::bytea), 'hex'), p_content)
    ON CONFLICT (run_id, scope_aspect) DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION agentcore.check_wf_scope_drift(
    p_run_id       uuid,
    p_project_id   uuid,
    p_scope_aspect text,
    p_current      text
)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = agentcore, public
AS $$
    SELECT CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM agentcore.wf_scope_baselines
            WHERE run_id = p_run_id AND scope_aspect = p_scope_aspect
        ) THEN false
        ELSE (
            SELECT baseline_hash != encode(sha256(p_current::bytea), 'hex')
            FROM agentcore.wf_scope_baselines
            WHERE run_id = p_run_id AND scope_aspect = p_scope_aspect
        )
    END;
$$;

-- ─────────────────────────────────────────────────────────────────────────────
-- GRANTS
-- ─────────────────────────────────────────────────────────────────────────────

GRANT SELECT ON agentcore.wf_runs TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_charters TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_milestones TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_macro_steps TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_micro_steps TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_checklist_items TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_gate_evals TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_human_pauses TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.capability_profiles TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_ab_experiments TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_critic_runs TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_evidence TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.wf_scope_baselines TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;

GRANT INSERT, UPDATE ON agentcore.wf_runs TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.wf_charters TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.wf_milestones TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.wf_macro_steps TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.wf_micro_steps TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.wf_checklist_items TO agentcore_worker, agentcore_admin;
GRANT INSERT ON agentcore.wf_gate_evals TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.wf_human_pauses TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.capability_profiles TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.wf_ab_experiments TO agentcore_worker, agentcore_admin;
GRANT INSERT ON agentcore.wf_critic_runs TO agentcore_worker, agentcore_admin;
GRANT INSERT ON agentcore.wf_evidence TO agentcore_worker, agentcore_admin;
GRANT INSERT ON agentcore.wf_scope_baselines TO agentcore_worker, agentcore_admin;
GRANT ALL ON ALL TABLES IN SCHEMA agentcore TO agentcore_admin;

GRANT EXECUTE ON FUNCTION agentcore.assert_run_project_scope(uuid, uuid) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.register_wf_run(uuid, text, uuid) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.record_wf_gate(uuid, uuid, text, text, agentcore.wf_gate_verdict, jsonb) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.create_wf_pause(uuid, uuid, text, text, text, integer) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.resolve_wf_pause(uuid, uuid, agentcore.wf_pause_resolution, text, text) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.set_capability_state(uuid, text, agentcore.wf_capability_state, text, text, boolean) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.get_project_tools(uuid) TO agentcore_read, agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.expire_wf_jit_leases(uuid) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.set_wf_scope_baseline(uuid, uuid, text, text) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.check_wf_scope_drift(uuid, uuid, text, text) TO agentcore_read, agentcore_worker, agentcore_admin;

INSERT INTO agentcore.schema_migrations (version, description, blueprint_level)
VALUES ('m6.001', 'wf_runs, wf_milestones, wf_macros, wf_micros, wf_checklists, wf_gates, wf_pauses, capability_profiles, wf_ab, wf_critics, wf_evidence, wf_scope_baselines', 'M6')
ON CONFLICT (version) DO NOTHING;

COMMIT;
