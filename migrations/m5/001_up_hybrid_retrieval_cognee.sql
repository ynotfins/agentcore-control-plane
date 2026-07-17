-- M5 001 UP — Hybrid Retrieval and Curated Cognee Memory
--
-- Authority: BLUEPRINT.md M5 and docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md M5.
-- Target: PostgreSQL 18 agent_core on 127.0.0.1:55433.
-- Scope: PostgreSQL metadata/FTS/pg_trgm/pgvector exact retrieval, benchmark-gated
--        HNSW decision recording, E: official-document pointers indexed in F:, and
--        curated Cognee promotion metadata behind KnowledgeMemoryPort.
--
-- Intentionally NOT included: Mem0, IVFFlat, pgvectorscale, DiskANN, LangGraph M6,
-- runtime JIT leases, new IDE-facing MCP servers, or raw transcript ingestion.

BEGIN;

CREATE SCHEMA IF NOT EXISTS agentcore;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = 'agentcore'::regnamespace AND typname = 'retrieval_scope') THEN
    CREATE TYPE agentcore.retrieval_scope AS ENUM ('project', 'global');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = 'agentcore'::regnamespace AND typname = 'supersession_state') THEN
    CREATE TYPE agentcore.supersession_state AS ENUM ('current', 'superseded', 'rejected');
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS agentcore.retrieval_documents (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    scope               agentcore.retrieval_scope NOT NULL DEFAULT 'project',
    title               text NOT NULL,
    body                text NOT NULL,
    source_uri          text NOT NULL,
    source_path         text,
    source_kind         text NOT NULL,
    trust_class         agentcore.trust_class NOT NULL,
    version             text NOT NULL,
    provenance          jsonb NOT NULL DEFAULT '{}'::jsonb,
    source_evidence_ids uuid[] NOT NULL DEFAULT ARRAY[]::uuid[],
    embedding           vector,
    metadata            jsonb NOT NULL DEFAULT '{}'::jsonb,
    search_tsv          tsvector GENERATED ALWAYS AS (
      to_tsvector('english', coalesce(title, '') || ' ' || coalesce(body, ''))
    ) STORED,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    CHECK ((scope = 'global' AND project_id IS NULL) OR (scope = 'project' AND project_id IS NOT NULL)),
    CHECK (source_kind IN (
      'accepted_evidence',
      'official_document',
      'curated_cognee_knowledge',
      'verified_fix',
      'architecture_decision',
      'dependency_guidance',
      'quarantined_evidence'
    ))
);

CREATE TABLE IF NOT EXISTS agentcore.curated_knowledge_promotions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    scope               agentcore.retrieval_scope NOT NULL,
    content_kind        text NOT NULL,
    trust_class         agentcore.trust_class NOT NULL,
    title               text NOT NULL,
    body                text NOT NULL,
    version             text NOT NULL,
    source_evidence_ids uuid[] NOT NULL DEFAULT ARRAY[]::uuid[],
    provenance          jsonb NOT NULL DEFAULT '{}'::jsonb,
    promotion_decision  text NOT NULL,
    supersession_state  agentcore.supersession_state NOT NULL DEFAULT 'current',
    retrieval_document_id uuid REFERENCES agentcore.retrieval_documents(id) ON DELETE RESTRICT,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CHECK ((scope = 'global' AND project_id IS NULL) OR (scope = 'project' AND project_id IS NOT NULL)),
    CHECK (content_kind IN (
      'validated_fact',
      'architecture_decision',
      'verified_fix',
      'reusable_pattern',
      'dependency_guidance',
      'official_document_concept'
    ))
);

CREATE TABLE IF NOT EXISTS agentcore.retrieval_benchmarks (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    benchmark_key   text NOT NULL,
    corpus_rows     integer NOT NULL CHECK (corpus_rows >= 0),
    exact_latency_ms numeric(12,3),
    ann_latency_ms   numeric(12,3),
    recall_at_k      numeric(6,5),
    decision         text NOT NULL,
    notes            text NOT NULL,
    measured_at      timestamptz NOT NULL DEFAULT now(),
    metadata         jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_retrieval_documents_project_trust
  ON agentcore.retrieval_documents (project_id, trust_class, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_retrieval_documents_scope_trust
  ON agentcore.retrieval_documents (scope, trust_class, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_retrieval_documents_fts
  ON agentcore.retrieval_documents USING gin (search_tsv);
CREATE INDEX IF NOT EXISTS idx_retrieval_documents_title_trgm
  ON agentcore.retrieval_documents USING gin (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_retrieval_documents_body_trgm
  ON agentcore.retrieval_documents USING gin (body gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_curated_promotions_project_state
  ON agentcore.curated_knowledge_promotions (project_id, supersession_state, created_at DESC);

-- M5 corpus is intentionally bounded. HNSW is not created by this migration until
-- measurements justify ANN; this row records the gate for acceptance evidence.
INSERT INTO agentcore.retrieval_benchmarks (
  benchmark_key, corpus_rows, exact_latency_ms, ann_latency_ms, recall_at_k, decision, notes, metadata
)
VALUES (
  'm5.hnsw.decision',
  0,
  NULL,
  NULL,
  NULL,
  'deferred',
  'M5 fixtures are bounded; exact pgvector is the correctness baseline and no ANN index is justified yet.',
  '{"deferred":["ivfflat","pgvectorscale","diskann"],"canonical":"postgresql_pgvector_exact"}'::jsonb
)
ON CONFLICT DO NOTHING;

CREATE OR REPLACE FUNCTION agentcore.promote_curated_knowledge(
    p_project_id uuid,
    p_scope agentcore.retrieval_scope,
    p_content_kind text,
    p_trust_class agentcore.trust_class,
    p_title text,
    p_body text,
    p_version text,
    p_source_evidence_ids uuid[],
    p_provenance jsonb,
    p_promotion_decision text
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = agentcore, public
AS $$
DECLARE
    v_promotion_id uuid;
    v_document_id uuid;
BEGIN
    IF p_scope = 'project' THEN
      PERFORM agentcore.assert_project_scope(p_project_id);
    ELSIF p_project_id IS NOT NULL THEN
      RAISE EXCEPTION 'global curated knowledge must not carry project_id'
        USING ERRCODE = '23514';
    END IF;

    IF p_content_kind IN ('raw_transcript', 'entire_repository', 'terminal_dump', 'untrusted_web', 'tool_output', 'quarantined_evidence') THEN
      RAISE EXCEPTION 'promotion gate rejected content kind %', p_content_kind
        USING ERRCODE = '42501';
    END IF;

    IF p_content_kind NOT IN (
      'validated_fact', 'architecture_decision', 'verified_fix',
      'reusable_pattern', 'dependency_guidance', 'official_document_concept'
    ) THEN
      RAISE EXCEPTION 'promotion gate does not allow content kind %', p_content_kind
        USING ERRCODE = '23514';
    END IF;

    IF p_trust_class IN ('raw_untrusted', 'quarantined', 'rejected') THEN
      RAISE EXCEPTION 'promotion gate rejected trust class %', p_trust_class
        USING ERRCODE = '42501';
    END IF;

    IF coalesce(p_promotion_decision, '') !~* 'approved|accepted|validated' THEN
      RAISE EXCEPTION 'promotion decision must be explicit approval/acceptance/validation'
        USING ERRCODE = '23514';
    END IF;

    INSERT INTO agentcore.retrieval_documents (
      project_id, scope, title, body, source_uri, source_path, source_kind,
      trust_class, version, provenance, source_evidence_ids, metadata
    )
    VALUES (
      p_project_id, p_scope, p_title, p_body,
      'cognee://curated/' || gen_random_uuid()::text,
      NULL,
      'curated_cognee_knowledge',
      p_trust_class,
      p_version,
      coalesce(p_provenance, '{}'::jsonb),
      coalesce(p_source_evidence_ids, ARRAY[]::uuid[]),
      jsonb_build_object('promotion_decision', p_promotion_decision, 'content_kind', p_content_kind)
    )
    RETURNING id INTO v_document_id;

    INSERT INTO agentcore.curated_knowledge_promotions (
      project_id, scope, content_kind, trust_class, title, body, version,
      source_evidence_ids, provenance, promotion_decision, supersession_state,
      retrieval_document_id
    )
    VALUES (
      p_project_id, p_scope, p_content_kind, p_trust_class, p_title, p_body, p_version,
      coalesce(p_source_evidence_ids, ARRAY[]::uuid[]),
      coalesce(p_provenance, '{}'::jsonb),
      p_promotion_decision,
      'current',
      v_document_id
    )
    RETURNING id INTO v_promotion_id;

    UPDATE agentcore.retrieval_documents
    SET source_uri = 'cognee://curated/' || v_promotion_id::text,
        metadata = metadata || jsonb_build_object('promotion_id', v_promotion_id)
    WHERE id = v_document_id;

    RETURN v_promotion_id;
END;
$$;

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

GRANT SELECT ON agentcore.retrieval_documents TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.curated_knowledge_promotions TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT SELECT ON agentcore.retrieval_benchmarks TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT INSERT, UPDATE ON agentcore.retrieval_documents TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.curated_knowledge_promotions TO agentcore_worker, agentcore_admin;
GRANT INSERT, UPDATE ON agentcore.retrieval_benchmarks TO agentcore_worker, agentcore_admin;
GRANT ALL ON agentcore.retrieval_documents TO agentcore_admin;
GRANT ALL ON agentcore.curated_knowledge_promotions TO agentcore_admin;
GRANT ALL ON agentcore.retrieval_benchmarks TO agentcore_admin;

GRANT EXECUTE ON FUNCTION agentcore.promote_curated_knowledge(uuid, agentcore.retrieval_scope, text, agentcore.trust_class, text, text, text, uuid[], jsonb, text) TO agentcore_worker, agentcore_admin;
GRANT EXECUTE ON FUNCTION agentcore.hybrid_retrieve_documents(uuid, text, vector, integer, text[], text[]) TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_admin;

INSERT INTO agentcore.schema_migrations (version, description, blueprint_level)
VALUES ('m5.001', 'hybrid PostgreSQL retrieval and curated Cognee promotion boundary', 'M5')
ON CONFLICT (version) DO NOTHING;

COMMIT;
