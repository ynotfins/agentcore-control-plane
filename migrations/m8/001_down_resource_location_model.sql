-- M8 001 DOWN - Rollback Canonical Project Resource-Location Model
--
-- Reverses migrations/m8/001_up_resource_location_model.sql.
-- Note: Enum values added to agentcore.storage_tier cannot be removed in PostgreSQL;
--       backup_g, canonical_d, scratch_i remain but cause no issues when unused.

BEGIN;

-- Drop views
DROP VIEW IF EXISTS agentcore.v_project_storage_tiers;
DROP VIEW IF EXISTS agentcore.v_active_worktrees;
DROP VIEW IF EXISTS agentcore.v_project_resource_map;

-- Remove columns from worktrees
ALTER TABLE agentcore.worktrees
  DROP COLUMN IF EXISTS retired_at,
  DROP COLUMN IF EXISTS worktree_kind,
  DROP COLUMN IF EXISTS worktree_status;

-- Remove columns from artifact_locations (drop self-referential FK last)
ALTER TABLE agentcore.artifact_locations
  DROP COLUMN IF EXISTS backup_coverage,
  DROP COLUMN IF EXISTS superseded_by_id,
  DROP COLUMN IF EXISTS restore_instructions,
  DROP COLUMN IF EXISTS retention_class,
  DROP COLUMN IF EXISTS classification,
  DROP COLUMN IF EXISTS resource_kind,
  DROP COLUMN IF EXISTS last_verified_at;

-- Remove migration record
DELETE FROM agentcore.schema_migrations WHERE version = 'm8.001';

COMMIT;
