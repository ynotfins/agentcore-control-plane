"""Resume semantics and idempotency tests for agentcore-memory.

Authority: BLUEPRINT.md M2/M4; task "harden continuous context durability" 2026-07-17.
Target: PostgreSQL 18 agent_core 127.0.0.1:55433.

Tests prove (per §4 of the hardening spec):
  1. same project + same task + new chat resumes correctly via session_key
  2. same project + new task creates a separate session (distinct session_key)
  3. Cursor and Codex sessions remain distinct (different client_key)
  4. both Cursor and Codex contribute to one coherent project chronology
  5. Project A cannot read Project B events
  6. duplicate prompt retries produce one canonical event (idempotency)

These are UNIT / DETERMINISTIC FIXTURE tests — no live network required beyond
a real PostgreSQL 18 connection on 127.0.0.1:55433.  Skip gracefully when the
database is unreachable so CI on machines without the database does not fail.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from contextlib import contextmanager
from typing import Any, Generator

import pytest

# ---------------------------------------------------------------------------
# Database helper (minimal, no ORM dependency)
# ---------------------------------------------------------------------------

PG_HOST = os.environ.get("AGENTCORE_PG_HOST", "127.0.0.1")
PG_PORT = int(os.environ.get("AGENTCORE_PG_PORT", "55433"))
PG_DATABASE = os.environ.get("AGENTCORE_PG_DATABASE", "agent_core")
PG_USER = os.environ.get("AGENTCORE_PG_USER", "postgres")
PG_PASSWORD_ENV = "AGENT_CORE_POSTGRES_PASSWORD"

_PSYCOPG_AVAILABLE = False
try:
    import psycopg
    from psycopg.rows import dict_row
    _PSYCOPG_AVAILABLE = True
except ImportError:
    pass

_DB_REACHABLE: bool | None = None


def _check_db_reachable() -> bool:
    global _DB_REACHABLE
    if _DB_REACHABLE is not None:
        return _DB_REACHABLE
    if not _PSYCOPG_AVAILABLE:
        _DB_REACHABLE = False
        return False
    import socket
    try:
        with socket.create_connection((PG_HOST, PG_PORT), timeout=1.5):
            _DB_REACHABLE = True
    except OSError:
        _DB_REACHABLE = False
    return _DB_REACHABLE


def _conn() -> "psycopg.Connection[Any]":
    password = os.environ.get(PG_PASSWORD_ENV)
    if not password:
        pytest.skip(f"env var {PG_PASSWORD_ENV} not set")
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DATABASE, user=PG_USER,
        password=password, sslmode="require", row_factory=dict_row,
    )


def db_available(f):
    """Decorator that skips the test when the database is unreachable."""
    def wrapper(*args, **kwargs):
        if not _check_db_reachable():
            pytest.skip("PostgreSQL 18 not reachable — skipping live DB test")
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


# ---------------------------------------------------------------------------
# Helpers to exercise the server module directly (without MCP wire)
# ---------------------------------------------------------------------------

# Add script path so we can import the server module
_SCRIPT_DIR = os.path.join(
    os.path.dirname(__file__), "..", ".."
)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

def _open_session(
    project_key: str,
    client_key: str,
    agent_key: str,
    session_key: str,
    *,
    project_name: str | None = None,
    repo_path: str = "D:\\github\\agentcore-control-plane",
    branch_name: str = "main",
) -> dict[str, Any]:
    """Call session_open through the server module."""
    from agentcore_memory import server  # noqa: PLC0415
    return server.session_open({
        "project_key": project_key,
        "project_name": project_name or project_key,
        "client_key": client_key,
        "agent_key": agent_key,
        "session_key": session_key,
        "canonical_repo_path": repo_path,
        "worktree_path": repo_path,
        "repo_key": "agentcore-control-plane",
        "branch_name": branch_name,
        "context_profile": "standard-context",
    })


def _append(session_id: str, idem_key: str, payload: dict) -> dict[str, Any]:
    from agentcore_memory import server  # noqa: PLC0415
    return server.append_event({
        "session_id": session_id,
        "event_kind": "prompt",
        "idempotency_key": idem_key,
        "payload": payload,
    })


def _close(session_id: str) -> dict[str, Any]:
    from agentcore_memory import server  # noqa: PLC0415
    return server.session_close({"session_id": session_id})


def _retrieve(project_key: str, session_id: str) -> dict[str, Any]:
    from agentcore_memory import server  # noqa: PLC0415
    return server.retrieve_context({
        "project_key": project_key,
        "recovery_mode": "session_replay",
        "session_id": session_id,
        "record_recovery": False,
    })


# ---------------------------------------------------------------------------
# Fixture: isolated test project keys so parallel test runs don't collide
# ---------------------------------------------------------------------------

@pytest.fixture()
def run_id() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture()
def project_a(run_id: str) -> str:
    return f"test-resume-{run_id}-project-a"


@pytest.fixture()
def project_b(run_id: str) -> str:
    return f"test-resume-{run_id}-project-b"


# ---------------------------------------------------------------------------
# Test 1: same project + same task + new chat resumes correctly
# ---------------------------------------------------------------------------

@db_available
def test_same_task_resume(project_a: str, run_id: str):
    """A second open() with the same session_key reopens the session cleanly."""
    client = f"cursor-{run_id}"
    agent = f"agent-{run_id}"
    sk = f"{project_a}:{client}:{agent}:task-alpha"

    # First open — create the session
    r1 = _open_session(project_a, client, agent, sk)
    assert r1["ok"], f"first open failed: {r1}"
    session_id = str(r1["session_id"])

    # Append an event to establish chronology
    ev1 = _append(session_id, f"{sk}:prompt-1", {"text": "initial prompt"})
    assert ev1["ok"]
    event_id = ev1["event_id"]

    # Close simulating a clean shutdown
    _close(session_id)

    # Second open with the SAME session_key — must resume (same session_id returned)
    r2 = _open_session(project_a, client, agent, sk)
    assert r2["ok"], f"second open failed: {r2}"
    assert str(r2["session_id"]) == session_id, (
        f"Resume did not return the original session_id: "
        f"expected {session_id}, got {r2['session_id']}"
    )

    # Previously appended event is retrievable
    ctx = _retrieve(project_a, session_id)
    assert ctx["ok"]
    ids = [item["id"] for item in ctx.get("recovery", {}).get("items", [])]
    assert event_id in ids, f"event {event_id} not found in resumed session chronology"


# ---------------------------------------------------------------------------
# Test 2: same project + new task creates a separate session
# ---------------------------------------------------------------------------

@db_available
def test_new_task_new_session(project_a: str, run_id: str):
    """A new session_key creates a distinct session; both share one project chronology."""
    client = f"cursor-{run_id}"
    agent = f"agent-{run_id}"
    sk_task1 = f"{project_a}:{client}:{agent}:task-one"
    sk_task2 = f"{project_a}:{client}:{agent}:task-two"

    r1 = _open_session(project_a, client, agent, sk_task1)
    r2 = _open_session(project_a, client, agent, sk_task2)
    assert r1["ok"] and r2["ok"]

    sid1 = str(r1["session_id"])
    sid2 = str(r2["session_id"])
    assert sid1 != sid2, "New task must produce a distinct session_id"

    # Both resolve to the same project
    assert str(r1["project_id"]) == str(r2["project_id"]), (
        "Both tasks must resolve to the same project_id"
    )


# ---------------------------------------------------------------------------
# Test 3: Cursor and Codex sessions remain distinct
# ---------------------------------------------------------------------------

@db_available
def test_cursor_codex_distinct_sessions(project_a: str, run_id: str):
    """Cursor and Codex get separate sessions (different client_key)."""
    sk_cursor = f"{project_a}:cursor-{run_id}:agent-{run_id}:shared-task"
    sk_codex = f"{project_a}:codex-{run_id}:agent-{run_id}:shared-task"

    rc = _open_session(project_a, f"cursor-{run_id}", f"agent-{run_id}", sk_cursor)
    rx = _open_session(project_a, f"codex-{run_id}", f"agent-{run_id}", sk_codex)
    assert rc["ok"] and rx["ok"]

    assert str(rc["session_id"]) != str(rx["session_id"]), (
        "Cursor and Codex must have distinct session IDs"
    )


# ---------------------------------------------------------------------------
# Test 4: Cursor and Codex both contribute to one project chronology
# ---------------------------------------------------------------------------

@db_available
def test_cross_ide_shared_project_chronology(project_a: str, run_id: str):
    """Events from Cursor and Codex are both retrievable in the project chronology."""
    sk_cursor = f"{project_a}:cursor-{run_id}:agent-{run_id}:multi-ide"
    sk_codex = f"{project_a}:codex-{run_id}:agent-{run_id}:multi-ide"

    rc = _open_session(project_a, f"cursor-{run_id}", f"agent-{run_id}", sk_cursor)
    rx = _open_session(project_a, f"codex-{run_id}", f"agent-{run_id}", sk_codex)

    sid_cursor = str(rc["session_id"])
    sid_codex = str(rx["session_id"])

    ev_c = _append(sid_cursor, f"{sk_cursor}:ev1", {"from": "cursor"})
    ev_x = _append(sid_codex, f"{sk_codex}:ev1", {"from": "codex"})
    assert ev_c["ok"] and ev_x["ok"]

    from agentcore_memory import server  # noqa: PLC0415
    chrono = server.retrieve_context({
        "project_key": project_a,
        "recovery_mode": "complete_project_chronology",
        "record_recovery": False,
    })
    assert chrono["ok"]
    ids = {item["id"] for item in chrono.get("recovery", {}).get("items", [])}
    assert ev_c["event_id"] in ids, "Cursor event missing from project chronology"
    assert ev_x["event_id"] in ids, "Codex event missing from project chronology"


# ---------------------------------------------------------------------------
# Test 5: Project A cannot read Project B events
# ---------------------------------------------------------------------------

@db_available
def test_cross_project_isolation(project_a: str, project_b: str, run_id: str):
    """Events from project_b are NOT retrievable when querying project_a."""
    sk_a = f"{project_a}:cursor-{run_id}:agent-{run_id}:isolation-task"
    sk_b = f"{project_b}:cursor-{run_id}:agent-{run_id}:isolation-task"

    ra = _open_session(project_a, f"cursor-{run_id}", f"agent-{run_id}", sk_a)
    rb = _open_session(project_b, f"cursor-{run_id}", f"agent-{run_id}", sk_b)

    ev_b = _append(str(rb["session_id"]), f"{sk_b}:secret-event", {"secret": True})
    assert ev_b["ok"]

    from agentcore_memory import server  # noqa: PLC0415
    ctx_a = server.retrieve_context({
        "project_key": project_a,
        "recovery_mode": "complete_project_chronology",
        "record_recovery": False,
    })
    assert ctx_a["ok"]
    ids_a = {item["id"] for item in ctx_a.get("recovery", {}).get("items", [])}
    assert ev_b["event_id"] not in ids_a, (
        "Project B event must NOT appear in Project A chronology (cross-project leak)"
    )


# ---------------------------------------------------------------------------
# Test 6: Duplicate prompt retries produce one canonical event (idempotency)
# ---------------------------------------------------------------------------

@db_available
def test_duplicate_prompt_idempotency(project_a: str, run_id: str):
    """Two appends with the same idempotency_key produce a single event."""
    sk = f"{project_a}:cursor-{run_id}:agent-{run_id}:idem-task"
    r = _open_session(project_a, f"cursor-{run_id}", f"agent-{run_id}", sk)
    sid = str(r["session_id"])

    idem = f"{sk}:prompt-dedup-{run_id}"
    ev1 = _append(sid, idem, {"text": "original prompt attempt"})
    ev2 = _append(sid, idem, {"text": "retry — same idempotency key"})

    assert ev1["ok"] and ev2["ok"]
    assert ev1["event_id"] == ev2["event_id"], (
        f"Duplicate append must return the same event_id. "
        f"Got ev1={ev1['event_id']} ev2={ev2['event_id']}"
    )
    assert ev2.get("idempotent_replay") is True, (
        "Second append must report idempotent_replay=True"
    )

    # Verify only one row in the database for this idempotency_key
    password = os.environ.get(PG_PASSWORD_ENV)
    if password:
        with _conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM agentcore.evidence_events e
                JOIN agentcore.source_identities si ON si.id = e.source_identity_id
                WHERE si.session_id = %s AND e.idempotency_key = %s
                """,
                (sid, idem),
            )
            cnt = cur.fetchone()["cnt"]
        assert cnt == 1, f"Expected 1 event row for the idempotency_key, found {cnt}"
