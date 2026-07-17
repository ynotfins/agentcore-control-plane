-- M3 001 DOWN — Lossless Context and STATE Projections
--
-- Removes M3 objects while preserving M2 identity/evidence primitives.
-- Explicit operator approval required before live rollback.

BEGIN;

DROP FUNCTION IF EXISTS agentcore.record_projection_revision(uuid, agentcore.projection_kind, text, text, text);
DROP FUNCTION IF EXISTS agentcore.assemble_context_window(uuid, text);
DROP FUNCTION IF EXISTS agentcore.propose_fact_review(uuid, text, jsonb, uuid, agentcore.trust_class, jsonb);
DROP FUNCTION IF EXISTS agentcore.register_artifact_location(uuid, uuid, agentcore.storage_tier, text, text);
DROP FUNCTION IF EXISTS agentcore.mark_event_duplicate(uuid, uuid, uuid, text);
DROP FUNCTION IF EXISTS agentcore.expand_summary(uuid);
DROP FUNCTION IF EXISTS agentcore.create_context_summary(uuid, uuid, agentcore.context_level, agentcore.context_bucket, text, text, integer, numeric, uuid[], uuid, text);
DROP FUNCTION IF EXISTS agentcore.recover_interrupted_compactions();
DROP FUNCTION IF EXISTS agentcore.complete_compaction_run(uuid, uuid, text);
DROP FUNCTION IF EXISTS agentcore.start_compaction_run(uuid, uuid, agentcore.context_level, agentcore.context_level, text, text, text);
DROP FUNCTION IF EXISTS agentcore.sha256_text(text);

DROP TABLE IF EXISTS agentcore.projection_revisions;
DROP TABLE IF EXISTS agentcore.fact_proposals;
DROP TABLE IF EXISTS agentcore.model_context_budgets;
DROP TABLE IF EXISTS agentcore.artifact_locations;
DROP TABLE IF EXISTS agentcore.event_dedupe_links;
DROP TABLE IF EXISTS agentcore.context_source_edges;
DROP TABLE IF EXISTS agentcore.context_summaries;
DROP TABLE IF EXISTS agentcore.compaction_runs;

DELETE FROM agentcore.schema_migrations WHERE version = 'm3.001';

DROP TYPE IF EXISTS agentcore.storage_tier;
DROP TYPE IF EXISTS agentcore.proposal_status;
DROP TYPE IF EXISTS agentcore.projection_kind;
DROP TYPE IF EXISTS agentcore.compaction_status;
DROP TYPE IF EXISTS agentcore.context_bucket;
DROP TYPE IF EXISTS agentcore.context_level;

COMMIT;
