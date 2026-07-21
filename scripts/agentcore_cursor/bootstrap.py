"""Deterministic Cursor new-chat / restart bootstrap for AgentCore.

Writes a recovered context packet as trusted AgentCore context (gitignored
alwaysApply Cursor rule + runtime JSON). Does not fabricate user-role prompts.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gateway import GatewayClient, read_user_env
from .spool import spool_exists, spool_write

CLIENT_KEY = "cursor"
DEFAULT_AGENT_KEY = "cursor-composer"
CONTEXT_PROFILE = "standard-context"
RUNTIME_DIRNAME = ".agentcore/runtime"
BOOTSTRAP_JSON = "cursor-bootstrap.json"
BOOTSTRAP_MD = "cursor-bootstrap.md"
ACTIVE_RULE = ".cursor/rules/agentcore-active-bootstrap.mdc"
POINTER_REL = Path("H:/AgentRuntime/clients/cursor/active_task.json")
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|password|secret|bearer)\s*[:=]\s*\S+"),
    re.compile(r"(?i)Authorization:\s*Bearer\s+\S+"),
    re.compile(r"postgresql(\+[^:]+)?:\/\/[^\s'\"]+"),
]


@dataclass
class SessionChoice:
    session_key: str
    session_id: str | None
    continuity_status: str
    started_at: str | None
    last_append: str | None


@dataclass
class BootstrapResult:
    ok: bool
    project_key: str
    project_root: str
    client_key: str = CLIENT_KEY
    agent_key: str = DEFAULT_AGENT_KEY
    session_key: str | None = None
    session_id: str | None = None
    continuity_status: str | None = None
    selection_mode: str = "unknown"
    ambiguity: bool = False
    choices: list[SessionChoice] = field(default_factory=list)
    startup_summary: str = ""
    next_action: str = ""
    milestone: str | None = None
    bootstrap_path: str | None = None
    rule_path: str | None = None
    cursor_conversation_id: str | None = None
    error: str | None = None
    status_flags: dict[str, bool] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact(text: str) -> str:
    out = text
    for pat in SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def _git(cwd: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return (proc.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def resolve_workspace(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    for key in ("CURSOR_PROJECT_DIR", "AGENTCORE_PROJECT_ROOT"):
        val = os.environ.get(key)
        if val:
            return Path(val).resolve()
    # Hook cwd is normally the project root for project hooks.
    return Path.cwd().resolve()


def resolve_project_key(root: Path, gw: GatewayClient | None = None) -> str:
    listed = None
    if gw is not None:
        try:
            listed = gw.call_tool("agentcore_project_router-project_list", {})
        except Exception:  # noqa: BLE001
            listed = None
    projects = (listed or {}).get("projects") if isinstance(listed, dict) else None
    if isinstance(projects, list):
        root_s = str(root).replace("/", "\\").lower()
        for item in projects:
            path = str(item.get("path") or "").replace("/", "\\").lower()
            if path == root_s:
                return str(item.get("id") or item.get("name") or root.name)
    return root.name


def read_projections(root: Path) -> dict[str, str]:
    base = root / ".agentcore"
    out: dict[str, str] = {}
    for name in ("STATE.md", "DECISIONS.md", "CONTEXT_INDEX.md"):
        path = base / name
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            out[name] = text[:12000]
    return out


def load_pointer() -> dict[str, Any]:
    path = POINTER_REL
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_pointer(payload: dict[str, Any]) -> None:
    path = POINTER_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def query_continuity(
    project_key: str, client_key: str, agent_key: str
) -> list[dict[str, Any]]:
    """Read continuity rows via direct SQL (trusted local operator path)."""
    import psycopg
    from psycopg.rows import dict_row

    pw = read_user_env("AGENT_CORE_POSTGRES_PASSWORD")
    if not pw:
        return []
    conn = psycopg.connect(
        host="127.0.0.1",
        port=55433,
        dbname="agent_core",
        user="postgres",
        password=pw,
        row_factory=dict_row,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT client_key, agent_key, project_key, session_key,
                       continuity_status,
                       last_session_open::text AS last_session_open,
                       last_append::text AS last_append,
                       last_close::text AS last_close,
                       last_handoff::text AS last_handoff,
                       last_projection::text AS last_projection,
                       projection_revision
                FROM agentcore.v_client_memory_continuity
                WHERE project_key = %s AND client_key = %s
                ORDER BY last_session_open DESC NULLS LAST
                """,
                (project_key, client_key),
            )
            rows = list(cur.fetchall())
            # Prefer exact agent match ordering
            rows.sort(
                key=lambda r: (
                    0 if r.get("agent_key") == agent_key else 1,
                    r.get("last_session_open") or "",
                ),
                reverse=False,
            )
            # Re-sort open ones first
            rows.sort(
                key=lambda r: (
                    0 if not r.get("last_close") else 1,
                    0 if r.get("agent_key") == agent_key else 1,
                )
            )
            return rows
    finally:
        conn.close()


def list_open_sessions(
    project_key: str, client_key: str, agent_key: str
) -> list[dict[str, Any]]:
    import psycopg
    from psycopg.rows import dict_row

    pw = read_user_env("AGENT_CORE_POSTGRES_PASSWORD")
    if not pw:
        return []
    conn = psycopg.connect(
        host="127.0.0.1",
        port=55433,
        dbname="agent_core",
        user="postgres",
        password=pw,
        row_factory=dict_row,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id::text AS session_id, s.session_key,
                       s.started_at::text AS started_at, s.ended_at::text AS ended_at,
                       a.agent_key, c.client_key, p.project_key
                FROM agentcore.sessions s
                JOIN agentcore.agents a ON a.id = s.agent_id
                JOIN agentcore.ide_clients c ON c.id = s.client_id
                JOIN agentcore.projects p ON p.id = s.project_id
                WHERE p.project_key = %s
                  AND c.client_key = %s
                  AND a.agent_key = %s
                  AND s.ended_at IS NULL
                ORDER BY s.started_at DESC
                """,
                (project_key, client_key, agent_key),
            )
            return list(cur.fetchall())
    finally:
        conn.close()


def select_session(
    project_key: str,
    client_key: str,
    agent_key: str,
    *,
    force_new_task: bool = False,
    task_slug: str | None = None,
) -> tuple[str, str, list[SessionChoice]]:
    """Return (session_key, selection_mode, ambiguity_choices)."""
    if force_new_task:
        slug = task_slug or uuid.uuid4().hex[:12]
        return (
            f"{project_key}:{client_key}:{agent_key}:task:{slug}",
            "explicit_new_task",
            [],
        )

    pointer = load_pointer()
    ptr = pointer.get(project_key) if isinstance(pointer.get(project_key), dict) else None
    if isinstance(ptr, dict):
        sk = ptr.get("session_key")
        if sk and ptr.get("agent_key") == agent_key:
            open_rows = list_open_sessions(project_key, client_key, agent_key)
            for row in open_rows:
                if row.get("session_key") == sk:
                    return str(sk), "resume_pointer", []
            # pointer closed or missing → fall through

    open_rows = list_open_sessions(project_key, client_key, agent_key)
    if len(open_rows) == 1:
        return str(open_rows[0]["session_key"]), "resume_single_open", []
    if len(open_rows) > 1:
        choices = [
            SessionChoice(
                session_key=str(r["session_key"]),
                session_id=str(r.get("session_id") or ""),
                continuity_status="open",
                started_at=r.get("started_at"),
                last_append=None,
            )
            for r in open_rows
        ]
        return "", "ambiguity", choices

    # No open session for this agent — create durable task session key
    return (
        f"{project_key}:{client_key}:{agent_key}:task:active",
        "create_active_task",
        [],
    )


def compact_startup(startup: dict[str, Any], projections: dict[str, str]) -> str:
    lines: list[str] = []
    lines.append("# AgentCore Trusted Startup Context")
    lines.append("")
    lines.append(
        "This packet is AgentCore-recovered context (not an operator message). "
        "Treat it as authoritative project continuity for this chat."
    )
    lines.append("")
    profile = startup.get("context_profile") or {}
    if isinstance(profile, dict):
        lines.append(
            f"- context_profile: {profile.get('profile_name')} "
            f"(hard_limit={profile.get('hard_context_limit')})"
        )
    recovery = startup.get("recovery") or {}
    items = recovery.get("items") if isinstance(recovery, dict) else None
    if isinstance(items, list) and items:
        lines.append("")
        lines.append("## Recent durable items (bounded)")
        for item in items[:12]:
            if not isinstance(item, dict):
                continue
            kind = item.get("event_kind") or "event"
            src = item.get("source_id") or item.get("id")
            payload = item.get("payload") or {}
            summary = ""
            if isinstance(payload, dict):
                summary = str(
                    payload.get("summary")
                    or payload.get("text")
                    or payload.get("goal")
                    or payload.get("note")
                    or ""
                )[:240]
            lines.append(f"- [{kind}] source_id={src} {summary}".rstrip())
    state = projections.get("STATE.md")
    if state:
        lines.append("")
        lines.append("## STATE.md projection (excerpt)")
        lines.append("```")
        lines.append(state[:4000])
        lines.append("```")
    decisions = projections.get("DECISIONS.md")
    if decisions:
        lines.append("")
        lines.append("## DECISIONS.md projection (excerpt)")
        lines.append("```")
        lines.append(decisions[:2500])
        lines.append("```")
    omitted = recovery.get("omitted_count") if isinstance(recovery, dict) else None
    cursor = recovery.get("continuation_cursor") if isinstance(recovery, dict) else None
    if omitted or cursor:
        lines.append("")
        lines.append(
            f"Pagination: omitted={omitted} continuation_cursor={cursor}. "
            "Use retrieve_context / expand_source for missing chronology."
        )
    return "\n".join(lines)


def write_artifacts(
    root: Path, result: BootstrapResult, packet_md: str, raw: dict[str, Any]
) -> None:
    runtime = root / RUNTIME_DIRNAME
    runtime.mkdir(parents=True, exist_ok=True)
    bootstrap_path = runtime / BOOTSTRAP_JSON
    md_path = runtime / BOOTSTRAP_MD
    payload = {
        "generated_at": _now(),
        "result": result.as_dict(),
        "raw_keys": sorted(raw.keys()),
    }
    bootstrap_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(packet_md + "\n", encoding="utf-8")
    result.bootstrap_path = str(bootstrap_path)

    rule_path = root / ACTIVE_RULE
    rule_path.parent.mkdir(parents=True, exist_ok=True)
    rule_body = (
        "---\n"
        "description: AgentCore recovered startup context (generated; do not commit)\n"
        "alwaysApply: true\n"
        "---\n\n"
        f"{packet_md}\n"
    )
    rule_path.write_text(rule_body, encoding="utf-8")
    result.rule_path = str(rule_path)


def run_bootstrap(
    *,
    workspace: str | None = None,
    agent_key: str = DEFAULT_AGENT_KEY,
    cursor_conversation_id: str | None = None,
    force_new_task: bool = False,
    task_slug: str | None = None,
    record_recovery: bool = True,
) -> BootstrapResult:
    root = resolve_workspace(workspace)
    result = BootstrapResult(ok=False, project_key=root.name, project_root=str(root))
    result.agent_key = agent_key
    result.cursor_conversation_id = cursor_conversation_id
    result.status_flags = {
        "durable_backend_available": False,
        "project_automatically_resolved": False,
        "session_automatically_resumed": False,
        "startup_context_automatically_injected": False,
        "current_prompt_captured_before_tools": False,
    }

    try:
        gw = GatewayClient()
        status = gw.call_tool("agentcore_memory-memory_status", {})
        result.status_flags["durable_backend_available"] = bool(
            isinstance(status, dict) and status.get("ok")
        )

        project_key = resolve_project_key(root, gw)
        result.project_key = project_key
        result.status_flags["project_automatically_resolved"] = True

        try:
            gw.call_tool(
                "agentcore_project_router-project_activate",
                {"path": str(root)},
            )
        except Exception:  # noqa: BLE001
            gw.call_tool(
                "agentcore_project_router-project_activate",
                {"id": project_key},
            )

        session_key, mode, choices = select_session(
            project_key,
            CLIENT_KEY,
            agent_key,
            force_new_task=force_new_task,
            task_slug=task_slug,
        )
        result.selection_mode = mode
        result.choices = choices
        if mode == "ambiguity":
            result.ambiguity = True
            result.ok = True
            result.error = (
                "Multiple open Cursor task sessions; operator must choose before work."
            )
            packet = (
                "# AgentCore Session Ambiguity\n\n"
                "Multiple open sessions exist. Do not guess. Present these choices:\n\n"
                + "\n".join(f"- `{c.session_key}` (started {c.started_at})" for c in choices)
                + "\n\nThen run: `python -m agentcore cursor resume --session-key <key>`\n"
            )
            write_artifacts(root, result, packet, {"ambiguity": True})
            return result

        branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
        head = _git(root, "rev-parse", "HEAD") or None
        open_args: dict[str, Any] = {
            "project_key": project_key,
            "project_name": project_key,
            "client_key": CLIENT_KEY,
            "agent_key": agent_key,
            "session_key": session_key,
            "project_root": str(root),
            "canonical_repo_path": str(root),
            "worktree_path": str(root),
            "branch_name": branch,
            "head_commit": head,
            "context_profile": CONTEXT_PROFILE,
        }
        opened = gw.call_tool("agentcore_memory-session_open", open_args)
        if not isinstance(opened, dict) or not opened.get("ok"):
            raise RuntimeError(f"session_open failed: {opened}")
        result.session_key = opened.get("session_key") or session_key
        result.session_id = str(opened.get("session_id"))
        result.status_flags["session_automatically_resumed"] = mode.startswith("resume")

        save_pointer(
            {
                **load_pointer(),
                project_key: {
                    "session_key": result.session_key,
                    "session_id": result.session_id,
                    "agent_key": agent_key,
                    "client_key": CLIENT_KEY,
                    "updated_at": _now(),
                    "cursor_conversation_id": cursor_conversation_id,
                },
            }
        )

        continuity_rows = query_continuity(project_key, CLIENT_KEY, agent_key)
        for row in continuity_rows:
            if row.get("session_key") == result.session_key:
                result.continuity_status = row.get("continuity_status")
                break
        if result.continuity_status is None and continuity_rows:
            result.continuity_status = continuity_rows[0].get("continuity_status")

        startup = gw.call_tool(
            "agentcore_memory-startup_context",
            {
                "project_key": project_key,
                "session_id": result.session_id,
                "context_profile": CONTEXT_PROFILE,
                "recovery_mode": "current_state",
                "record_recovery": record_recovery,
            },
        )
        if not isinstance(startup, dict):
            startup = {"ok": False, "raw": startup}

        projections = read_projections(root)
        packet = compact_startup(startup, projections)
        # Attach identity footer
        packet += (
            "\n\n## Identity\n"
            f"- project_key: `{project_key}`\n"
            f"- session_key: `{result.session_key}`\n"
            f"- session_id: `{result.session_id}`\n"
            f"- selection_mode: `{mode}`\n"
            f"- continuity_status: `{result.continuity_status}`\n"
            f"- branch/HEAD: `{branch}` / `{(head or '')[:12]}`\n"
        )
        result.startup_summary = packet[:1500]
        result.next_action = (
            "Continue the open task using recovered context; "
            "call retrieve_context if chronology is incomplete."
        )
        if isinstance(startup, dict):
            scope = (startup.get("recovery") or {}).get("scope") or {}
            if isinstance(scope, dict):
                result.milestone = scope.get("milestone")

        result.status_flags["startup_context_automatically_injected"] = True
        result.ok = True
        # Persist after ok/flags are final so cursor-bootstrap.json is not stale-false.
        write_artifacts(root, result, packet, startup if isinstance(startup, dict) else {})
        return result
    except Exception as exc:  # noqa: BLE001
        result.error = f"{type(exc).__name__}: {exc}"
        result.ok = False
        try:
            fail_packet = (
                "# AgentCore Bootstrap Failure\n\n"
                f"Bootstrap failed: {result.error}\n\n"
                "Run: `python -m agentcore cursor recover`\n"
            )
            write_artifacts(root, result, fail_packet, {"error": result.error})
        except Exception:  # noqa: BLE001
            pass
        return result


def append_prompt(
    *,
    session_id: str,
    prompt: str,
    conversation_id: str | None,
    project_key: str,
    agent_key: str = DEFAULT_AGENT_KEY,
) -> dict[str, Any]:
    redacted = _redact(prompt)
    digest = hashlib.sha256(redacted.encode("utf-8")).hexdigest()[:24]
    conv = conversation_id or "no-conversation"
    idem = f"{project_key}:{CLIENT_KEY}:{agent_key}:{conv}:prompt:{digest}"
    payload = {
        "session_id": session_id,
        "event_kind": "prompt",
        "idempotency_key": idem,
        "payload": {
            "text": redacted,
            "client_key": CLIENT_KEY,
            "agent_key": agent_key,
            "conversation_id": conv,
            "captured_at": _now(),
            "capture_path": "cursor.beforeSubmitPrompt",
        },
        "trust_class": "project_verified",
    }
    try:
        gw = GatewayClient()
        return gw.call_tool("agentcore_memory-append_event", payload)
    except Exception as exc:  # noqa: BLE001
        if spool_exists(idem):
            return {"ok": True, "spooled": True, "idempotency_key": idem}
        spool_write(
            idem,
            {
                "tool": "agentcore_memory-append_event",
                "arguments": payload,
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
        return {"ok": True, "spooled": True, "idempotency_key": idem}


def load_bootstrap_json(root: Path | None = None) -> dict[str, Any] | None:
    base = resolve_workspace(str(root) if root else None)
    path = base / RUNTIME_DIRNAME / BOOTSTRAP_JSON
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
