-- M5 001 DOWN — remove hybrid retrieval and curated Cognee metadata.
-- Rollback point: M4 PostgreSQL-only context assembly with Cognee disabled.

BEGIN;

DROP FUNCTION IF EXISTS agentcore.hybrid_retrieve_documents(uuid, text, vector, integer, text[], text[]);
DROP FUNCTION IF EXISTS agentcore.promote_curated_knowledge(
  uuid,
  agentcore.retrieval_scope,
  text,
  agentcore.trust_class,
  text,
  text,
  text,
  uuid[],
  jsonb,
  text
);

DROP TABLE IF EXISTS agentcore.curated_knowledge_promotions;
DROP TABLE IF EXISTS agentcore.retrieval_documents;
DROP TABLE IF EXISTS agentcore.retrieval_benchmarks;

DROP TYPE IF EXISTS agentcore.supersession_state;
DROP TYPE IF EXISTS agentcore.retrieval_scope;

DELETE FROM agentcore.schema_migrations WHERE version = 'm5.001';

COMMIT;
