-- 0001_down_memory_source_systems.sql
-- Reverses 0001_up_memory_source_systems.sql. Test in agent_core_restore_test before applying up to production.
-- NOTE: memory_catalog (0002) has a FK to memory_source_systems(slug); drop 0002 before 0001.

DROP INDEX IF EXISTS idx_mss_slug;
DROP TABLE IF EXISTS memory_source_systems;
