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

SERVER_NAME = "agentcore-memory"
SERVER_VERSION = "0.5.0"
# Bifrost currently initializes with 2025-06-18; accept and echo it.
SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}
DEFAULT_PROTOCOL_VERSION = "2025-06-18"
PG_HOST = "127.0.0.1"
PG_PORT = 55433
PG_DATABASE = "agent_core"
PG_USER = "postgres"
PG_PASSWORD_ENV = "AGENT_CORE_POSTGRES_PASSWORD"
REPO_PATH = Path(r"D:\github\agentcore-control-plane")
HOT_ARTIFACT_ROOT = Path(r"H:\AgentRuntime\agentcore-memory\artifacts")


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
    return [
        {
            "name": "memory_status",
            "description": "Return sanitized memory/gateway status summary without secrets.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
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
                "properties": {"project_key": text_schema, "budget_name": text_schema},
                "required": ["project_key"],
                "additionalProperties": False,
            },
        },
        {
            "name": "expand_source",
            "description": "Expand a summary, event, or artifact reference back to exact source evidence.",
            "inputSchema": {
                "type": "object",
                "properties": {"summary_id": text_schema, "event_id": text_schema, "artifact_id": text_schema},
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
                "properties": {"project_key": text_schema},
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
        cur.execute("SELECT * FROM agentcore.projects WHERE project_key = %s", (project_key,))
        row = cur.fetchone()
    if not row:
        raise ValueError(f"unknown project_key: {project_key}")
    return row


def set_project(conn: psycopg.Connection[Any], project_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('agentcore.current_project_id', %s, true)", (project_id,))


def session_open(args: dict[str, Any]) -> dict[str, Any]:
    project_key = args["project_key"]
    project_name = args.get("project_name") or project_key
    client_key = args.get("client_key") or "unknown-client"
    agent_key = args.get("agent_key") or "unknown-agent"
    session_key = args.get("session_key") or f"{project_key}:{client_key}:{agent_key}:{_now()}"
    repo_key = "agentcore-control-plane"
    repo_path = str(REPO_PATH)

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            WITH repo AS (
              INSERT INTO agentcore.repositories (repo_key, canonical_path, remote_url)
              VALUES (%s, %s, 'https://github.com/ynotfins/agentcore-control-plane.git')
              ON CONFLICT (canonical_path) DO UPDATE SET remote_url = EXCLUDED.remote_url
              RETURNING id
            ),
            wt AS (
              INSERT INTO agentcore.worktrees (repository_id, worktree_path, branch_name)
              SELECT id, %s, 'task/authority-reconciliation' FROM repo
              ON CONFLICT (worktree_path) DO UPDATE SET branch_name = EXCLUDED.branch_name
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
              INSERT INTO agentcore.agents (agent_key, display_name)
              VALUES (%s, %s)
              ON CONFLICT (agent_key) DO UPDATE SET display_name = EXCLUDED.display_name
              RETURNING id
            ),
            session AS (
              INSERT INTO agentcore.sessions (project_id, client_id, agent_id, session_key)
              SELECT project.id, client.id, agent.id, %s FROM project, client, agent
              ON CONFLICT (session_key) DO UPDATE SET ended_at = NULL
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
                repo_path,
                project_key,
                project_name,
                repo_path,
                client_key,
                client_key,
                agent_key,
                agent_key,
                session_key,
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
            cur.execute("SELECT version FROM agentcore.schema_migrations ORDER BY version")
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
    return {"ok": True, "event_id": str(event_id), "artifact_id": str(artifact_id) if artifact_id else None}


def hybrid_retrieval(args: dict[str, Any], conn: psycopg.Connection[Any]) -> list[dict[str, Any]]:
    query = str(args.get("query") or "").strip()
    if not query and not args.get("query_embedding"):
        return []

    project_id = None
    if args.get("project_key"):
        project = get_project(conn, args["project_key"])
        project_id = project["id"]

    limit = max(1, min(int(args.get("limit") or 5), 25))
    methods = get_knowledge_memory_port().enabled_methods(requested_list(args, "retrieval_methods"))
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


def legacy_docs_search(args: dict[str, Any], conn: psycopg.Connection[Any]) -> list[dict[str, Any]]:
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


def retrieve_context(args: dict[str, Any]) -> dict[str, Any]:
    budget = args.get("budget_name") or "default"
    with db() as conn, conn.cursor() as cur:
        project = get_project(conn, args["project_key"])
        set_project(conn, str(project["id"]))
        cur.execute(
            """
            SELECT item_type, item_id::text, level::text, bucket::text, body, token_count, importance, cumulative_tokens
            FROM agentcore.assemble_context_window(%s, %s)
            """,
            (project["id"], budget),
        )
        items = cur.fetchall()
        retrieval_results = hybrid_retrieval(args, conn)
    return {
        "ok": True,
        "project_key": args["project_key"],
        "budget_name": budget,
        "items": items,
        "retrieval_results": retrieval_results,
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
            cur.execute("SELECT agentcore.expire_wf_jit_leases(%s::uuid) AS expired", (project_id,))
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
    capability_profile: dict[str, Any] = {"available": False, "note": "no project_id resolved"}
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


def expand_source(args: dict[str, Any]) -> dict[str, Any]:
    with db() as conn, conn.cursor() as cur:
        if args.get("summary_id"):
            cur.execute(
                """
                SELECT source_event_id::text, event_kind::text, payload, artifact_id::text, storage_uri, trust_class::text, provenance
                FROM agentcore.expand_summary(%s)
                """,
                (args["summary_id"],),
            )
            return {"ok": True, "summary_id": args["summary_id"], "sources": cur.fetchall()}
        if args.get("event_id"):
            cur.execute(
                """
                SELECT id::text, event_kind::text, payload, artifact_id::text, trust_class::text, provenance
                FROM agentcore.evidence_events WHERE id = %s
                """,
                (args["event_id"],),
            )
            return {"ok": True, "event": cur.fetchone()}
        if args.get("artifact_id"):
            cur.execute(
                """
                SELECT a.id::text, a.sha256, a.bytes, coalesce(l.storage_uri, a.storage_uri) AS storage_uri
                FROM agentcore.artifact_objects a
                LEFT JOIN LATERAL (
                    SELECT storage_uri FROM agentcore.artifact_locations
                    WHERE artifact_id = a.id AND is_active
                    ORDER BY CASE storage_tier WHEN 'cold_e' THEN 0 ELSE 1 END, created_at DESC
                    LIMIT 1
                ) l ON true
                WHERE a.id = %s
                """,
                (args["artifact_id"],),
            )
            return {"ok": True, "artifact": cur.fetchone()}
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
    context = retrieve_context({"project_key": args["project_key"], "budget_name": "default"})
    with db() as conn, conn.cursor() as cur:
        project = get_project(conn, args["project_key"])
        cur.execute(
            """
            SELECT event_kind::text, payload, accepted_at
            FROM agentcore.evidence_events
            WHERE project_id = %s
            ORDER BY accepted_at DESC
            LIMIT 10
            """,
            (project["id"],),
        )
        recent = cur.fetchall()
    return {"ok": True, "project_key": args["project_key"], "context": context["items"], "recent_events": recent}


def docs_search(args: dict[str, Any]) -> dict[str, Any]:
    with db() as conn, conn.cursor() as cur:
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
            requested = str((params or {}).get("protocolVersion") or DEFAULT_PROTOCOL_VERSION)
            version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION
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
