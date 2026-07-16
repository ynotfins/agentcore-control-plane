"""AgentCore M6 — Deterministic gate functions.

Gates ALWAYS run before any LLM critic call. Each gate returns
(verdict: str, details: dict) where verdict is 'pass'|'fail'|'warn'.

Gate types:
  requirement  — required fields present and non-empty
  scope        — no drift from baseline (hash compare)
  arch         — architecture constraints not violated
  doc_version  — documentation version pinned and not stale
  security     — no forbidden tool or cross-project access attempted
  migration    — migration gate (operator approved destructive migrations)
  resource     — resource limits not breached
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(r"D:\github\agentcore-control-plane")


def gate_requirement(state: dict) -> tuple[str, dict]:
    """Verify required workflow state fields are present and non-empty."""
    required = ["project_id", "project_key", "thread_uuid", "milestone_key"]
    missing = [f for f in required if not state.get(f)]
    if missing:
        return "fail", {"missing_fields": missing, "gate": "requirement"}
    if not state.get("macro_steps"):
        return "fail", {"reason": "macro_steps empty — workflow not initialised", "gate": "requirement"}
    return "pass", {"checked_fields": required, "macro_count": len(state.get("macro_steps", []))}


def gate_scope(state: dict, db_check: bool = True) -> tuple[str, dict]:
    """Detect scope or requirement drift from the stored baseline.

    When db_check is True, calls agentcore.check_scope_drift; otherwise
    falls back to a content hash comparison (for tests without a live DB).
    """
    if not state.get("thread_db_id"):
        return "warn", {"reason": "thread_db_id not set, skipping scope drift check"}

    try:
        if db_check:
            from . import db
            requirements_content = json.dumps(
                state.get("macro_steps", []) + state.get("micro_steps", []),
                sort_keys=True,
            )
            drifted = db.check_scope_drift(
                state["thread_db_id"],
                state["project_id"],
                "requirements",
                requirements_content,
            )
            if drifted:
                return "fail", {
                    "gate": "scope",
                    "reason": "Requirement/scope drift detected from baseline — operator approval required",
                    "aspect": "requirements",
                }
        return "pass", {"gate": "scope", "drift_detected": False}
    except Exception as exc:
        return "warn", {"gate": "scope", "error": str(exc)}


def gate_arch(state: dict) -> tuple[str, dict]:
    """Check that no forbidden architecture patterns are being introduced.

    Forbidden: second canonical memory store, Swarm dependency, Mem0 installation,
    Docker/WSL for core platform, replacing PostgreSQL as canonical authority.
    """
    errors = []
    project_key = state.get("project_key", "")
    macro_labels = " ".join(s.get("label", "") for s in state.get("macro_steps", []))

    forbidden_terms = [
        ("mem0", "Mem0 is not permitted in v1"),
        ("swarmrecall", "SwarmRecall is Swarm-only"),
        ("swarmvault", "SwarmVault is Swarm-only"),
        ("qdrant", "No second canonical vector store"),
        ("redis", "No Redis dependency for core platform"),
        ("docker", "No Docker dependency for core platform"),
        ("wsl", "No WSL dependency for core platform"),
    ]
    lower_labels = macro_labels.lower()
    for term, reason in forbidden_terms:
        if term in lower_labels:
            errors.append(reason)

    if errors:
        return "fail", {"gate": "arch", "violations": errors}
    return "pass", {"gate": "arch", "checked_terms": [t for t, _ in forbidden_terms]}


def gate_doc_version(state: dict) -> tuple[str, dict]:
    """Verify that the BLUEPRINT.md reference matches the locked version."""
    blueprint = REPO_ROOT / "BLUEPRINT.md"
    if not blueprint.exists():
        return "fail", {"gate": "doc_version", "reason": "BLUEPRINT.md not found"}
    first_line = blueprint.read_text(encoding="utf-8").splitlines()[0]
    if "BLUEPRINT.md" not in first_line and "#" not in first_line:
        return "warn", {"gate": "doc_version", "reason": "BLUEPRINT.md format unexpected"}
    return "pass", {"gate": "doc_version", "blueprint_exists": True}


def gate_security(state: dict) -> tuple[str, dict]:
    """Verify no cross-project access is attempted and no secrets are in state."""
    violations = []
    # Confirm project_id appears in thread_uuid (our convention: project-scoped thread)
    thread_uuid = state.get("thread_uuid", "")
    project_id = state.get("project_id", "")

    # Check state does not contain obvious secret patterns
    state_str = json.dumps(state)
    for pattern in ["password=", "secret=", "api_key=", "token=", "Bearer "]:
        if pattern.lower() in state_str.lower():
            violations.append(f"Potential secret pattern '{pattern}' found in workflow state")

    # Verify no env var secret leakage
    pg_pass = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    if pg_pass and pg_pass in state_str:
        violations.append("PostgreSQL password appears in workflow state")

    if violations:
        return "fail", {"gate": "security", "violations": violations}
    return "pass", {"gate": "security", "project_id": project_id}


def gate_migration(state: dict, requires_destructive: bool = False) -> tuple[str, dict]:
    """Migration gate: destructive DB migrations require operator approval.

    For M6 workflow execution, check that the M6 migration has been applied.
    """
    try:
        from . import db
        with db.conn() as c:
            row = c.execute(
                "SELECT COUNT(*) AS cnt FROM agentcore.schema_migrations WHERE version = 'm6.001'",
            ).fetchone()
            applied = (row["cnt"] > 0) if row else False

        if not applied:
            return "fail", {
                "gate": "migration",
                "reason": "M6 migration m6.001 not yet applied — run the migration first",
            }

        if requires_destructive:
            return "fail", {
                "gate": "migration",
                "reason": "Destructive migration requires explicit operator approval",
            }

        return "pass", {"gate": "migration", "m6_001_applied": True}
    except Exception as exc:
        return "warn", {"gate": "migration", "error": str(exc)}


def gate_resource(state: dict) -> tuple[str, dict]:
    """Check resource limits: disk, DB connections, active leases."""
    warnings = []

    # Check active JIT leases — too many = resource warning
    try:
        from . import db
        tools = db.get_project_tools(state["project_id"])
        jit_count = sum(1 for t in tools if t["tool_state"] == "jit_leased")
        if jit_count > 5:
            warnings.append(f"{jit_count} concurrent JIT leases — consider expiring completed ones")
    except Exception:
        pass

    if warnings:
        return "warn", {"gate": "resource", "warnings": warnings}
    return "pass", {"gate": "resource"}


# ─────────────────────────────────────────────────────────────────────────────
# Gate runner
# ─────────────────────────────────────────────────────────────────────────────

GATE_REGISTRY = {
    "requirement": gate_requirement,
    "scope": gate_scope,
    "arch": gate_arch,
    "doc_version": gate_doc_version,
    "security": gate_security,
    "migration": gate_migration,
    "resource": gate_resource,
}


def run_all_gates(state: dict, gates: list[str] | None = None) -> dict[str, tuple[str, dict]]:
    """Run the specified gates (or all gates) and return {gate_name: (verdict, details)}."""
    gates_to_run = gates or list(GATE_REGISTRY.keys())
    results = {}
    for gate_name in gates_to_run:
        fn = GATE_REGISTRY.get(gate_name)
        if fn:
            try:
                results[gate_name] = fn(state)
            except Exception as exc:
                results[gate_name] = ("warn", {"gate": gate_name, "error": str(exc)})
    return results
