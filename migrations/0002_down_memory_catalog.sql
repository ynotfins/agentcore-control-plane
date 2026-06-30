-- 0002_down_memory_catalog.sql
-- Reverses 0002_up_memory_catalog.sql. Test in agent_core_restore_test first.
-- NOTE: context_pack_items (0003) has a FK to memory_catalog(id); drop 0003 before 0002.

DROP INDEX IF EXISTS idx_mc_embedding;
DROP INDEX IF EXISTS idx_mc_created_at;
DROP INDEX IF EXISTS idx_mc_privacy_zone;
DROP INDEX IF EXISTS idx_mc_memory_type;
DROP INDEX IF EXISTS idx_mc_source_system;
DROP INDEX IF EXISTS idx_mc_project_id;
DROP TABLE IF EXISTS memory_catalog;
