-- M5 002 DOWN — reverse knowledge corpus additive changes
-- HARD GATE: only on restore-test / with explicit operator AUTH.

BEGIN;

DROP FUNCTION IF EXISTS agentcore.hybrid_retrieve_documents(uuid, text, vector, integer, text[], text[], jsonb);

-- Restore prior 6-arg overload from m5.001 semantics (no metadata filter, no chunk_id in source_ref).
-- Operators should re-apply m5.001 function body from 001_up if a full restore is required.
-- Minimal restore: recreate without p_metadata_filter / chunk_id extras.

CREATE OR REPLACE FUNCTION agentcore.hybrid_retrieve_documents(
    p_project_id uuid,
    p_query text,
    p_query_embedding vector DEFAULT NULL,
    p_limit integer DEFAULT 5,
    p_trust_classes text[] DEFAULT NULL,
    p_methods text[] DEFAULT NULL
)
RETURNS TABLE(
    source text,
    id text,
    title text,
    text text,
    source_ref jsonb,
    trust_class text,
    version text,
    scope text,
    retrieval_method text,
    score numeric,
    provenance jsonb,
    metadata jsonb
)
LANGUAGE sql
STABLE
AS $$
WITH params AS (
  SELECT
    nullif(trim(coalesce(p_query, '')), '') AS query_text,
    websearch_to_tsquery('english', coalesce(p_query, '')) AS tsq,
    greatest(coalesce(p_limit, 5), 1) AS limit_n
),
eligible AS (
  SELECT d.*
  FROM agentcore.retrieval_documents d
  WHERE (d.project_id = p_project_id OR d.scope = 'global')
    AND d.trust_class NOT IN ('quarantined', 'rejected')
    AND (p_trust_classes IS NULL OR d.trust_class::text = ANY(p_trust_classes))
),
fts AS (
  SELECT
    'retrieval_document'::text AS source,
    e.id::text,
    e.title,
    e.body AS text,
    jsonb_build_object(
      'retrieval_document_id', e.id,
      'source_uri', e.source_uri,
      'source_path', e.source_path,
      'source_kind', e.source_kind,
      'source_evidence_ids', e.source_evidence_ids
    ) AS source_ref,
    e.trust_class::text,
    e.version,
    e.scope::text,
    'postgres_fts'::text AS retrieval_method,
    ts_rank_cd(e.search_tsv, params.tsq)::numeric AS score,
    e.provenance,
    e.metadata
  FROM eligible e, params
  WHERE params.query_text IS NOT NULL
    AND (p_methods IS NULL OR 'postgres_fts' = ANY(p_methods))
    AND e.search_tsv @@ params.tsq
),
trgm AS (
  SELECT
    'retrieval_document'::text AS source,
    e.id::text,
    e.title,
    e.body AS text,
    jsonb_build_object(
      'retrieval_document_id', e.id,
      'source_uri', e.source_uri,
      'source_path', e.source_path,
      'source_kind', e.source_kind,
      'source_evidence_ids', e.source_evidence_ids
    ) AS source_ref,
    e.trust_class::text,
    e.version,
    e.scope::text,
    'postgres_trigram'::text AS retrieval_method,
    greatest(similarity(e.title, params.query_text), similarity(e.body, params.query_text))::numeric AS score,
    e.provenance,
    e.metadata
  FROM eligible e, params
  WHERE params.query_text IS NOT NULL
    AND (p_methods IS NULL OR 'postgres_trigram' = ANY(p_methods))
    AND greatest(similarity(e.title, params.query_text), similarity(e.body, params.query_text)) > 0.08
),
vec AS (
  SELECT
    'retrieval_document'::text AS source,
    e.id::text,
    e.title,
    e.body AS text,
    jsonb_build_object(
      'retrieval_document_id', e.id,
      'source_uri', e.source_uri,
      'source_path', e.source_path,
      'source_kind', e.source_kind,
      'source_evidence_ids', e.source_evidence_ids
    ) AS source_ref,
    e.trust_class::text,
    e.version,
    e.scope::text,
    CASE WHEN e.source_kind = 'curated_cognee_knowledge' THEN 'cognee_curated' ELSE 'pgvector_exact' END AS retrieval_method,
    (1.0 - (e.embedding <=> p_query_embedding))::numeric AS score,
    e.provenance,
    e.metadata
  FROM eligible e
  WHERE p_query_embedding IS NOT NULL
    AND e.embedding IS NOT NULL
    AND (
      p_methods IS NULL
      OR 'pgvector_exact' = ANY(p_methods)
      OR (e.source_kind = 'curated_cognee_knowledge' AND 'cognee_curated' = ANY(p_methods))
    )
),
curated_text AS (
  SELECT
    'curated_knowledge'::text AS source,
    e.id::text,
    e.title,
    e.body AS text,
    jsonb_build_object(
      'retrieval_document_id', e.id,
      'promotion_id', e.metadata->>'promotion_id',
      'source_uri', e.source_uri,
      'source_kind', e.source_kind,
      'source_evidence_ids', e.source_evidence_ids
    ) AS source_ref,
    e.trust_class::text,
    e.version,
    e.scope::text,
    'cognee_curated'::text AS retrieval_method,
    greatest(similarity(e.title, params.query_text), similarity(e.body, params.query_text))::numeric AS score,
    e.provenance,
    e.metadata
  FROM eligible e, params
  WHERE params.query_text IS NOT NULL
    AND e.source_kind = 'curated_cognee_knowledge'
    AND (p_methods IS NULL OR 'cognee_curated' = ANY(p_methods))
    AND (
      e.search_tsv @@ params.tsq
      OR greatest(similarity(e.title, params.query_text), similarity(e.body, params.query_text)) > 0.08
    )
),
combined AS (
  SELECT * FROM fts
  UNION ALL SELECT * FROM trgm
  UNION ALL SELECT * FROM vec
  UNION ALL SELECT * FROM curated_text
),
deduped AS (
  SELECT DISTINCT ON (id, retrieval_method) *
  FROM combined
  ORDER BY id, retrieval_method, score DESC
)
SELECT
  source, id, title, text, source_ref, trust_class, version, scope,
  retrieval_method, score, provenance, metadata
FROM deduped, params
ORDER BY
  CASE retrieval_method
    WHEN 'cognee_curated' THEN 0
    WHEN 'pgvector_exact' THEN 1
    WHEN 'postgres_fts' THEN 2
    WHEN 'postgres_trigram' THEN 3
    ELSE 9
  END,
  score DESC,
  title
LIMIT (SELECT limit_n FROM params)
$$;

GRANT EXECUTE ON FUNCTION agentcore.hybrid_retrieve_documents(uuid, text, vector, integer, text[], text[])
  TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_admin;

DROP INDEX IF EXISTS agentcore.idx_retrieval_documents_metadata_gin;
DROP INDEX IF EXISTS agentcore.idx_retrieval_documents_meta_license;
DROP INDEX IF EXISTS agentcore.idx_retrieval_documents_meta_language;
DROP INDEX IF EXISTS agentcore.idx_retrieval_documents_meta_framework;
DROP INDEX IF EXISTS agentcore.idx_retrieval_documents_meta_asset_type;
DROP INDEX IF EXISTS agentcore.uq_retrieval_documents_source_version_chunk;

ALTER TABLE agentcore.retrieval_documents
  DROP CONSTRAINT IF EXISTS retrieval_documents_source_kind_check;

ALTER TABLE agentcore.retrieval_documents
  ADD CONSTRAINT retrieval_documents_source_kind_check
  CHECK (source_kind IN (
    'accepted_evidence',
    'official_document',
    'curated_cognee_knowledge',
    'verified_fix',
    'architecture_decision',
    'dependency_guidance',
    'quarantined_evidence'
  ));

ALTER TABLE agentcore.retrieval_documents DROP COLUMN IF EXISTS embedding_dim;
ALTER TABLE agentcore.retrieval_documents DROP COLUMN IF EXISTS embedding_model;
ALTER TABLE agentcore.retrieval_documents DROP COLUMN IF EXISTS chunk_id;

DELETE FROM agentcore.schema_migrations WHERE version = 'm5.002';

COMMIT;
