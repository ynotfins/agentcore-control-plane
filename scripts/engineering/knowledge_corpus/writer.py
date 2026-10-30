"""Upsert chunk rows into agentcore.retrieval_documents."""

from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .chunkers import Chunk, content_sha256
from .config import EMBEDDING_DIM, EMBEDDING_MODEL_SHORT, LEGACY_SOURCE_KIND, SOURCE_KIND_BY_ASSET
from .embedder import Embedder
from .schema_probe import SchemaCapabilities


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"


def resolve_source_kind(asset_type: str, caps: SchemaCapabilities) -> str:
    desired = SOURCE_KIND_BY_ASSET.get(asset_type, "official_document")
    if caps.knowledge_corpus_ready and desired in caps.source_kinds:
        return desired
    return LEGACY_SOURCE_KIND.get(desired, "official_document")


def upsert_chunk(
    conn: psycopg.Connection,
    *,
    caps: SchemaCapabilities,
    embedder: Embedder,
    path: str,
    source_uri: str,
    asset_type: str,
    framework: str,
    version: str,
    license_id: str,
    trust_class: str,
    chunk: Chunk,
    dry_run: bool = False,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_kind = resolve_source_kind(asset_type, caps)
    vectors = embedder.embed([chunk.body[:8000]])
    embedding = vectors[0]
    if len(embedding) != embedder.dim:
        raise ValueError(f"embedding dim mismatch: got {len(embedding)} expected {embedder.dim}")

    metadata: dict[str, Any] = {
        "asset_type": asset_type,
        "framework": framework,
        "language": chunk.language,
        "license": license_id,
        "chunk_id": chunk.chunk_id,
        "embedding_model": embedder.model_id,
        "embedding_dim": embedder.dim,
        "content_sha256": content_sha256(chunk.body),
        "version": version,
        **chunk.extra_metadata,
        **(extra_metadata or {}),
    }
    provenance = {
        "maintainer": "operator",
        "ingest": "knowledge_corpus",
        "source_path": path,
    }

    result = {
        "title": chunk.title[:500],
        "chunk_id": chunk.chunk_id,
        "source_uri": source_uri,
        "source_kind": source_kind,
        "embedding_model": embedder.model_id,
        "dry_run": dry_run,
    }
    if dry_run:
        return result

    body = chunk.body[:50000]
    emb_lit = vector_literal(embedding)

    with conn.cursor() as cur:
        if caps.knowledge_corpus_ready:
            cur.execute(
                """
                INSERT INTO agentcore.retrieval_documents
                    (scope, title, body, source_uri, source_path, source_kind,
                     trust_class, version, provenance, metadata, embedding,
                     chunk_id, embedding_model, embedding_dim)
                VALUES (
                    'global', %s, %s, %s, %s, %s,
                    %s::agentcore.trust_class, %s, %s::jsonb, %s::jsonb, %s::vector,
                    %s, %s, %s
                )
                ON CONFLICT (source_uri, version, chunk_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    body = EXCLUDED.body,
                    source_path = EXCLUDED.source_path,
                    source_kind = EXCLUDED.source_kind,
                    trust_class = EXCLUDED.trust_class,
                    provenance = EXCLUDED.provenance,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    embedding_model = EXCLUDED.embedding_model,
                    embedding_dim = EXCLUDED.embedding_dim,
                    updated_at = now()
                RETURNING id
                """,
                (
                    chunk.title[:500],
                    body,
                    source_uri,
                    path,
                    source_kind,
                    trust_class,
                    version,
                    Jsonb(provenance),
                    Jsonb(metadata),
                    emb_lit,
                    chunk.chunk_id,
                    embedder.model_id,
                    embedder.dim,
                ),
            )
        else:
            # Pre-m5.002: delete+insert by metadata chunk identity (no unique index).
            cur.execute(
                """
                DELETE FROM agentcore.retrieval_documents
                WHERE source_uri = %s
                  AND version = %s
                  AND metadata->>'chunk_id' = %s
                """,
                (source_uri, version, chunk.chunk_id),
            )
            cur.execute(
                """
                INSERT INTO agentcore.retrieval_documents
                    (scope, title, body, source_uri, source_path, source_kind,
                     trust_class, version, provenance, metadata, embedding)
                VALUES (
                    'global', %s, %s, %s, %s, %s,
                    %s::agentcore.trust_class, %s, %s::jsonb, %s::jsonb, %s::vector
                )
                RETURNING id
                """,
                (
                    chunk.title[:500],
                    body,
                    source_uri,
                    path,
                    source_kind,
                    trust_class,
                    version,
                    Jsonb(provenance),
                    Jsonb(metadata),
                    emb_lit,
                ),
            )
        row = cur.fetchone()
        if not row:
            result["id"] = None
        elif isinstance(row, dict):
            result["id"] = str(row.get("id"))
        else:
            result["id"] = str(row[0])
    return result


# Silence unused import lint for documented constant
_ = (EMBEDDING_DIM, EMBEDDING_MODEL_SHORT)
