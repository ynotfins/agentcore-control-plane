-- 0004_down_agent_run_ledger_quality_scores.sql
-- Reverses 0004_up_agent_run_ledger_quality_scores.sql. Test in agent_core_restore_test first.
-- Drop quality_scores first (FKs to agent_run_ledger), then agent_run_ledger.

DROP INDEX IF EXISTS idx_aqs_retrieval_event;
DROP INDEX IF EXISTS idx_aqs_pack_id;
DROP TABLE IF EXISTS agent_quality_scores;

DROP INDEX IF EXISTS idx_arl_created_at;
DROP INDEX IF EXISTS idx_arl_agent_id;
DROP INDEX IF EXISTS idx_arl_project_id;
DROP TABLE IF EXISTS agent_run_ledger;
