-- M6 001 DOWN - Durable LangGraph Autonomous Workflow (rollback)
--
-- Authority: BLUEPRINT.md M6 rollback point.
-- Removes all M6 AgentCore wf_* tables and functions.
-- LangGraph internal checkpoint tables (checkpoints schema) are NOT touched.

BEGIN;

DROP FUNCTION IF EXISTS agentcore.check_wf_scope_drift(uuid, uuid, text, text);
DROP FUNCTION IF EXISTS agentcore.set_wf_scope_baseline(uuid, uuid, text, text);
DROP FUNCTION IF EXISTS agentcore.expire_wf_jit_leases(uuid);
DROP FUNCTION IF EXISTS agentcore.get_project_tools(uuid);
DROP FUNCTION IF EXISTS agentcore.set_capability_state(uuid, text, agentcore.wf_capability_state, text, text, boolean);
DROP FUNCTION IF EXISTS agentcore.resolve_wf_pause(uuid, uuid, agentcore.wf_pause_resolution, text, text);
DROP FUNCTION IF EXISTS agentcore.create_wf_pause(uuid, uuid, text, text, text, integer);
DROP FUNCTION IF EXISTS agentcore.record_wf_gate(uuid, uuid, text, text, agentcore.wf_gate_verdict, jsonb);
DROP FUNCTION IF EXISTS agentcore.register_wf_run(uuid, text, uuid);
DROP FUNCTION IF EXISTS agentcore.assert_run_project_scope(uuid, uuid);

DROP TABLE IF EXISTS agentcore.wf_scope_baselines CASCADE;
DROP TABLE IF EXISTS agentcore.wf_evidence CASCADE;
DROP TABLE IF EXISTS agentcore.wf_critic_runs CASCADE;
DROP TABLE IF EXISTS agentcore.wf_ab_experiments CASCADE;
DROP TABLE IF EXISTS agentcore.capability_profiles CASCADE;
DROP TABLE IF EXISTS agentcore.wf_human_pauses CASCADE;
DROP TABLE IF EXISTS agentcore.wf_gate_evals CASCADE;
DROP TABLE IF EXISTS agentcore.wf_checklist_items CASCADE;
DROP TABLE IF EXISTS agentcore.wf_micro_steps CASCADE;
DROP TABLE IF EXISTS agentcore.wf_macro_steps CASCADE;
DROP TABLE IF EXISTS agentcore.wf_milestones CASCADE;
DROP TABLE IF EXISTS agentcore.wf_charters CASCADE;
DROP TABLE IF EXISTS agentcore.wf_runs CASCADE;

DROP TYPE IF EXISTS agentcore.wf_judge_verdict;
DROP TYPE IF EXISTS agentcore.wf_ab_decision;
DROP TYPE IF EXISTS agentcore.wf_pause_resolution;
DROP TYPE IF EXISTS agentcore.wf_capability_state;
DROP TYPE IF EXISTS agentcore.wf_risk_class;
DROP TYPE IF EXISTS agentcore.wf_gate_verdict;
DROP TYPE IF EXISTS agentcore.wf_step_status;
DROP TYPE IF EXISTS agentcore.wf_run_status;

DELETE FROM agentcore.schema_migrations WHERE version = 'm6.001';

COMMIT;
