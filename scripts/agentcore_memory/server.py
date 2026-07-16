#!/usr/bin/env python3
"""AgentCore memory MCP server (stdio NDJSON).

Bifrost Windows Gateway speaks newline-delimited JSON-RPC on STDIO
(not Content-Length framing). Protocol version observed: 2025-06-18.

Tools:
  memory_status, startup_context, retrieve_context, append_event, propose_fact,
  expand_source, session_open, session_close, build_handoff, docs_search

Never exposes credentials. Stable identity: agentcore-memory
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import sys
import traceback
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from knowledge_memory import get_knowledge_memory_port
from recovery import (
    EXCLUDED_NORMAL_TRUST_CLASSES,
    ModelContextProfile,
    content_sha256,
    decode_cursor,
    encode_cursor,
    estimate_tokens,
    recovery_scope_hash,
)

SERVER_NAME = "agentcore-memory"
SERVER_VERSION = "0.6.0"
# Bifrost currently initializes with 2025-06-18; accept and echo it.
SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}
DEFAULT_PROTOCOL_VERSION = "2025-06-18"
PG_HOST = os.environ.get("AGENTCORE_PG_HOST", "127.0.0.1")
PG_PORT = int(os.environ.get("AGENTCORE_PG_PORT", "55433"))
PG_DATABASE = os.environ.get("AGENTCORE_PG_DATABASE", "agent_core")
PG_USER = os.environ.get("AGENTCORE_PG_USER", "postgres")
PG_PASSWORD_ENV = "AGENT_CORE_POSTGRES_PASSWORD"
REPO_PATH = Path(
    os.environ.get("AGENTCORE_REPO_PATH", r"D:\github\agentcore-control-plane")
)
HOT_ARTIFACT_ROOT = Path(
    os.environ.get(
        "AGENTCORE_HOT_ARTIFACT_ROOT", r"H:\AgentRuntime\agentcore-memory\artifacts"
    )
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(msg: str) -> None:
    sys.stderr.write(f"[{SERVER_NAME}] {msg}\n")
    sys.stderr.flush()


def postgres_reachable(timeout: float = 1.5) -> tuple[bool, str]:
    try:
        with socket.create_connection((PG_HOST, PG_PORT), timeout=timeout):
            return True, "tcp_ok"
    except OSError as exc:
        return False, exc.__class__.__name__


def tool_defs() -> list[dict[str, Any]]:
    text_schema = {"type": "string"}
    text_array_schema = {"type": "array", "items": text_schema}
    embedding_schema = {"type": "array", "items": {"type": "number"}}
    recovery_properties = {
        "context_profile": text_schema,
        "recovery_mode": {
            "type": "string",
            "enum": [
                "current_state",
                "current_milestone",
                "session_replay",
                "milestone_replay",
                "time_range_replay",
                "decision_history",
                "failure_fix_reconstruction",
                "complete_project_chronology",
            ],
        },
        "continuation_cursor": text_schema,
        "page_size": {"type": "integer", "minimum": 1},
        "session_id": text_schema,
        "milestone": text_schema,
        "start_at": text_schema,
        "end_at": text_schema,
        "include_quarantined": {"type": "boolean"},
        "record_recovery": {"type": "boolean"},
    }
    return [
        {
            "name": "memory_status",
            "description": "Return sanitized memory/gateway status summary without secrets.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "session_open",
            "description": "Open or create a governed AgentCore memory session for a project/client/agent.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_key": text_schema,
                    "project_name": text_schema,
                    "client_key": text_schema,
                    "agent_key": text_schema,
                    "session_key": text_schema,
                    "project_root": text_schema,
                    "repo_key": text_schema,
                    "remote_url": text_schema,
                    "branch_name": text_schema,
                    "head_commit": text_schema,
                    "model_provider": text_schema,
                    "model_id": text_schema,
                    "context_profile": text_schema,
                },
                "required": ["project_key"],
                "additionalProperties": False,
            },
        },
        {
            "name": "session_close",
            "description": "Close a governed AgentCore memory session.",
            "inputSchema": {
                "type": "object",
                "properties": {"session_id": text_schema},
                "required": ["session_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "append_event",
            "description": "Append an immutable event through AgentCore memory (idempotent; no raw SQL exposed).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "session_id": text_schema,
                    "event_kind": text_schema,
                    "idempotency_key": text_schema,
                    "payload": {"type": "object"},
                    "trust_class": text_schema,
                    "large_text": text_schema,
                },
                "required": ["session_id", "event_kind", "idempotency_key", "payload"],
                "additionalProperties": False,
            },
        },
        {
            "name": "retrieve_context",
            "description": "Retrieve bounded context for a project using model-specific token budgets.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_key": text_schema,
                    "budget_name": text_schema,
                    "query": text_schema,
                    "limit": {"type": "integer"},
                    "query_embedding": embedding_schema,
                    "retrieval_methods": text_array_schema,
                    "trust_classes": text_array_schema,
                    **recovery_properties,
                },
                "required": ["project_key"],
                "additionalProperties": False,
            },
        },
        {
            "name": "startup_context",
            "description": "Return a startup context packet for a project/session.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_key": text_schema,
                    "budget_name": text_schema,
                    **recovery_properties,
                },
                "required": ["project_key"],
                "additionalProperties": False,
            },
        },
        {
            "name": "expand_source",
            "description": "Expand a summary, event, or artifact reference back to exact source evidence.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_key": text_schema,
                    "summary_id": text_schema,
                    "event_id": text_schema,
                    "artifact_id": text_schema,
                    "continuation_cursor": text_schema,
                    "page_size": {"type": "integer", "minimum": 1},
                    "artifact_offset": {"type": "integer", "minimum": 0},
                    "max_bytes": {"type": "integer", "minimum": 1},
                },
                "required": ["project_key"],
                "anyOf": [
                    {"required": ["summary_id"]},
                    {"required": ["event_id"]},
                    {"required": ["artifact_id"]},
                ],
                "additionalProperties": False,
            },
        },
        {
            "name": "propose_fact",
            "description": "Create a governed fact proposal/review record instead of silently replacing truth.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_key": text_schema,
                    "fact_key": text_schema,
                    "proposed_value": {"type": "object"},
                    "contradicts_event_id": text_schema,
                    "trust_class": text_schema,
                },
                "required": ["project_key", "fact_key", "proposed_value"],
                "additionalProperties": False,
            },
        },
        {
            "name": "build_handoff",
            "description": "Build a compact project handoff packet from canonical memory state.",
            "inputSchema": {
                "type": "object",
                "properties": {"project_key": text_schema, **recovery_properties},
                "required": ["project_key"],
                "additionalProperties": False,
            },
        },
        {
            "name": "docs_search",
            "description": "Search indexed AgentCore memory documentation/context metadata (Arabold remains source for external docs).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_key": text_schema,
                    "query": text_schema,
                    "limit": {"type": "integer"},
                    "query_embedding": embedding_schema,
                    "retrieval_methods": text_array_schema,
                    "trust_classes": text_array_schema,
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    ]


def db() -> psycopg.Connection[Any]:
    password = os.environ.get(PG_PASSWORD_ENV)
    if not password:
        raise RuntimeError(f"missing required env var {PG_PASSWORD_ENV}")
    return psycopg.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=password,
        sslmode="require",
        row_factory=dict_row,
    )


def redact_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: redact_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_payload(v) for v in value]
    if isinstance(value, str):
        return value.replace("password=", "password=[REDACTED] ")
    return value


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (UUID, datetime)):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [to_jsonable(v) for v in value]
    return value


def vector_literal(values: Any) -> str | None:
    if values is None:
        return None
    if not isinstance(values, list):
        raise ValueError("query_embedding must be an array of numbers")
    parsed: list[float] = []
    for value in values:
        if not isinstance(value, (int, float)):
            raise ValueError("query_embedding values must be numbers")
        parsed.append(float(value))
    if not parsed:
        return None
    return "[" + ",".join(f"{value:.12g}" for value in parsed) + "]"


def requested_list(args: dict[str, Any], key: str) -> list[str] | None:
    value = args.get(key)
    if value is None:
        return None
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be an array of strings")
    return value


def get_project(conn: psycopg.Connection[Any], project_key: str) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM agentcore.projects WHERE project_key = %s", (project_key,)
        )
        row = cur.fetchone()
    if not row:
        raise ValueError(f"unknown project_key: {project_key}")
    return row


def set_project(conn: psycopg.Connection[Any], project_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT set_config('agentcore.current_project_id', %s, true)", (project_id,)
        )


def session_open(args: dict[str, Any]) -> dict[str, Any]:
    project_key = args["project_key"]
    project_name = args.get("project_name") or project_key
    client_key = args.get("client_key") or "unknown-client"
    agent_key = args.get("agent_key") or "unknown-agent"
    session_key = (
        args.get("session_key") or f"{project_key}:{client_key}:{agent_key}:{_now()}"
    )
    repo_path = str(Path(args.get("project_root") or REPO_PATH).resolve())
    repo_key = args.get("repo_key") or Path(repo_path).name
    remote_url = args.get("remote_url")
    if remote_url is None and repo_key == "agentcore-control-plane":
        remote_url = "https://github.com/ynotfins/agentcore-control-plane.git"
    branch_name = args.get("branch_name") or "unknown"
    head_commit = args.get("head_commit")
    model_hint = (
        ":".join(
            part
            for part in (
                str(args.get("model_provider") or ""),
                str(args.get("model_id") or ""),
            )
            if part
        )
        or "unknown"
    )
    context_profile = args.get("context_profile") or "standard-context"

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            WITH repo AS (
              INSERT INTO agentcore.repositories (repo_key, canonical_path, remote_url)
              VALUES (%s, %s, %s)
              ON CONFLICT (canonical_path) DO UPDATE SET remote_url = EXCLUDED.remote_url
              RETURNING id
            ),
            wt AS (
              INSERT INTO agentcore.worktrees (repository_id, worktree_path, branch_name, head_commit)
              SELECT id, %s, %s, %s FROM repo
              ON CONFLICT (worktree_path) DO UPDATE
                SET branch_name = EXCLUDED.branch_name, head_commit = EXCLUDED.head_commit
              RETURNING id, repository_id
            ),
            project AS (
              INSERT INTO agentcore.projects (project_key, project_name, repository_id, primary_worktree_id, root_path, current_milestone)
              SELECT %s, %s, wt.repository_id, wt.id, %s, 'M4' FROM wt
              ON CONFLICT (project_key) DO UPDATE SET project_name = EXCLUDED.project_name
              RETURNING id, repository_id, primary_worktree_id
            ),
            pwt AS (
              INSERT INTO agentcore.project_worktrees (project_id, worktree_id, is_primary)
              SELECT project.id, project.primary_worktree_id, true FROM project
              ON CONFLICT DO NOTHING
            ),
            client AS (
              INSERT INTO agentcore.ide_clients (client_key, display_name, profile_id)
              VALUES (%s, %s, 'builder-core')
              ON CONFLICT (client_key) DO UPDATE SET display_name = EXCLUDED.display_name
              RETURNING id
            ),
            agent AS (
              INSERT INTO agentcore.agents (agent_key, display_name, model_hint)
              VALUES (%s, %s, %s)
              ON CONFLICT (agent_key) DO UPDATE
                SET display_name = EXCLUDED.display_name, model_hint = EXCLUDED.model_hint
              RETURNING id
            ),
            session AS (
              INSERT INTO agentcore.sessions (
                project_id, client_id, agent_id, session_key, context_profile_name
              )
              SELECT project.id, client.id, agent.id, %s, %s FROM project, client, agent
              ON CONFLICT (session_key) DO UPDATE
                SET ended_at = NULL, context_profile_name = EXCLUDED.context_profile_name
              RETURNING id, project_id, client_id, agent_id
            ),
            run AS (
              INSERT INTO agentcore.runs (session_id, run_key)
              SELECT session.id, %s FROM session
              ON CONFLICT (run_key) DO UPDATE SET ended_at = NULL
              RETURNING id
            ),
            workflow AS (
              INSERT INTO agentcore.workflows (project_id, workflow_key, display_name)
              SELECT project.id, %s, 'M4 Memory Session' FROM project
              ON CONFLICT (workflow_key) DO UPDATE SET display_name = EXCLUDED.display_name
              RETURNING id
            ),
            thread AS (
              INSERT INTO agentcore.workflow_threads (workflow_id, thread_key)
              SELECT workflow.id, %s FROM workflow
              ON CONFLICT (thread_key) DO UPDATE SET thread_key = EXCLUDED.thread_key
              RETURNING id
            ),
            machine AS (
              INSERT INTO agentcore.machines (machine_name, hardware_ref)
              VALUES ('CHAOSCENTRAL', 'D:\\ChaosCentral-Current-Build\\DOC_AUTHORITY.md')
              ON CONFLICT (machine_name) DO UPDATE SET hardware_ref = EXCLUDED.hardware_ref
              RETURNING id
            ),
            usr AS (
              INSERT INTO agentcore.users (username, display_name)
              VALUES ('ynotf', 'Tony Valentine')
              ON CONFLICT (username) DO UPDATE SET display_name = EXCLUDED.display_name
              RETURNING id
            ),
            source AS (
              INSERT INTO agentcore.source_identities (
                machine_id, user_id, project_id, repository_id, worktree_id, client_id, agent_id,
                session_id, run_id, workflow_thread_id, source_label, trust_class
              )
              SELECT machine.id, usr.id, session.project_id, project.repository_id, project.primary_worktree_id,
                     session.client_id, session.agent_id, session.id, run.id, thread.id,
                     %s, 'project_verified'
              FROM machine, usr, project, session, run, thread
              RETURNING id
            )
            SELECT session.id AS session_id, session.project_id, source.id AS source_identity_id, run.id AS run_id
            FROM session, source, run
            """,
            (
                repo_key,
                repo_path,
                remote_url,
                repo_path,
                branch_name,
                head_commit,
                project_key,
                project_name,
                repo_path,
                client_key,
                client_key,
                agent_key,
                agent_key,
                model_hint,
                session_key,
                context_profile,
                f"{session_key}:run",
                f"{project_key}:workflow",
                f"{session_key}:thread",
                f"{session_key}:source",
            ),
        )
        row = cur.fetchone()
        conn.commit()
    return {"ok": True, **row, "session_key": session_key}


def memory_health() -> dict[str, Any]:
    """Internal health helper used by memory_status; not exposed as a normal agent tool."""
    ok, detail = postgres_reachable()
    status = "healthy" if ok else "degraded"
    return {
        "ok": True,
        "server": SERVER_NAME,
        "status": status,
        "checked_at": _now(),
        "postgres": {
            "host": PG_HOST,
            "port": PG_PORT,
            "reachable": ok,
            "probe": "tcp",
            "detail": detail if not ok else "connected",
        },
        "credentials_exposed": False,
    }


def memory_status() -> dict[str, Any]:
    health = memory_health()
    migrations: list[str] = []
    try:
        with db() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT version FROM agentcore.schema_migrations ORDER BY version"
            )
            migrations = [r["version"] for r in cur.fetchall()]
    except Exception as exc:  # noqa: BLE001
        migrations = [f"degraded:{exc.__class__.__name__}"]
    knowledge_status = get_knowledge_memory_port().status().as_dict()
    return {
        "ok": True,
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "status": health["status"],
        "checked_at": _now(),
        "components": {
            "postgres_agent_core": {
                "endpoint": f"{PG_HOST}:{PG_PORT}",
                "reachable": health["postgres"]["reachable"],
                "role": "canonical AgentCore database listener probe",
                "migrations": migrations,
            },
            "gateway_write_path": {
                "note": "Normal durable memory writes are governed through compact tools only; no raw SQL/admin tools exposed.",
            },
            "cognee": knowledge_status,
            "langgraph": {
                "status": "m6_integrated",
                "checkpointer": "langgraph-checkpoint-postgres==3.1.0",
                "checkpoint_tables": "public.checkpoints/checkpoint_blobs/checkpoint_writes",
                "workflow_tables": "agentcore.wf_runs/wf_milestones/wf_macro_steps/wf_micro_steps",
                "capability_profiles": "agentcore.capability_profiles (PostgreSQL-backed M6 leases)",
            },
        },
        "secrets": "never_returned",
    }


def session_close(args: dict[str, Any]) -> dict[str, Any]:
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE agentcore.sessions SET ended_at = now() WHERE id = %s RETURNING id",
            (args["session_id"],),
        )
        row = cur.fetchone()
        conn.commit()
    return {"ok": bool(row), "session_id": args["session_id"]}


def append_event(args: dict[str, Any]) -> dict[str, Any]:
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id AS session_id, s.project_id, si.id AS source_identity_id
            FROM agentcore.sessions s
            JOIN agentcore.source_identities si ON si.session_id = s.id
            WHERE s.id = %s
            ORDER BY si.created_at DESC
            LIMIT 1
            """,
            (args["session_id"],),
        )
        ctx = cur.fetchone()
        if not ctx:
            raise ValueError("unknown session_id")
        set_project(conn, str(ctx["project_id"]))

        artifact_id = None
        large_text = args.get("large_text")
        if large_text:
            data = large_text.encode("utf-8")
            sha = hashlib.sha256(data).hexdigest()
            artifact_dir = HOT_ARTIFACT_ROOT / "sha256" / sha[:2]
            artifact_dir.mkdir(parents=True, exist_ok=True)
            artifact_path = artifact_dir / f"{sha}.txt"
            artifact_path.write_bytes(data)
            cur.execute(
                """
                INSERT INTO agentcore.artifact_objects
                    (project_id, sha256, bytes, storage_uri, mime_type, trust_class, source_identity_id)
                VALUES (%s, %s, %s, %s, 'text/plain', %s, %s)
                ON CONFLICT (project_id, sha256) DO UPDATE SET storage_uri = EXCLUDED.storage_uri
                RETURNING id
                """,
                (
                    ctx["project_id"],
                    sha,
                    len(data),
                    str(artifact_path),
                    args.get("trust_class", "project_verified"),
                    ctx["source_identity_id"],
                ),
            )
            artifact_id = cur.fetchone()["id"]

        payload = redact_payload(args.get("payload") or {})
        cur.execute(
            """
            SELECT agentcore.append_evidence_event(%s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb) AS event_id
            """,
            (
                ctx["project_id"],
                ctx["source_identity_id"],
                args["event_kind"],
                args["idempotency_key"],
                json.dumps(payload),
                artifact_id,
                args.get("trust_class", "project_verified"),
                json.dumps({"tool": "append_event", "server": SERVER_NAME}),
            ),
        )
        event_id = cur.fetchone()["event_id"]
        conn.commit()
    return {
        "ok": True,
        "event_id": str(event_id),
        "artifact_id": str(artifact_id) if artifact_id else None,
    }


def hybrid_retrieval(
    args: dict[str, Any], conn: psycopg.Connection[Any]
) -> list[dict[str, Any]]:
    query = str(args.get("query") or "").strip()
    if not query and not args.get("query_embedding"):
        return []

    project_id = None
    if args.get("project_key"):
        project = get_project(conn, args["project_key"])
        project_id = project["id"]

    limit = max(1, min(int(args.get("limit") or 5), 25))
    methods = get_knowledge_memory_port().enabled_methods(
        requested_list(args, "retrieval_methods")
    )
    trust_classes = requested_list(args, "trust_classes")
    embedding = vector_literal(args.get("query_embedding"))

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source, id, title, text, source_ref, trust_class, version, scope,
                   retrieval_method, score, provenance, metadata
            FROM agentcore.hybrid_retrieve_documents(%s, %s, %s::vector, %s, %s, %s)
            """,
            (project_id, query, embedding, limit, trust_classes, methods),
        )
        return cur.fetchall()


def legacy_docs_search(
    args: dict[str, Any], conn: psycopg.Connection[Any]
) -> list[dict[str, Any]]:
    query = args["query"].lower()
    limit = int(args.get("limit") or 5)
    with conn.cursor() as cur:
        if args.get("project_key"):
            project = get_project(conn, args["project_key"])
            cur.execute(
                """
                SELECT 'summary' AS source, id::text, title, summary_text AS text
                FROM agentcore.context_summaries
                WHERE project_id = %s AND lower(summary_text || ' ' || title) LIKE %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (project["id"], f"%{query}%", limit),
            )
        else:
            cur.execute(
                """
                SELECT 'summary' AS source, id::text, title, summary_text AS text
                FROM agentcore.context_summaries
                WHERE lower(summary_text || ' ' || title) LIKE %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (f"%{query}%", limit),
            )
        return cur.fetchall()


def resolve_context_profile(
    conn: psycopg.Connection[Any], args: dict[str, Any]
) -> tuple[ModelContextProfile, str]:
    requested = str(
        args.get("context_profile") or args.get("budget_name") or "standard-context"
    )
    with conn.cursor() as cur:
        cur.execute(
            "SELECT to_regclass('agentcore.model_context_profiles') IS NOT NULL AS exists"
        )
        profiles_available = bool(cur.fetchone()["exists"])
        if profiles_available:
            cur.execute(
                """
                SELECT p.*
                FROM agentcore.model_context_profiles p
                WHERE p.profile_name = COALESCE(
                    (SELECT a.profile_name
                     FROM agentcore.model_context_profile_aliases a
                     WHERE a.alias_name = %s),
                    %s
                )
                """,
                (requested, requested),
            )
            row = cur.fetchone()
        else:
            row = None
    if row:
        profile = ModelContextProfile.from_mapping(row)
        return profile, profile.profile_name
    if profiles_available:
        if args.get("context_profile"):
            raise ValueError(f"unknown context_profile: {requested}")
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM agentcore.model_context_profiles WHERE profile_name = 'standard-context'"
            )
            fallback = cur.fetchone()
        if not fallback:
            raise ValueError("standard-context profile is missing")
        profile = ModelContextProfile.from_mapping(fallback)
        return profile, profile.profile_name

    # Safe compatibility path while m3.002 is pending deployment. It preserves
    # the old named assembler budget without treating it as a durable-memory cap.
    legacy_budget = (
        requested if requested in {"small", "default", "large"} else "default"
    )
    legacy_limits = {"small": 512, "default": 4096, "large": 16000}
    active_limit = legacy_limits[legacy_budget]
    profile = ModelContextProfile.from_mapping(
        {
            "profile_name": f"pre-m3.002-{legacy_budget}",
            "provider": "agentcore",
            "model_id": "legacy/pre-m3.002",
            "hard_context_limit": active_limit + 1024,
            "safe_active_context_ceiling": active_limit,
            "reserved_output_tokens": 512,
            "reserved_tool_schema_tokens": 128,
            "reserved_tool_result_tokens": 256,
            "safety_reserve_tokens": 128,
            "soft_compaction_threshold_tokens": max(1, int(active_limit * 0.75)),
            "hard_compaction_threshold_tokens": max(2, int(active_limit * 0.95)),
            "retrieval_page_size": 50,
            "tokenizer": "cl100k_base-estimate",
            "last_validated_date": "2026-07-16",
            "validation_source": "pre-m3.002 compatibility only",
        }
    )
    return profile, legacy_budget


def _recovery_filters(
    args: dict[str, Any], project: dict[str, Any]
) -> tuple[str, list[Any], dict[str, Any]]:
    mode = str(args.get("recovery_mode") or "complete_project_chronology")
    clauses = ["e.project_id = %s"]
    params: list[Any] = [project["id"]]
    scope: dict[str, Any] = {
        "project_id": str(project["id"]),
        "project_key": project["project_key"],
        "mode": mode,
    }

    if not args.get("include_quarantined"):
        clauses.append("e.trust_class::text <> ALL(%s)")
        params.append(list(EXCLUDED_NORMAL_TRUST_CLASSES))
    else:
        scope["include_quarantined"] = True

    if mode == "session_replay":
        session_id = args.get("session_id")
        if not session_id:
            raise ValueError("session_replay requires session_id")
        clauses.append("si.session_id = %s")
        params.append(session_id)
        scope["session_id"] = str(session_id)
    elif mode in {"current_milestone", "milestone_replay"}:
        milestone = args.get("milestone") or project.get("current_milestone")
        if not milestone:
            raise ValueError(
                f"{mode} requires a milestone or project current_milestone"
            )
        clauses.append(
            "COALESCE(e.payload->>'milestone', e.provenance->>'milestone') = %s"
        )
        params.append(milestone)
        scope["milestone"] = str(milestone)
    elif mode == "time_range_replay":
        if args.get("start_at"):
            clauses.append("e.accepted_at >= %s::timestamptz")
            params.append(args["start_at"])
            scope["start_at"] = str(args["start_at"])
        if args.get("end_at"):
            clauses.append("e.accepted_at <= %s::timestamptz")
            params.append(args["end_at"])
            scope["end_at"] = str(args["end_at"])
        if not args.get("start_at") and not args.get("end_at"):
            raise ValueError("time_range_replay requires start_at and/or end_at")
    elif mode == "decision_history":
        clauses.append("e.event_kind = 'decision'")
    elif mode == "failure_fix_reconstruction":
        clauses.append(
            "(e.event_kind IN ('test_result','tool_event','decision','state_transition') "
            "AND e.payload::text ~* '(error|fail|fix|rollback|recover)')"
        )
    elif mode not in {"current_state", "complete_project_chronology"}:
        raise ValueError(f"unsupported recovery mode: {mode}")

    return " AND ".join(clauses), params, scope


def retrieve_chronology_page(
    conn: psycopg.Connection[Any],
    project: dict[str, Any],
    profile: ModelContextProfile,
    args: dict[str, Any],
) -> dict[str, Any]:
    where_sql, base_params, scope = _recovery_filters(args, project)
    mode = str(scope["mode"])
    scope_digest = recovery_scope_hash(scope)
    cursor_state: dict[str, Any] | None = None
    if args.get("continuation_cursor"):
        cursor_state = decode_cursor(str(args["continuation_cursor"]))
        if (
            cursor_state.get("project_id") != str(project["id"])
            or cursor_state.get("mode") != mode
            or cursor_state.get("scope_hash") != scope_digest
        ):
            raise ValueError("continuation cursor scope mismatch")

    with conn.cursor() as cur:
        if cursor_state:
            window_end_at = cursor_state["window_end_at"]
            window_end_id = cursor_state["window_end_id"]
        else:
            cur.execute(
                f"""
                SELECT e.accepted_at, e.id::text
                FROM agentcore.evidence_events e
                JOIN agentcore.source_identities si ON si.id = e.source_identity_id
                WHERE {where_sql}
                ORDER BY e.accepted_at DESC, e.id DESC
                LIMIT 1
                """,
                base_params,
            )
            boundary = cur.fetchone()
            window_end_at = boundary["accepted_at"] if boundary else None
            window_end_id = boundary["id"] if boundary else None

        page_where = where_sql
        page_params = list(base_params)
        if window_end_at is not None:
            page_where += " AND (e.accepted_at, e.id) <= (%s::timestamptz, %s::uuid)"
            page_params.extend([window_end_at, window_end_id])
        if cursor_state:
            page_where += " AND (e.accepted_at, e.id) > (%s::timestamptz, %s::uuid)"
            page_params.extend([cursor_state["after_at"], cursor_state["after_id"]])

        cur.execute(
            f"""
            SELECT count(*) AS remaining
            FROM agentcore.evidence_events e
            JOIN agentcore.source_identities si ON si.id = e.source_identity_id
            WHERE {page_where}
            """,
            page_params,
        )
        remaining = int(cur.fetchone()["remaining"])
        requested_page_size = int(args.get("page_size") or profile.retrieval_page_size)
        page_size = max(1, min(requested_page_size, profile.retrieval_page_size))
        cur.execute(
            f"""
            SELECT e.id::text, e.event_kind::text, e.payload, e.artifact_id::text,
                   e.trust_class::text, e.provenance, e.occurred_at, e.accepted_at,
                   si.session_id::text,
                   a.sha256 AS artifact_sha256,
                   COALESCE(loc.storage_uri, a.storage_uri) AS artifact_storage_uri
            FROM agentcore.evidence_events e
            JOIN agentcore.source_identities si ON si.id = e.source_identity_id
            LEFT JOIN agentcore.artifact_objects a ON a.id = e.artifact_id
            LEFT JOIN LATERAL (
                SELECT l.storage_uri
                FROM agentcore.artifact_locations l
                WHERE l.artifact_id = a.id AND l.is_active
                ORDER BY CASE l.storage_tier WHEN 'cold_e' THEN 0 ELSE 1 END, l.created_at DESC
                LIMIT 1
            ) loc ON true
            WHERE {page_where}
            ORDER BY e.accepted_at, e.id
            LIMIT %s
            """,
            [*page_params, page_size],
        )
        candidates = cur.fetchall()

    items: list[dict[str, Any]] = []
    used_tokens = 0
    for row in candidates:
        item = {
            **row,
            "source_id": row["id"],
            "content_sha256": content_sha256(row["payload"]),
            "exact_expansion_reference": {
                "tool": "expand_source",
                "project_key": project["project_key"],
                "event_id": row["id"],
            },
        }
        item_tokens = estimate_tokens(item)
        if used_tokens + item_tokens > profile.active_packet_limit:
            if items:
                break
            item = {
                key: value
                for key, value in item.items()
                if key not in {"payload", "provenance"}
            }
            item["payload_omitted_from_page"] = True
            item["payload_token_estimate"] = item_tokens
            item_tokens = estimate_tokens(item)
            if item_tokens > profile.active_packet_limit:
                raise ValueError("recovery item metadata exceeds active packet limit")
            items.append(item)
            used_tokens += item_tokens
            break
        items.append(item)
        used_tokens += item_tokens

    omitted = max(0, remaining - len(items))
    next_cursor = None
    if omitted and items and window_end_at is not None:
        last = items[-1]
        next_cursor = encode_cursor(
            {
                "project_id": str(project["id"]),
                "mode": mode,
                "scope_hash": scope_digest,
                "after_at": str(last["accepted_at"]),
                "after_id": last["id"],
                "window_end_at": str(window_end_at),
                "window_end_id": str(window_end_id),
            }
        )

    page = {
        "mode": mode,
        "scope": scope,
        "items": items,
        "source_ids": [item["source_id"] for item in items],
        "trust_classifications": [item["trust_class"] for item in items],
        "content_hashes": [item["content_sha256"] for item in items],
        "exact_expansion_references": [
            item["exact_expansion_reference"] for item in items
        ],
        "continuation_cursor": next_cursor,
        "omitted_item_count": omitted,
        "page_token_count": used_tokens,
        "chronological_boundaries": {
            "page_start": str(items[0]["accepted_at"]) if items else None,
            "page_end": str(items[-1]["accepted_at"]) if items else None,
            "window_end": str(window_end_at) if window_end_at else None,
        },
    }

    if args.get("record_recovery", True):
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agentcore.recovery_operations (
                        project_id, session_id, recovery_mode, context_profile_name,
                        request_scope, chronological_start, chronological_end,
                        continuation_digest, source_event_ids, omitted_item_count, result_sha256
                    ) VALUES (
                        %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::uuid[], %s, %s
                    )
                    """,
                    (
                        project["id"],
                        args.get("session_id"),
                        mode,
                        profile.profile_name,
                        json.dumps(scope),
                        items[0]["accepted_at"] if items else None,
                        items[-1]["accepted_at"] if items else None,
                        content_sha256(next_cursor) if next_cursor else None,
                        page["source_ids"],
                        omitted,
                        content_sha256(page),
                    ),
                )
                conn.commit()
        except psycopg.errors.UndefinedTable:
            conn.rollback()

    return page


def retrieve_context(args: dict[str, Any]) -> dict[str, Any]:
    with db() as conn, conn.cursor() as cur:
        project = get_project(conn, args["project_key"])
        set_project(conn, str(project["id"]))
        profile, assembler_budget = resolve_context_profile(conn, args)
        if args.get("recovery_mode"):
            page = retrieve_chronology_page(conn, project, profile, args)
            return {
                "ok": True,
                "project_key": args["project_key"],
                "context_profile": profile.as_dict(),
                "recovery": page,
            }
        cur.execute(
            """
            SELECT item_type, item_id::text, level::text, bucket::text, body, token_count, importance, cumulative_tokens
            FROM agentcore.assemble_context_window(%s, %s)
            """,
            (project["id"], assembler_budget),
        )
        items = cur.fetchall()
        retrieval_results = hybrid_retrieval(args, conn)
    return {
        "ok": True,
        "project_key": args["project_key"],
        "budget_name": args.get("budget_name"),
        "context_profile": profile.as_dict(),
        "items": items,
        "retrieval_results": retrieval_results,
        "durable_memory_limit": None,
        "durable_memory_contract": "effectively_unbounded_by_model_token_limits",
    }


def get_project_capability_profile(project_id: str) -> dict[str, Any]:
    """Return the active capability profile for a project from PostgreSQL (M6 wiring).

    The profile reflects which tools are active, JIT-leased, or operator-only for
    this specific project. This is the agentcore-gateway path: startup_context
    exposes the profile so callers know effective tool availability without needing
    direct database access.
    """
    try:
        with db() as conn, conn.cursor() as cur:
            # Expire any timed-out JIT leases first
            cur.execute(
                "SELECT agentcore.expire_wf_jit_leases(%s::uuid) AS expired",
                (project_id,),
            )
            conn.commit()
            cur.execute(
                """
                SELECT tool_name, tool_state::text, requires_operator_approval
                FROM agentcore.capability_profiles
                WHERE project_id = %s::uuid
                ORDER BY tool_name
                """,
                (project_id,),
            )
            rows = cur.fetchall()
    except Exception as exc:
        return {"available": False, "error": str(exc.__class__.__name__), "tools": []}

    active, jit, op_only = [], [], []
    for r in rows:
        state = r["tool_state"]
        if state in ("core_active", "milestone_active"):
            active.append(r["tool_name"])
        elif state == "jit_leased":
            jit.append(r["tool_name"])
        elif state == "operator_only":
            op_only.append(r["tool_name"])

    return {
        "available": True,
        "project_id": project_id,
        "active_tools": active,
        "jit_leased_tools": jit,
        "operator_only_tools": op_only,
        "effective_tools": active + jit,  # what the project may use right now
    }


def startup_context(args: dict[str, Any]) -> dict[str, Any]:
    context = retrieve_context(args)
    # M6: include capability profile so the gateway path reflects effective tool availability
    capability_profile: dict[str, Any] = {
        "available": False,
        "note": "no project_id resolved",
    }
    try:
        with db() as conn:
            project = get_project(conn, args["project_key"])
            capability_profile = get_project_capability_profile(str(project["id"]))
    except Exception:
        pass
    return {
        **context,
        "authority": [
            "PROJECT_ANCHOR.md",
            "DOC_AUTHORITY.md",
            "BLUEPRINT.md",
            "CONTEXT_BLOCK.md",
            "docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md",
        ],
        "m4_status": "agentcore-memory compact surface active",
        "m6_capability_profile": capability_profile,
    }


def _artifact_expansion(
    conn: psycopg.Connection[Any],
    project: dict[str, Any],
    artifact_id: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.id::text, a.sha256, a.bytes, a.mime_type, a.trust_class::text,
                   COALESCE(l.storage_uri, a.storage_uri) AS storage_uri,
                   l.storage_tier::text
            FROM agentcore.artifact_objects a
            LEFT JOIN LATERAL (
                SELECT storage_uri, storage_tier
                FROM agentcore.artifact_locations
                WHERE artifact_id = a.id AND is_active
                ORDER BY CASE storage_tier WHEN 'cold_e' THEN 0 ELSE 1 END, created_at DESC
                LIMIT 1
            ) l ON true
            WHERE a.id = %s AND a.project_id = %s
            """,
            (artifact_id, project["id"]),
        )
        artifact = cur.fetchone()
    if not artifact:
        return {"ok": False, "error": "artifact not found in project scope"}

    offset = int(args.get("artifact_offset") or 0)
    if args.get("continuation_cursor"):
        state = decode_cursor(str(args["continuation_cursor"]))
        if (
            state.get("project_id") != str(project["id"])
            or state.get("artifact_id") != artifact_id
            or state.get("sha256") != artifact["sha256"]
        ):
            raise ValueError("artifact continuation cursor scope mismatch")
        offset = int(state["next_offset"])
    max_bytes = max(1, min(int(args.get("max_bytes") or 65536), 1048576))
    path = Path(str(artifact["storage_uri"]))
    response: dict[str, Any] = {
        "ok": True,
        "project_key": project["project_key"],
        "artifact": artifact,
        "content_available": path.is_file(),
        "byte_range": {"start": offset, "end": offset, "total": int(artifact["bytes"])},
        "continuation_cursor": None,
    }
    if not path.is_file():
        response["error"] = "artifact payload unavailable at registered active location"
        return response

    with path.open("rb") as source:
        actual_sha = hashlib.file_digest(source, "sha256").hexdigest()
        source.seek(offset)
        chunk = source.read(max_bytes)
    if actual_sha.lower() != str(artifact["sha256"]).lower():
        raise ValueError("artifact content hash mismatch")
    end = offset + len(chunk)
    response["content_sha256_verified"] = True
    response["byte_range"] = {
        "start": offset,
        "end": end,
        "total": int(artifact["bytes"]),
    }
    try:
        response["content"] = chunk.decode("utf-8")
        response["content_encoding"] = "utf-8"
    except UnicodeDecodeError:
        response["content"] = base64.b64encode(chunk).decode("ascii")
        response["content_encoding"] = "base64"
    if end < int(artifact["bytes"]):
        response["continuation_cursor"] = encode_cursor(
            {
                "project_id": str(project["id"]),
                "artifact_id": artifact_id,
                "sha256": artifact["sha256"],
                "next_offset": end,
            }
        )
        response["omitted_byte_count"] = int(artifact["bytes"]) - end
    else:
        response["omitted_byte_count"] = 0
    return response


def expand_source(args: dict[str, Any]) -> dict[str, Any]:
    with db() as conn, conn.cursor() as cur:
        project = get_project(conn, args["project_key"])
        set_project(conn, str(project["id"]))
        if args.get("summary_id"):
            page_size = max(1, min(int(args.get("page_size") or 100), 1000))
            after_event_id = None
            if args.get("continuation_cursor"):
                state = decode_cursor(str(args["continuation_cursor"]))
                if (
                    state.get("project_id") != str(project["id"])
                    or state.get("summary_id") != args["summary_id"]
                ):
                    raise ValueError("summary continuation cursor scope mismatch")
                after_event_id = state["after_event_id"]
            cur.execute(
                """
                SELECT count(*) AS source_count
                FROM agentcore.context_source_edges edge
                JOIN agentcore.context_summaries s ON s.id = edge.summary_id
                WHERE edge.summary_id = %s AND s.project_id = %s
                  AND (%s::uuid IS NULL OR edge.source_event_id > %s::uuid)
                """,
                (args["summary_id"], project["id"], after_event_id, after_event_id),
            )
            remaining = int(cur.fetchone()["source_count"])
            cur.execute(
                """
                SELECT source_event_id::text, event_kind::text, payload, artifact_id::text,
                       storage_uri, trust_class::text, provenance
                FROM agentcore.expand_summary(%s)
                WHERE (%s::uuid IS NULL OR source_event_id > %s::uuid)
                ORDER BY source_event_id
                LIMIT %s
                """,
                (args["summary_id"], after_event_id, after_event_id, page_size),
            )
            sources = cur.fetchall()
            for source in sources:
                source["source_id"] = source["source_event_id"]
                source["content_sha256"] = content_sha256(source["payload"])
                source["exact_expansion_reference"] = {
                    "tool": "expand_source",
                    "project_key": project["project_key"],
                    "event_id": source["source_event_id"],
                }
            omitted = max(0, remaining - len(sources))
            next_cursor = None
            if omitted and sources:
                next_cursor = encode_cursor(
                    {
                        "project_id": str(project["id"]),
                        "summary_id": args["summary_id"],
                        "after_event_id": sources[-1]["source_event_id"],
                    }
                )
            return {
                "ok": True,
                "project_key": project["project_key"],
                "summary_id": args["summary_id"],
                "sources": sources,
                "source_ids": [source["source_event_id"] for source in sources],
                "continuation_cursor": next_cursor,
                "omitted_item_count": omitted,
            }
        if args.get("event_id"):
            cur.execute(
                """
                SELECT id::text, event_kind::text, payload, artifact_id::text,
                       trust_class::text, provenance, occurred_at, accepted_at
                FROM agentcore.evidence_events
                WHERE id = %s AND project_id = %s
                """,
                (args["event_id"], project["id"]),
            )
            event = cur.fetchone()
            if not event:
                return {"ok": False, "error": "event not found in project scope"}
            event["source_id"] = event["id"]
            event["content_sha256"] = content_sha256(event["payload"])
            event["exact_expansion_reference"] = {
                "tool": "expand_source",
                "project_key": project["project_key"],
                "event_id": event["id"],
            }
            response: dict[str, Any] = {
                "ok": True,
                "project_key": project["project_key"],
                "event": event,
            }
            if event.get("artifact_id"):
                response["artifact_expansion_reference"] = {
                    "tool": "expand_source",
                    "project_key": project["project_key"],
                    "artifact_id": event["artifact_id"],
                }
            return response
        if args.get("artifact_id"):
            return _artifact_expansion(conn, project, args["artifact_id"], args)
    return {"ok": False, "error": "provide summary_id, event_id, or artifact_id"}


def propose_fact(args: dict[str, Any]) -> dict[str, Any]:
    with db() as conn, conn.cursor() as cur:
        project = get_project(conn, args["project_key"])
        set_project(conn, str(project["id"]))
        cur.execute(
            "SELECT agentcore.propose_fact_review(%s, %s, %s::jsonb, %s, %s, %s::jsonb) AS proposal_id",
            (
                project["id"],
                args["fact_key"],
                json.dumps(args["proposed_value"]),
                args.get("contradicts_event_id"),
                args.get("trust_class", "raw_untrusted"),
                json.dumps({"tool": "propose_fact", "server": SERVER_NAME}),
            ),
        )
        proposal_id = cur.fetchone()["proposal_id"]
        conn.commit()
    return {"ok": True, "proposal_id": str(proposal_id), "status": "proposed"}


def build_handoff(args: dict[str, Any]) -> dict[str, Any]:
    active_args = {
        "project_key": args["project_key"],
        "context_profile": args.get("context_profile") or "standard-context",
    }
    context = retrieve_context(active_args)
    recovery_args = {
        **args,
        "recovery_mode": args.get("recovery_mode") or "current_state",
        "record_recovery": args.get("record_recovery", True),
    }
    recovery = retrieve_context(recovery_args)
    with db() as conn, conn.cursor() as cur:
        project = get_project(conn, args["project_key"])
        cur.execute(
            """
            SELECT p.project_key, p.project_name, p.current_milestone, p.root_path,
                   r.repo_key, r.canonical_path, r.remote_url,
                   w.worktree_path, w.branch_name, w.head_commit
            FROM agentcore.projects p
            LEFT JOIN agentcore.repositories r ON r.id = p.repository_id
            LEFT JOIN agentcore.worktrees w ON w.id = p.primary_worktree_id
            WHERE p.id = %s
            """,
            (project["id"],),
        )
        identity = cur.fetchone()
        cur.execute(
            """
            SELECT kind::text, target_path, revision, content_sha256, source_revision,
                   generated_at, previous_revision_id::text
            FROM agentcore.projection_revisions
            WHERE (project_id = %s OR project_id IS NULL) AND is_current
            ORDER BY kind, generated_at DESC
            """,
            (project["id"],),
        )
        projections = cur.fetchall()
        try:
            cur.execute(
                """
                SELECT snapshot_kind, milestone, release_ref, commit_sha, branch_name,
                       changed_file_manifest, source_hashes, patch_artifact_id::text,
                       archive_artifact_id::text, created_at
                FROM agentcore.project_snapshots
                WHERE project_id = %s
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (project["id"],),
            )
            snapshots = cur.fetchall()
        except psycopg.errors.UndefinedTable:
            conn.rollback()
            snapshots = []
    return {
        "ok": True,
        "project_key": args["project_key"],
        "identity": identity,
        "context_profile": context.get("context_profile"),
        "active_context": context.get("items", []),
        "recovery": recovery.get("recovery"),
        "current_projections": projections,
        "governed_snapshots": snapshots,
        "continuation_cursor": (recovery.get("recovery") or {}).get(
            "continuation_cursor"
        ),
    }


def docs_search(args: dict[str, Any]) -> dict[str, Any]:
    with db() as conn:
        try:
            rows = hybrid_retrieval(args, conn)
        except Exception as exc:  # noqa: BLE001 - preserve degraded M4 behavior if M5 SQL is absent.
            _log(f"hybrid retrieval degraded: {exc.__class__.__name__}")
            rows = legacy_docs_search(args, conn)
    return {
        "ok": True,
        "query": args["query"],
        "results": rows,
        "external_docs_note": "Use arabold-docs for dependency/API docs.",
    }


def call_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    arguments = arguments or {}
    if name == "memory_status":
        return memory_status()
    if name == "session_open":
        return session_open(arguments)
    if name == "session_close":
        return session_close(arguments)
    if name == "append_event":
        return append_event(arguments)
    if name == "retrieve_context":
        return retrieve_context(arguments)
    if name == "startup_context":
        return startup_context(arguments)
    if name == "expand_source":
        return expand_source(arguments)
    if name == "propose_fact":
        return propose_fact(arguments)
    if name == "build_handoff":
        return build_handoff(arguments)
    if name == "docs_search":
        return docs_search(arguments)
    return {"ok": False, "error": f"Unknown tool: {name}"}


def handle_request(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method")
    req_id = msg.get("id")
    params = msg.get("params") or {}

    if req_id is None and method and str(method).startswith("notifications/"):
        return None

    try:
        if method == "initialize":
            requested = str(
                (params or {}).get("protocolVersion") or DEFAULT_PROTOCOL_VERSION
            )
            version = (
                requested
                if requested in SUPPORTED_PROTOCOL_VERSIONS
                else DEFAULT_PROTOCOL_VERSION
            )
            result = {
                "protocolVersion": version,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": tool_defs()}
        elif method == "tools/call":
            payload = call_tool(params.get("name"), params.get("arguments") or {})
            payload = to_jsonable(payload)
            result = {
                "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
                "structuredContent": payload,
                "isError": not payload.get("ok", True),
            }
        elif method in ("resources/list", "prompts/list"):
            result = {method.split("/")[0]: []}
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    except Exception:  # noqa: BLE001
        _log(traceback.format_exc())
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": "internal error (sanitized)"},
        }


def main() -> int:
    _log("starting stdio NDJSON server")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue
        response = handle_request(msg)
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
