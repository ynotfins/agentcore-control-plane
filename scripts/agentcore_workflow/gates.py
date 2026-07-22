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
  resource     — resource limits / DA rework ceilings not breached
  drift        — plan vs diff drift (DA worker)
  formatting / lint / typecheck / unit / integration — tool hooks
  secret_scan  — secret pattern scan
  depwire_verify — DepWire verify_change when available
  filesystem_boundary — worktree under allowed roots
  dependency_scan — forbidden dependency introduction
"""
from __future__ import annotations
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Callable
# ─────────────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"D:\github\agentcore-control-plane")
ALLOWED_WORKTREE_ROOTS = (
    Path(r"D:\github"),
    Path(r"D:\agentcore-fixture"),
    Path(r"I:\AgentCoreScratch"),
)
SECRET_PATTERNS = (
    re.compile(r"(?i)(password|secret|api[_-]?key|token)\s*[=:]\s*['\"]?[^\s'\"]{8,}"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
FORBIDDEN_DEPENDENCY_HINTS = (
    "mem0",
    "swarmrecall",
    "swarmvault",
    "qdrant",
    "redis",
    "docker",
)
def _autonomous_strict(state: dict) -> bool:
    if state.get("autonomous"):
        return True
    return os.environ.get("AGENTCORE_WORKER_MODE", "").strip().lower() == "deterministic"
def _tool_available(cmd: str) -> bool:
    return shutil.which(cmd) is not None
def _gate_evidence(state: dict, gate_name: str) -> dict | None:
    ev = state.get("gate_evidence") or {}
    if isinstance(ev, dict) and gate_name in ev:
        payload = ev[gate_name]
        return payload if isinstance(payload, dict) else {"value": payload}
    exec_res = state.get("execution_result") or {}
    if isinstance(exec_res, dict):
        nested = exec_res.get("gate_evidence") or {}
        if isinstance(nested, dict) and gate_name in nested:
            payload = nested[gate_name]
            return payload if isinstance(payload, dict) else {"value": payload}
    return None
def _tool_hook_gate(
    state: dict,
    gate_name: str,
    *,
    commands: list[str],
    required_evidence_keys: tuple[str, ...] = ("passed",),
) -> tuple[str, dict]:
    """Optional external tool hook, or use supplied evidence.

    - Evidence passed=False → fail; passed=True → pass
    - Tool absent → warn (skip cleanly)
    - Autonomous + gate in required_gates / evidence.required without usable
      evidence → fail
    """
    details: dict[str, Any] = {"gate": gate_name}
    evidence = _gate_evidence(state, gate_name)
    required_gates = {str(x) for x in (state.get("required_gates") or [])}
    evidence_required = bool(
        gate_name in required_gates
        or (isinstance(evidence, dict) and evidence.get("required"))
    )
    if evidence is not None:
        details["evidence"] = evidence
        passed = evidence.get("passed")
        if passed is False:
            return "fail", {**details, "reason": f"{gate_name} evidence reported failure"}
        if passed is True:
            return "pass", details
        if _autonomous_strict(state) and evidence_required:
            missing = [k for k in required_evidence_keys if k not in evidence]
            return "fail", {
                **details,
                "reason": (
                    f"autonomous mode missing required evidence keys: "
                    f"{missing or list(required_evidence_keys)}"
                ),
            }
        return "warn", {**details, "reason": "evidence present but inconclusive"}
    available = [c for c in commands if _tool_available(c)]
    if not available:
        details["tools_checked"] = commands
        if _autonomous_strict(state) and evidence_required:
            return "fail", {
                **details,
                "reason": (
                    f"{gate_name}: required evidence missing in autonomous/"
                    "deterministic fixture mode (tool absent)"
                ),
            }
        return "warn", {
            **details,
            "reason": f"{gate_name}: tool absent — skipped",
            "skipped": True,
        }
    details["tool_available"] = available[0]
    details["mode"] = "availability_only"
    return "pass", details
def gate_requirement(state: dict) -> tuple[str, dict]:
    """Verify required workflow state fields are present and non-empty."""
    required = ["project_id", "project_key", "thread_uuid", "milestone_key"]
    missing = [f for f in required if not state.get(f)]
    if missing:
        return "fail", {"missing_fields": missing, "gate": "requirement"}
    if not state.get("macro_steps"):
        return "fail", {"reason": "macro_steps empty — workflow not initialised", "gate": "requirement"}
    if not state.get("current_micro_key"):
        return "fail", {
            "reason": "current_micro_key empty — first-cycle micro not set",
            "gate": "requirement",
        }
    return "pass", {
        "checked_fields": required,
        "macro_count": len(state.get("macro_steps", [])),
        "current_micro_key": state.get("current_micro_key"),
    }
def gate_scope(state: dict, db_check: bool = True) -> tuple[str, dict]:
    """Detect scope or requirement drift from the stored baseline.
    When db_check is True, calls agentcore.check_scope_drift; otherwise
    falls back to a content hash comparison (for tests without a live DB).
    """
    if not state.get("thread_db_id") and not state.get("run_db_id"):
        return "warn", {"reason": "run_db_id/thread_db_id not set, skipping scope drift check"}
    try:
        if db_check:
            from . import db
            requirements_content = json.dumps(
                state.get("macro_steps", []) + state.get("micro_steps", []),
                sort_keys=True,
            )
            run_id = state.get("run_db_id") or state.get("thread_db_id")
            drifted = db.check_scope_drift(
                run_id,
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
    """Check resource limits: DA ceilings, JIT leases, rework, token/time budgets.
    Ceilings default for CHAOSCENTRAL (i9-14900KF / 128GB / RTX 4070 SUPER 12GB)
    and are overridable via AGENTCORE_DA_* env vars (see deepagents_worker).
    """
    from .deepagents_worker import resource_ceiling_defaults
    ceilings = resource_ceiling_defaults()
    warnings: list[str] = []
    failures: list[str] = []
    details: dict[str, Any] = {"gate": "resource", "ceilings": ceilings}
    # Check active JIT leases — too many = resource warning
    try:
        from . import db
        tools = db.get_project_tools(state["project_id"])
        jit_count = sum(1 for t in tools if t["tool_state"] == "jit_leased")
        details["jit_leased"] = jit_count
        if jit_count > 5:
            warnings.append(f"{jit_count} concurrent JIT leases — consider expiring completed ones")
    except Exception:
        pass
    # Deep Agents rework ceiling (state-tracked; topology unchanged)
    rework = int(state.get("da_rework_count") or 0)
    details["da_rework_count"] = rework
    if rework > ceilings["max_rework"]:
        failures.append(
            f"da_rework_count={rework} exceeds max_rework={ceilings['max_rework']}"
        )
    # Optional per-run budget overrides from state (worker also enforces via env)
    budget = state.get("da_budget") or {}
    if isinstance(budget, dict):
        token_used = int(budget.get("tokens_used") or 0)
        token_cap = int(budget.get("token_budget") or ceilings["token_budget"])
        details["token_used"] = token_used
        details["token_budget"] = token_cap
        if token_used > token_cap:
            failures.append(f"token budget exceeded: used={token_used} cap={token_cap}")
        elapsed_ms = int(budget.get("elapsed_ms") or 0)
        time_cap_ms = int(budget.get("time_budget_ms") or ceilings["worker_timeout_sec"] * 1000)
        details["elapsed_ms"] = elapsed_ms
        details["time_budget_ms"] = time_cap_ms
        if elapsed_ms > time_cap_ms:
            failures.append(f"time budget exceeded: elapsed_ms={elapsed_ms} cap={time_cap_ms}")
    # VRAM admission stub: at most one heavy GPU task recorded in state
    heavy_gpu_active = bool(state.get("da_heavy_gpu_active"))
    details["vram_slots"] = ceilings["vram_slots"]
    details["da_heavy_gpu_active"] = heavy_gpu_active
    if heavy_gpu_active and ceilings["vram_slots"] < 1:
        failures.append("VRAM admission denied: vram_slots=0")
    details["max_concurrent_workers"] = ceilings["max_concurrent_workers"]
    details["max_subagents"] = ceilings["max_subagents"]
    if failures:
        return "fail", {**details, "failures": failures, "warnings": warnings}
    if warnings:
        return "warn", {**details, "warnings": warnings}
    return "pass", details
def gate_drift(state: dict) -> tuple[str, dict]:
    """Deterministic drift gate (ported compute_drift from deepagents-platform).
    Checks execution_result.diff against the plan to detect forbidden paths,
    size shocks, and plan deviations. Runs before any LLM critic.
    """
    from .deepagents_worker import gate_drift as _drift
    return _drift(state)
def gate_formatting(state: dict) -> tuple[str, dict]:
    return _tool_hook_gate(state, "formatting", commands=["ruff", "black"])
def gate_lint(state: dict) -> tuple[str, dict]:
    return _tool_hook_gate(state, "lint", commands=["ruff", "flake8", "eslint"])
def gate_typecheck(state: dict) -> tuple[str, dict]:
    return _tool_hook_gate(state, "typecheck", commands=["mypy", "pyright", "tsc"])
def gate_unit(state: dict) -> tuple[str, dict]:
    return _tool_hook_gate(state, "unit", commands=["pytest", "python"])
def gate_integration(state: dict) -> tuple[str, dict]:
    return _tool_hook_gate(state, "integration", commands=["pytest"])
def gate_secret_scan(state: dict) -> tuple[str, dict]:
    """Scan builder diffs / gate_evidence for secret-like material."""
    details: dict[str, Any] = {"gate": "secret_scan"}
    evidence = _gate_evidence(state, "secret_scan")
    if evidence is not None:
        if evidence.get("passed") is False:
            return "fail", {**details, "evidence": evidence, "reason": "secret_scan evidence failed"}
        if evidence.get("passed") is True:
            return "pass", {**details, "evidence": evidence}
    blobs: list[str] = []
    exec_res = state.get("execution_result") or {}
    if isinstance(exec_res, dict):
        for key in ("diff", "output", "files_changed_content"):
            val = exec_res.get(key)
            if isinstance(val, str):
                blobs.append(val)
            elif isinstance(val, list):
                blobs.extend(str(x) for x in val)
    # Never scan full state (contains env-derived noise); scan goal/acceptance lightly.
    for key in ("goal",):
        if state.get(key):
            blobs.append(str(state.get(key)))
    hits: list[str] = []
    for blob in blobs:
        for pat in SECRET_PATTERNS:
            if pat.search(blob):
                hits.append(pat.pattern[:48])
                break
    details["scanned_blobs"] = len(blobs)
    if hits:
        return "fail", {**details, "violations": hits, "reason": "secret-like pattern in artifacts"}
    return "pass", details
def gate_depwire_verify(state: dict) -> tuple[str, dict]:
    """DepWire verify_change hook — availability / evidence only (no remote graph writes)."""
    return _tool_hook_gate(state, "depwire_verify", commands=["depwire"])


def gate_filesystem_boundary(state: dict) -> tuple[str, dict]:
    """Worktree must stay under allowed roots (D:\\github, fixture, I scratch)."""
    details: dict[str, Any] = {"gate": "filesystem_boundary"}
    worktree = state.get("worktree_path") or ""
    if not worktree:
        return "warn", {**details, "reason": "worktree_path empty — deferred"}
    try:
        wt = Path(worktree).resolve()
    except Exception as exc:
        return "fail", {**details, "reason": f"invalid worktree_path: {exc}"}
    allowed = False
    for root in ALLOWED_WORKTREE_ROOTS:
        try:
            wt.relative_to(root.resolve())
            allowed = True
            break
        except ValueError:
            continue
        except Exception:
            continue
    details["worktree_path"] = str(wt)
    if not allowed:
        return "fail", {
            **details,
            "reason": "worktree outside allowed filesystem roots",
            "allowed_roots": [str(r) for r in ALLOWED_WORKTREE_ROOTS],
        }
    # Diff paths (if present) must also stay inside the worktree
    exec_res = state.get("execution_result") or {}
    files = exec_res.get("files_changed") if isinstance(exec_res, dict) else None
    leaked: list[str] = []
    if isinstance(files, list):
        for f in files:
            try:
                p = Path(str(f))
                if not p.is_absolute():
                    p = wt / p
                p.resolve().relative_to(wt)
            except Exception:
                leaked.append(str(f))
    if leaked:
        return "fail", {**details, "reason": "files_changed escaped worktree", "leaked": leaked[:10]}
    return "pass", details
def gate_dependency_scan(state: dict) -> tuple[str, dict]:
    """Fail if builder artifacts introduce forbidden dependency names."""
    details: dict[str, Any] = {"gate": "dependency_scan"}
    evidence = _gate_evidence(state, "dependency_scan")
    if evidence is not None:
        if evidence.get("passed") is False:
            return "fail", {**details, "evidence": evidence}
        if evidence.get("passed") is True:
            return "pass", {**details, "evidence": evidence}
    blobs: list[str] = []
    exec_res = state.get("execution_result") or {}
    if isinstance(exec_res, dict):
        for key in ("diff", "output", "files_changed"):
            val = exec_res.get(key)
            if isinstance(val, str):
                blobs.append(val.lower())
            elif isinstance(val, list):
                blobs.append(" ".join(str(x).lower() for x in val))
    hits = [term for term in FORBIDDEN_DEPENDENCY_HINTS if any(term in b for b in blobs)]
    details["scanned_blobs"] = len(blobs)
    if hits:
        return "fail", {**details, "violations": hits, "reason": "forbidden dependency hint in artifacts"}
    return "pass", details
# ─────────────────────────────────────────────────────────────────────────────
# Gate runner
# ─────────────────────────────────────────────────────────────────────────────
GATE_REGISTRY: dict[str, Callable[[dict], tuple[str, dict]]] = {
    "requirement": gate_requirement,
    "scope": gate_scope,
    "arch": gate_arch,
    "doc_version": gate_doc_version,
    "security": gate_security,
    "migration": gate_migration,
    "resource": gate_resource,
    "drift": gate_drift,
    "formatting": gate_formatting,
    "lint": gate_lint,
    "typecheck": gate_typecheck,
    "unit": gate_unit,
    "integration": gate_integration,
    "secret_scan": gate_secret_scan,
    "depwire_verify": gate_depwire_verify,
    "filesystem_boundary": gate_filesystem_boundary,
    "dependency_scan": gate_dependency_scan,
}
# Gates whose fail verdict is never waivable by score (judge hard-block).
HARD_DETERMINISTIC_GATES = frozenset(GATE_REGISTRY.keys())
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

