"""AgentCore M7 — Seed engineering knowledge into F: retrieval index.

Reads Engineering Constitution, dependency catalog, and recipe files from the
repository (as official documentation) and inserts retrieval_documents rows
into PostgreSQL (F:) so they are discoverable through docs_search and
retrieve_context without scanning the full E: corpus.

Source files are tracked in retrieval_documents.source_path pointing to D: repo paths.
Official long-term copies should live on E:/AgentCoreArchive/agentcore-memory/official-docs/.

Run: python scripts/engineering/seed_knowledge_index.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

REPO_ROOT = Path(__file__).resolve().parents[2]
PG_PASS = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
CI = f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={PG_PASS}"
E_DOCS = Path(r"E:\AgentCoreArchive\agentcore-memory\official-docs\m7-engineering")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(msg: str) -> None:
    sys.stderr.write(f"[seed_knowledge] {msg}\n")


KNOWLEDGE_SOURCES = [
    {
        "title": "AgentCore Engineering Constitution",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "CONSTITUTION.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/CONSTITUTION.md",
        "trust_class": "operator_verified",
        "version": "2026-07-16",
        "tags": ["constitution", "engineering", "standards", "python", "postgresql", "mcp", "langgraph"],
    },
    {
        "title": "Dependency Catalog",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "dependency-catalog" / "catalog.yaml",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/dependency-catalog/catalog.yaml",
        "trust_class": "operator_verified",
        "version": "2026-07-16",
        "tags": ["dependencies", "catalog", "approved", "rejected", "psycopg", "langgraph", "copier"],
    },
    {
        "title": "Recipe 01: PostgreSQL Migration and Rollback",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "recipes" / "01-pg-migration-rollback.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/recipes/01-pg-migration-rollback.md",
        "trust_class": "system_verified",
        "version": "2026-07-16",
        "tags": ["recipe", "postgresql", "migration", "rollback", "sql"],
    },
    {
        "title": "Recipe 02: Secure Environment Variable Loading",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "recipes" / "02-env-var-loading.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/recipes/02-env-var-loading.md",
        "trust_class": "system_verified",
        "version": "2026-07-16",
        "tags": ["recipe", "security", "secrets", "env", "python", "powershell"],
    },
    {
        "title": "Recipe 03: MCP Stdio Server (Bifrost-compatible)",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "recipes" / "03-mcp-stdio-server.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/recipes/03-mcp-stdio-server.md",
        "trust_class": "system_verified",
        "version": "2026-07-16",
        "tags": ["recipe", "mcp", "stdio", "bifrost", "python", "server"],
    },
    {
        "title": "Recipe 04: MCP Streamable HTTP Server",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "recipes" / "04-mcp-streamable-http.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/recipes/04-mcp-streamable-http.md",
        "trust_class": "system_verified",
        "version": "2026-07-16",
        "tags": ["recipe", "mcp", "http", "streamable", "python"],
    },
    {
        "title": "Recipe 05: LangGraph PostgreSQL Checkpoint and Resume",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "recipes" / "05-langgraph-pg-checkpoint.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/recipes/05-langgraph-pg-checkpoint.md",
        "trust_class": "system_verified",
        "version": "2026-07-16",
        "tags": ["recipe", "langgraph", "checkpoint", "resume", "postgresql"],
    },
    {
        "title": "Recipe 06: LangGraph Human-Review Pause/Resume",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "recipes" / "06-langgraph-human-review.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/recipes/06-langgraph-human-review.md",
        "trust_class": "system_verified",
        "version": "2026-07-16",
        "tags": ["recipe", "langgraph", "human", "pause", "resume", "interrupt"],
    },
    {
        "title": "Recipe 07: Windows Service and Scheduled Task Recovery",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "recipes" / "07-windows-service-recovery.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/recipes/07-windows-service-recovery.md",
        "trust_class": "system_verified",
        "version": "2026-07-16",
        "tags": ["recipe", "windows", "service", "task-scheduler", "recovery", "bifrost"],
    },
    {
        "title": "Recipe 08: Structured Logging and Diagnostics",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "recipes" / "08-structured-logging.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/recipes/08-structured-logging.md",
        "trust_class": "system_verified",
        "version": "2026-07-16",
        "tags": ["recipe", "logging", "diagnostics", "structured", "json", "stderr"],
    },
    {
        "title": "Recipe 09: Backup, Restore, and Point-in-Time Recovery",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "recipes" / "09-backup-restore-pitr.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/recipes/09-backup-restore-pitr.md",
        "trust_class": "system_verified",
        "version": "2026-07-16",
        "tags": ["recipe", "backup", "restore", "pitr", "postgresql", "wal"],
    },
    {
        "title": "Recipe 10: Isolated Project and Worktree Execution",
        "source_kind": "official_document",
        "path": REPO_ROOT / "docs" / "engineering" / "recipes" / "10-isolated-project-worktree.md",
        "source_uri": "file://D:/github/agentcore-control-plane/docs/engineering/recipes/10-isolated-project-worktree.md",
        "trust_class": "system_verified",
        "version": "2026-07-16",
        "tags": ["recipe", "worktree", "git", "isolation", "project"],
    },
]


def seed_to_db(sources: list[dict]) -> list[str]:
    """Insert knowledge documents into agentcore.retrieval_documents for F: FTS/vector index."""
    inserted_ids = []
    with psycopg.connect(CI, row_factory=dict_row) as c:
        # Get a global project (scope=global means project_id IS NULL)
        for src in sources:
            path = src["path"]
            if not path.exists():
                _log(f"SKIP (not found): {path}")
                continue

            body = path.read_text(encoding="utf-8", errors="replace")
            content_hash = hashlib.sha256(body.encode()).hexdigest()

            row = c.execute(
                """
                INSERT INTO agentcore.retrieval_documents
                    (scope, title, body, source_uri, source_path, source_kind,
                     trust_class, version, provenance, metadata)
                VALUES (
                    'global', %s, %s, %s, %s, %s,
                    %s::agentcore.trust_class, %s,
                    %s,
                    %s
                )
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (
                    src["title"],
                    body[:50000],  # cap at 50KB; large bodies go to E:
                    src["source_uri"],
                    str(src["path"]),
                    src["source_kind"],
                    src["trust_class"],
                    src["version"],
                    json.dumps({"content_sha256": content_hash, "maintainer": "operator"}),
                    json.dumps({"tags": src.get("tags", []), "m7": True}),
                ),
            ).fetchone()
            if row:
                inserted_ids.append(str(row["id"]))
                _log(f"INSERTED: {src['title']} → {row['id']}")
            else:
                _log(f"ALREADY EXISTS (skipped): {src['title']}")
    return inserted_ids


def copy_to_e_archive(sources: list[dict]) -> list[str]:
    """Copy source files to E:/AgentCoreArchive as the official cold archive."""
    try:
        E_DOCS.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        _log(f"Cannot create E: archive dir (non-fatal): {exc}")
        return []

    copied = []
    for src in sources:
        path = src["path"]
        if not path.exists():
            continue
        dest = E_DOCS / path.name
        try:
            dest.write_bytes(path.read_bytes())
            copied.append(str(dest))
        except Exception as exc:
            _log(f"E: copy failed for {path.name}: {exc}")
    return copied


if __name__ == "__main__":
    _log(f"Starting M7 knowledge seed — {_now()}")
    e_files = copy_to_e_archive(KNOWLEDGE_SOURCES)
    _log(f"E: archive: {len(e_files)} files copied")
    inserted = seed_to_db(KNOWLEDGE_SOURCES)
    _log(f"F: index: {len(inserted)} new rows inserted ({len(KNOWLEDGE_SOURCES) - len(inserted)} skipped as existing)")
    print(json.dumps({
        "ok": True,
        "e_archive_files": len(e_files),
        "f_index_inserted": len(inserted),
        "total_sources": len(KNOWLEDGE_SOURCES),
    }))
