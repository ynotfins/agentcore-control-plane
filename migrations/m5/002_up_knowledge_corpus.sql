-- M5 002 UP — Knowledge corpus metadata, chunk identity, local-embedding lock
--
-- Authority: BLUEPRINT.md M5/M7; postgreSQL18-control-plane docs/databases/agent-knowledge.md
-- Target: PostgreSQL 18 agent_core on 127.0.0.1:55433
-- Scope: Additive only — expand source_kind, chunk identity, embedding model/dim,
--        metadata prefilter indexes, hybrid_retrieve metadata filters.
--
-- HARD GATE: Do NOT apply to live agent_core without explicit operator AUTH,
--            backup/restore gate, and dry-run ROLLBACK first.
-- Intentionally NOT included: HNSW/IVFFlat/pgvectorscale, LanceDB, Qdrant,
-- new database names, whole-repository dumps, Mem0.

BEGIN;

-- ---------------------------------------------------------------------------
-- Columns: chunk identity + embedding lock
-- ---------------------------------------------------------------------------
ALTER TABLE agentcore.retrieval_documents
  ADD COLUMN IF NOT EXISTS chunk_id text NOT NULL DEFAULT '';

ALTER TABLE agentcore.retrieval_documents
  ADD COLUMN IF NOT EXISTS embedding_model text;

ALTER TABLE agentcore.retrieval_documents
  ADD COLUMN IF NOT EXISTS embedding_dim integer
    CHECK (embedding_dim IS NULL OR embedding_dim > 0);

COMMENT ON COLUMN agentcore.retrieval_documents.chunk_id IS
  'Stable chunk identity within a source_uri+version; empty string = whole document.';
COMMENT ON COLUMN agentcore.retrieval_documents.embedding_model IS
  'Frozen dense embedding model id, e.g. nomic-embed-text-v1.5';
COMMENT ON COLUMN agentcore.retrieval_documents.embedding_dim IS
  'Embedding dimensionality locked to the model (768 for nomic-embed-text-v1.5)';

-- Backfill chunk identity from metadata before unique index (legacy seed rows).
UPDATE agentcore.retrieval_documents
SET chunk_id = coalesce(nullif(metadata->>'chunk_id', ''), id::text)
WHERE chunk_id = ''
  AND metadata ? 'chunk_id'
  AND coalesce(metadata->>'chunk_id', '') <> '';

-- Any remaining empty duplicates get a stable per-row identity.
UPDATE agentcore.retrieval_documents d
SET chunk_id = d.id::text
WHERE d.chunk_id = ''
  AND EXISTS (
    SELECT 1
    FROM agentcore.retrieval_documents x
    WHERE x.source_uri = d.source_uri
      AND x.version = d.version
      AND x.chunk_id = ''
      AND x.id <> d.id
  );

-- Idempotent ingest key
CREATE UNIQUE INDEX IF NOT EXISTS uq_retrieval_documents_source_version_chunk
  ON agentcore.retrieval_documents (source_uri, version, chunk_id);

-- ---------------------------------------------------------------------------
-- Expand source_kind CHECK (drop/recreate inline constraint)
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  conname text;
BEGIN
  SELECT c.conname INTO conname
  FROM pg_constraint c
  JOIN pg_class t ON t.oid = c.conrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
  WHERE n.nspname = 'agentcore'
    AND t.relname = 'retrieval_documents'
    AND c.contype = 'c'
    AND pg_get_constraintdef(c.oid) ILIKE '%source_kind%';

  IF conname IS NOT NULL THEN
    EXECUTE format('ALTER TABLE agentcore.retrieval_documents DROP CONSTRAINT %I', conname);
  END IF;

  ALTER TABLE agentcore.retrieval_documents
    ADD CONSTRAINT retrieval_documents_source_kind_check
    CHECK (source_kind IN (
      'accepted_evidence',
      'official_document',
      'curated_cognee_knowledge',
      'verified_fix',
      'architecture_decision',
      'dependency_guidance',
      'quarantined_evidence',
      'boilerplate',
      'agent_rule',
      'openapi_spec'
    ));
END $$;

-- ---------------------------------------------------------------------------
-- Metadata prefilter expression indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_retrieval_documents_meta_asset_type
  ON agentcore.retrieval_documents ((metadata->>'asset_type'));
CREATE INDEX IF NOT EXISTS idx_retrieval_documents_meta_framework
  ON agentcore.retrieval_documents ((metadata->>'framework'));
CREATE INDEX IF NOT EXISTS idx_retrieval_documents_meta_language
  ON agentcore.retrieval_documents ((metadata->>'language'));
CREATE INDEX IF NOT EXISTS idx_retrieval_documents_meta_license
  ON agentcore.retrieval_documents ((metadata->>'license'));
CREATE INDEX IF NOT EXISTS idx_retrieval_documents_metadata_gin
  ON agentcore.retrieval_documents USING gin (metadata jsonb_path_ops);

-- ---------------------------------------------------------------------------
-- hybrid_retrieve_documents — add optional metadata filter (jsonb containment)
-- Signature change: DROP old overload, CREATE new with p_metadata_filter
-- ---------------------------------------------------------------------------
DROP FUNCTION IF EXISTS agentcore.hybrid_retrieve_documents(uuid, text, vector, integer, text[], text[]);

CREATE OR REPLACE FUNCTION agentcore.hybrid_retrieve_documents(
    p_project_id uuid,
    p_query text,
    p_query_embedding vector DEFAULT NULL,
    p_limit integer DEFAULT 5,
    p_trust_classes text[] DEFAULT NULL,
    p_methods text[] DEFAULT NULL,
    p_metadata_filter jsonb DEFAULT NULL
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
    AND (p_metadata_filter IS NULL OR d.metadata @> p_metadata_filter)
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
      'chunk_id', e.chunk_id,
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
      'chunk_id', e.chunk_id,
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
      'chunk_id', e.chunk_id,
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
      'chunk_id', e.chunk_id,
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

GRANT EXECUTE ON FUNCTION agentcore.hybrid_retrieve_documents(uuid, text, vector, integer, text[], text[], jsonb)
  TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_admin;

INSERT INTO agentcore.schema_migrations (version, description, blueprint_level)
VALUES (
  'm5.002',
  'knowledge corpus chunk identity, embedding lock, metadata prefilters',
  'M5'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
