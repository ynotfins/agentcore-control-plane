-- 0003_down_retrieval_events_context_packs.sql
-- Reverses 0003_up_retrieval_events_context_packs.sql. Test in agent_core_restore_test first.
-- NOTE: agent_quality_scores (0004) FKs context_packs + memory_retrieval_events; drop 0004 before 0003.
-- Drop in reverse FK dependency order.

DROP INDEX IF EXISTS idx_cpi_catalog_id;
DROP INDEX IF EXISTS idx_cpi_pack_id;
DROP TABLE IF EXISTS context_pack_items;

DROP INDEX IF EXISTS idx_mre_created_at;
DROP INDEX IF EXISTS idx_mre_run_id;
DROP INDEX IF EXISTS idx_mre_agent_id;
DROP INDEX IF EXISTS idx_mre_project_id;
DROP TABLE IF EXISTS memory_retrieval_events;

DROP INDEX IF EXISTS idx_cp_created_at;
DROP INDEX IF EXISTS idx_cp_project_id;
DROP TABLE IF EXISTS context_packs;
