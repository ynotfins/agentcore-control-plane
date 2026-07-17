-- M8 002 UP — Client Memory Continuity View
--
-- Authority: BLUEPRINT.md §3/§6; task "harden continuous context durability" 2026-07-17.
-- Target: PostgreSQL 18 agent_core on 127.0.0.1:55433.
-- Scope: v_client_memory_continuity — per-client continuity status for the central audit.
--
-- This view provides one row per (client, agent, project) showing only non-secret fields:
--   client_key, agent_key, project_key, active session, last_session_open, last_append,
--   last_projection, last_handoff, last_close, continuity_status.
-- Used by: ops/Test-AgentCoreDurabilityAndPlacement.ps1 and the DurabilityResourceAudit task.
-- Never exposes raw credentials, foreign keys, or payload content.
--
-- Rollback: migrations/m8/002_down_client_memory_continuity_view.sql

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. v_client_memory_continuity — per-client/agent/project continuity snapshot
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW agentcore.v_client_memory_continuity AS
WITH latest_session AS (
  -- Most recent session per (client, agent, project) tuple
  SELECT DISTINCT ON (s.client_id, s.agent_id, s.project_id)
    s.id            AS session_id,
    s.client_id,
    s.agent_id,
    s.project_id,
    s.session_key,
    s.started_at,
    s.ended_at
  FROM agentcore.sessions s
  ORDER BY s.client_id, s.agent_id, s.project_id, s.started_at DESC
),
event_stats AS (
  -- Last event and last handoff event per session
  SELECT
    si.session_id,
    MAX(e.accepted_at)                                                         AS last_append,
    MAX(e.accepted_at) FILTER (WHERE e.event_kind = 'handoff')                 AS last_handoff
  FROM agentcore.evidence_events e
  JOIN agentcore.source_identities si ON si.id = e.source_identity_id
  GROUP BY si.session_id
),
latest_projection AS (
  -- Most recent is_current projection per project
  SELECT DISTINCT ON (pr.project_id)
    pr.project_id,
    pr.revision,
    pr.content_sha256    AS projection_hash,
    pr.generated_at      AS last_projection
  FROM agentcore.projection_revisions pr
  WHERE pr.is_current
  ORDER BY pr.project_id, pr.generated_at DESC
)
SELECT
  c.client_key,
  a.agent_key,
  p.project_key,
  ls.session_key,
  ls.started_at                           AS last_session_open,
  es.last_append,
  es.last_handoff,
  lp.last_projection,
  lp.revision                             AS projection_revision,
  lp.projection_hash,
  ls.ended_at                             AS last_close,
  CASE
    WHEN ls.ended_at IS NOT NULL
      AND es.last_handoff IS NULL
    THEN 'closed_no_handoff'
    WHEN ls.ended_at IS NOT NULL
    THEN 'closed'
    WHEN es.last_append IS NULL
    THEN 'open_no_events'
    WHEN es.last_append < now() - interval '6 hours'
    THEN 'stale'
    WHEN lp.last_projection IS NULL
      OR lp.last_projection < es.last_append - interval '2 hours'
    THEN 'projection_stale'
    ELSE 'healthy'
  END                                     AS continuity_status
FROM latest_session ls
JOIN agentcore.ide_clients c ON c.id = ls.client_id
JOIN agentcore.agents a       ON a.id = ls.agent_id
JOIN agentcore.projects p     ON p.id = ls.project_id
LEFT JOIN event_stats es      ON es.session_id = ls.session_id
LEFT JOIN latest_projection lp ON lp.project_id = ls.project_id;

COMMENT ON VIEW agentcore.v_client_memory_continuity IS
  'Per-client memory continuity snapshot (non-secret). One row per (client, agent, project) '
  'showing last session, last event, last projection, last handoff, and continuity status. '
  'Used by the central durability audit (ops/Test-AgentCoreDurabilityAndPlacement.ps1). '
  'PostgreSQL is canonical; projections are generated. Never stores credentials or raw payloads.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Grant read access to agentcore_worker role
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'agentcore_worker') THEN
    GRANT SELECT ON agentcore.v_client_memory_continuity TO agentcore_worker;
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Record migration
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO agentcore.schema_migrations (version, description, applied_at, applied_by, blueprint_level)
VALUES (
  'm8.002',
  'client memory continuity view: v_client_memory_continuity for central durability audit',
  now(), 'postgres', 'M8'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
