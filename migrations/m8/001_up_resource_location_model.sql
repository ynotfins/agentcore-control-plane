-- M8 001 UP - Canonical Project Resource-Location Model
--
-- Authority: BLUEPRINT.md §3 and user task 2026-07-17 consolidation.
-- Target: PostgreSQL 18 agent_core on 127.0.0.1:55433.
-- Scope: Extend artifact_locations and worktrees to carry full location metadata;
--        add storage_tier values for backup (G:) and canonical repo (D:);
--        create views for project resource-location map and active-worktree queries.
--
-- Every durable project resource must carry:
--   project identity, resource kind, canonical path/URI, storage tier,
--   classification (canonical/derived/cache/backup), authority class,
--   retention class, content hash, source event, backup coverage,
--   created/last-verified timestamps, superseded location, restore instructions.
--
-- Rollback: migrations/m8/001_down_resource_location_model.sql

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Extend storage_tier enum with backup_g (G: drive) and canonical_d (D: repos)
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_enum e
    JOIN pg_type t ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'agentcore' AND t.typname = 'storage_tier' AND e.enumlabel = 'backup_g'
  ) THEN
    ALTER TYPE agentcore.storage_tier ADD VALUE 'backup_g';  -- G: backup tier
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_enum e
    JOIN pg_type t ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'agentcore' AND t.typname = 'storage_tier' AND e.enumlabel = 'canonical_d'
  ) THEN
    ALTER TYPE agentcore.storage_tier ADD VALUE 'canonical_d';  -- D: canonical repo tier
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_enum e
    JOIN pg_type t ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'agentcore' AND t.typname = 'storage_tier' AND e.enumlabel = 'scratch_i'
  ) THEN
    ALTER TYPE agentcore.storage_tier ADD VALUE 'scratch_i';  -- I: temporary scratch tier
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Extend artifact_locations with full location metadata
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE agentcore.artifact_locations
  ADD COLUMN IF NOT EXISTS last_verified_at    timestamptz,
  ADD COLUMN IF NOT EXISTS resource_kind       text,           -- 'source','binary','snapshot','backup','evidence','report'
  ADD COLUMN IF NOT EXISTS classification      text            -- 'canonical','derived','cache','backup'
    CHECK (classification IN ('canonical','derived','cache','backup') OR classification IS NULL),
  ADD COLUMN IF NOT EXISTS retention_class     text            -- 'permanent','milestone','session','temporary'
    CHECK (retention_class IN ('permanent','milestone','session','temporary') OR retention_class IS NULL),
  ADD COLUMN IF NOT EXISTS restore_instructions text,
  ADD COLUMN IF NOT EXISTS superseded_by_id   uuid            -- FK to artifact_locations.id (self-ref)
    REFERENCES agentcore.artifact_locations(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS backup_coverage     boolean;       -- true = this location has a backup

COMMENT ON COLUMN agentcore.artifact_locations.last_verified_at IS
  'Last time this path/URI was confirmed to exist and hash-match.';
COMMENT ON COLUMN agentcore.artifact_locations.resource_kind IS
  'Semantic kind: source, binary, snapshot, backup, evidence, report, projection.';
COMMENT ON COLUMN agentcore.artifact_locations.classification IS
  'canonical=authoritative original; derived=generated from source; cache=reconstructable; backup=copy for recovery.';
COMMENT ON COLUMN agentcore.artifact_locations.retention_class IS
  'permanent=keep forever; milestone=keep until superseded+2 milestones; session=current session only; temporary=delete at task close.';
COMMENT ON COLUMN agentcore.artifact_locations.restore_instructions IS
  'Human-readable or machine-parseable instructions to restore this artifact from its backup or source.';
COMMENT ON COLUMN agentcore.artifact_locations.superseded_by_id IS
  'Points to the replacement artifact_locations row when this location has been superseded.';
COMMENT ON COLUMN agentcore.artifact_locations.backup_coverage IS
  'True if a verified backup copy exists for this location (on backup_g tier or equivalent).';

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Extend worktrees with status, kind, and retirement timestamp
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE agentcore.worktrees
  ADD COLUMN IF NOT EXISTS worktree_status text NOT NULL DEFAULT 'active'
    CHECK (worktree_status IN ('active','retired','temporary')),
  ADD COLUMN IF NOT EXISTS worktree_kind   text NOT NULL DEFAULT 'feature'
    CHECK (worktree_kind IN ('primary','feature','ai','temporary','shared')),
  ADD COLUMN IF NOT EXISTS retired_at      timestamptz;

COMMENT ON COLUMN agentcore.worktrees.worktree_status IS
  'active=in use; retired=removed (path may no longer exist); temporary=ephemeral scratch.';
COMMENT ON COLUMN agentcore.worktrees.worktree_kind IS
  'primary=main checkout; feature=task branch; ai=AI-managed; temporary=ephemeral; shared=multi-agent.';
COMMENT ON COLUMN agentcore.worktrees.retired_at IS
  'Timestamp when this worktree was removed. NULL means still active.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Views for resource-location map queries
-- ─────────────────────────────────────────────────────────────────────────────

-- v_project_resource_map: canonical cross-table location view
CREATE OR REPLACE VIEW agentcore.v_project_resource_map AS
SELECT
  p.id                        AS project_id,
  p.project_key,
  p.project_name,
  r.id                        AS repository_id,
  r.repo_key,
  r.canonical_path            AS canonical_source_path,
  r.remote_url,
  w.id                        AS worktree_id,
  w.worktree_path,
  w.branch_name               AS worktree_branch,
  w.head_commit               AS worktree_commit,
  w.worktree_status,
  w.worktree_kind,
  w.retired_at,
  pw.is_primary               AS is_primary_worktree,
  al.id                       AS artifact_location_id,
  ao.id                       AS artifact_id,
  ao.sha256                   AS content_hash,
  al.storage_tier,
  al.storage_uri              AS artifact_path,
  al.resource_kind,
  al.classification,
  al.retention_class,
  al.is_active                AS location_is_active,
  al.backup_coverage,
  al.last_verified_at,
  al.restore_instructions,
  al.superseded_by_id,
  al.created_at               AS location_created_at
FROM agentcore.projects p
JOIN agentcore.repositories r       ON r.id = p.repository_id
LEFT JOIN agentcore.project_worktrees pw ON pw.project_id = p.id
LEFT JOIN agentcore.worktrees w      ON w.id = pw.worktree_id
LEFT JOIN agentcore.artifact_objects ao ON ao.project_id = p.id
LEFT JOIN agentcore.artifact_locations al ON al.artifact_id = ao.id;

COMMENT ON VIEW agentcore.v_project_resource_map IS
  'Canonical location map: answers where any project resource lives, its storage tier, backup status, and restore path. '
  'PostgreSQL is canonical; agents read via retrieve_context / build_handoff, never raw SQL.';

-- v_active_worktrees: quick lookup of non-retired worktrees per project
CREATE OR REPLACE VIEW agentcore.v_active_worktrees AS
SELECT
  p.id             AS project_id,
  p.project_key,
  p.project_name,
  w.id             AS worktree_id,
  w.worktree_path,
  w.branch_name,
  w.head_commit,
  w.worktree_status,
  w.worktree_kind,
  pw.is_primary
FROM agentcore.worktrees w
JOIN agentcore.project_worktrees pw ON pw.worktree_id = w.id
JOIN agentcore.projects p           ON p.id = pw.project_id
WHERE w.worktree_status = 'active';

COMMENT ON VIEW agentcore.v_active_worktrees IS
  'Active (non-retired) worktrees per project. Retired worktrees remain in agentcore.worktrees for audit.';

-- v_project_storage_tiers: storage tier summary per project
CREATE OR REPLACE VIEW agentcore.v_project_storage_tiers AS
SELECT
  p.id             AS project_id,
  p.project_key,
  al.storage_tier,
  al.classification,
  al.retention_class,
  COUNT(*)         AS location_count,
  SUM(ao.bytes)    AS total_bytes,
  MAX(al.last_verified_at) AS last_verified_at,
  BOOL_OR(al.backup_coverage) AS any_backup_coverage
FROM agentcore.projects p
JOIN agentcore.artifact_objects ao  ON ao.project_id = p.id
JOIN agentcore.artifact_locations al ON al.artifact_id = ao.id
WHERE al.is_active
GROUP BY p.id, p.project_key, al.storage_tier, al.classification, al.retention_class;

COMMENT ON VIEW agentcore.v_project_storage_tiers IS
  'Storage tier summary per project: how much is hot (H:), cold (E:), backup (G:), canonical (D:).';

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. Grant read access to views for agentcore_worker role
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'agentcore_worker') THEN
    GRANT SELECT ON agentcore.v_project_resource_map   TO agentcore_worker;
    GRANT SELECT ON agentcore.v_active_worktrees       TO agentcore_worker;
    GRANT SELECT ON agentcore.v_project_storage_tiers  TO agentcore_worker;
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. Record migration in schema_migrations
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO agentcore.schema_migrations (version, description, applied_at, applied_by, blueprint_level)
VALUES ('m8.001', 'canonical project resource-location model: storage tiers, artifact metadata, worktree status, location map views', now(), 'postgres', 'M8')
ON CONFLICT (version) DO NOTHING;

COMMIT;
