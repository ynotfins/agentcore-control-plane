"""Detect whether m5.002 knowledge-corpus columns exist on live agent_core."""

from __future__ import annotations

from dataclasses import dataclass

import psycopg
from psycopg.rows import dict_row


@dataclass
class SchemaCapabilities:
    has_chunk_id: bool
    has_embedding_model: bool
    has_embedding_dim: bool
    source_kinds: set[str]
    migration_m5002: bool

    @property
    def knowledge_corpus_ready(self) -> bool:
        return (
            self.has_chunk_id
            and self.has_embedding_model
            and self.has_embedding_dim
            and {"boilerplate", "agent_rule", "openapi_spec"}.issubset(self.source_kinds)
        )


def probe(conn: psycopg.Connection) -> SchemaCapabilities:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'agentcore'
              AND table_name = 'retrieval_documents'
              AND column_name IN ('chunk_id', 'embedding_model', 'embedding_dim')
            """
        )
        cols = {r["column_name"] for r in cur.fetchall()}

        cur.execute(
            """
            SELECT pg_get_constraintdef(c.oid) AS def
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'agentcore'
              AND t.relname = 'retrieval_documents'
              AND c.contype = 'c'
              AND pg_get_constraintdef(c.oid) ILIKE '%source_kind%'
            """
        )
        rows = cur.fetchall()
        kinds: set[str] = set()
        for row in rows:
            defn = row["def"] or ""
            for token in (
                "accepted_evidence",
                "official_document",
                "curated_cognee_knowledge",
                "verified_fix",
                "architecture_decision",
                "dependency_guidance",
                "quarantined_evidence",
                "boilerplate",
                "agent_rule",
                "openapi_spec",
            ):
                if f"'{token}'" in defn:
                    kinds.add(token)

        cur.execute(
            """
            SELECT 1 AS ok
            FROM agentcore.schema_migrations
            WHERE version = 'm5.002'
            LIMIT 1
            """
        )
        mig = cur.fetchone() is not None

    return SchemaCapabilities(
        has_chunk_id="chunk_id" in cols,
        has_embedding_model="embedding_model" in cols,
        has_embedding_dim="embedding_dim" in cols,
        source_kinds=kinds,
        migration_m5002=mig,
    )
