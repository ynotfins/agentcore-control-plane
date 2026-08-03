"""Cursor hook entrypoints — invoked by hook_dispatcher.py only."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


def _normalize_workspace_path(path_str: str | None) -> Path:
    if not path_str:
        return Path.cwd().resolve()
    match = re.match(r"^([a-zA-Z]):([^\\/].*)$", str(path_str))
    if match:
        path_str = f"{match.group(1)}:\\{match.group(2)}"
    return Path(path_str).resolve()

# Ensure scripts/ is importable when launched from repo hooks.
_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from agentcore_cursor.bootstrap import (  # noqa: E402
    DEFAULT_AGENT_KEY,
    append_prompt,
    load_bootstrap_json,
    run_bootstrap,
)
from agentcore_cursor.gateway import GatewayClient  # noqa: E402
from agentcore_cursor.session_scope import SessionScope  # noqa: E402


SERENA_MAINTENANCE_SCRIPT = Path(
    r"D:\github\agentcore-control-plane\scripts\agentcore_cursor\serena_maintenance.py"
)
SERENA_MAINTENANCE_APPROVAL_PATTERN = r"AUTH-[0-9]{4}-[0-9]{2}-[0-9]{2}-[A-Z0-9_-]+"
AUTHORITY_APPROVAL_PATTERN = SERENA_MAINTENANCE_APPROVAL_PATTERN
AUTHORITY_OPERATOR_LOCKED = {
    "PROJECT_ANCHOR.md",
    "BLUEPRINT.md",
    "MILESTONES.md",
    "AUTHORITY_LOCK.md",
    "contracts/authority-lock.yaml",
}
AUTHORITY_GENERATED_READ_ONLY = {
    ".agentcore/STATE.md",
    ".agentcore/DECISIONS.md",
    ".agentcore/CONTEXT_INDEX.md",
}
GLOBAL_GENERATED_READ_ONLY = {
    str(Path(r"C:\Users\ynotf\.agentcore\GLOBAL_STATE.md").resolve()).lower()
}
AUTHORITY_SHELL_PROTECTED_FRAGMENT = (
    r"(PROJECT_ANCHOR\.md|BLUEPRINT\.md|MILESTONES\.md|AUTHORITY_LOCK\.md|"
    r"contracts[\\/]+authority-lock\.yaml|\.agentcore[\\/]+(?:STATE|DECISIONS|CONTEXT_INDEX)\.md)"
)
AUTHORITY_SHELL_PROTECTED_PATTERN = re.compile(
    AUTHORITY_SHELL_PROTECTED_FRAGMENT,
    re.IGNORECASE,
)


def os_environ_get(name: str) -> str | None:
    return os.environ.get(name)


def _append_durable_hook_event(
    root_path: Path,
    *,
    event_kind: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    bootstrap = load_bootstrap_json(root_path) or {}
    result = bootstrap.get("result") if isinstance(bootstrap, dict) else {}
    if not isinstance(result, dict):
        return {"ok": False, "error": "bootstrap_missing"}
    session_id = str(result.get("session_id") or "")
    project_key = str(result.get("project_key") or "")
    if not session_id or not project_key:
        return {"ok": False, "error": "session_identity_missing"}
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    idempotency_key = hashlib.sha256(
        f"{project_key}|{session_id}|{event_kind}|{serialized}".encode("utf-8")
    ).hexdigest()
    return GatewayClient().call_tool(
        "agentcore_memory-append_event",
        {
            "project_key": project_key,
            "project_root": str(root_path.resolve()),
            "session_id": session_id,
            "event_kind": event_kind,
            "idempotency_key": idempotency_key,
            "payload": payload,
            "trust_class": "system_verified",
        },
    )


def _build_durable_handoff(root_path: Path) -> dict[str, Any]:
    bootstrap = load_bootstrap_json(root_path) or {}
    result = bootstrap.get("result") if isinstance(bootstrap, dict) else {}
    if not isinstance(result, dict):
        return {"ok": False, "error": "bootstrap_missing"}
    project_key = str(result.get("project_key") or "")
    session_id = str(result.get("session_id") or "")
    if not project_key or not session_id:
        return {"ok": False, "error": "session_identity_missing"}
    return GatewayClient().call_tool(
        "agentcore_memory-build_handoff",
        {"project_key": project_key, "project_root": str(root_path.resolve()), "session_id": session_id},
    )


def handle_session_start(payload: dict[str, Any]) -> dict[str, Any]:
    conversation_id = (
        payload.get("session_id")
        or payload.get("conversation_id")
        or payload.get("composer_id")
    )
    roots = payload.get("workspace_roots") or []
    workspace = None
    if isinstance(roots, list) and roots:
        workspace = str(_normalize_workspace_path(str(roots[0])))
    result = run_bootstrap(
        workspace=workspace,
        agent_key=DEFAULT_AGENT_KEY,
        cursor_conversation_id=str(conversation_id) if conversation_id else None,
    )
    env = {
        "AGENTCORE_BOOTSTRAP_OK": "1" if result.ok and not result.ambiguity else "0",
        "AGENTCORE_PROJECT_KEY": result.project_key or "",
        "AGENTCORE_SESSION_KEY": result.session_key or "",
        "AGENTCORE_SESSION_ID": result.session_id or "",
        "AGENTCORE_BOOTSTRAP_PATH": result.bootstrap_path or "",
    }
    additional = ""
    if result.rule_path and Path(result.rule_path).is_file():
        additional = Path(result.rule_path).read_text(encoding="utf-8", errors="replace")
        if additional.startswith("---"):
            parts = additional.split("---", 2)
            if len(parts) >= 3:
                additional = parts[2].strip()
    if not additional and result.bootstrap_path:
        cached = load_bootstrap_json(Path(workspace) if workspace else None)
        if isinstance(cached, dict):
            md_path = Path(result.bootstrap_path).with_name("cursor-bootstrap.md")
            if md_path.is_file():
                additional = md_path.read_text(encoding="utf-8", errors="replace")[:120000]
    # Never mutate a rejected workspace or claim prompt capture at session start.
    try:
        boot_p = (Path(workspace) if workspace else Path.cwd()) / ".agentcore" / "runtime" / "cursor-bootstrap.json"
        if result.ok and boot_p.is_file():
            bdata = json.loads(boot_p.read_text(encoding="utf-8"))
            bdata.setdefault("result", {}).setdefault("status_flags", {})["startup_context_completed"] = True
            boot_p.write_text(json.dumps(bdata, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass

    # run_bootstrap uses the signed GatewayClient path; do not open a duplicate
    # Context Engine session from a second bridge.
    env["AGENTCORE_CONTEXT_ENGINE"] = "1" if result.ok else "0"

    out: dict[str, Any] = {"env": env}
    if additional:
        out["additional_context"] = additional[:120000]
    return out


def handle_before_submit(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = str(
        payload.get("prompt")
        or payload.get("text")
        or payload.get("user_prompt")
        or payload.get("message")
        or ""
    )
    conversation_id = (
        payload.get("conversation_id")
        or payload.get("session_id")
        or payload.get("composer_id")
        or os_environ_get("AGENTCORE_CURSOR_CONVERSATION_ID")
    )
    roots = payload.get("workspace_roots") or []
    workspace = str(_normalize_workspace_path(str(roots[0]))) if isinstance(roots, list) and roots else None

    data = load_bootstrap_json(Path(workspace) if workspace else None)
    result_block = (data or {}).get("result") if isinstance(data, dict) else None
    needs_bootstrap = not isinstance(result_block, dict) or not result_block.get("ok")
    if needs_bootstrap:
        boot = run_bootstrap(
            workspace=workspace,
            cursor_conversation_id=str(conversation_id) if conversation_id else None,
        )
        result_block = boot.as_dict()
    if isinstance(result_block, dict) and result_block.get("ambiguity"):
        return {
            "continue": False,
            "user_message": (
                "AgentCore: multiple open task sessions. "
                "Run `python -m agentcore cursor status` and resume one session "
                "before continuing."
            ),
        }

    session_id = (result_block or {}).get("session_id") if isinstance(result_block, dict) else None
    project_key = (result_block or {}).get("project_key") if isinstance(result_block, dict) else None
    prompt_evidence: dict[str, Any] = {}
    if session_id and prompt and project_key:
        append_result = append_prompt(
            session_id=str(session_id),
            prompt=prompt,
            conversation_id=str(conversation_id) if conversation_id else None,
            project_key=str(project_key),
            project_root=str(Path(workspace).resolve() if workspace else Path.cwd().resolve()),
        )
        accepted = isinstance(append_result, dict) and append_result.get("ok")
        if not accepted:
            return {
                "continue": False,
                "user_message": (
                    "AgentCore failed to durably capture the operator prompt. "
                    "Fix gateway/memory health, then resubmit."
                ),
            }
        prompt_evidence = {
            "event_id": append_result.get("event_id"),
            "idempotent_replay": bool(append_result.get("idempotent_replay")),
        }
        root = Path(workspace) if workspace else Path.cwd()
        boot_path = root / ".agentcore" / "runtime" / "cursor-bootstrap.json"
        if boot_path.is_file():
            try:
                blob = json.loads(boot_path.read_text(encoding="utf-8"))
                blob.setdefault("result", {}).setdefault("status_flags", {})[
                    "current_prompt_captured_before_tools"
                ] = True
                blob["last_prompt_capture_at"] = __import__(
                    "datetime"
                ).datetime.now(__import__("datetime").timezone.utc).isoformat()
                boot_path.write_text(json.dumps(blob, indent=2) + "\n", encoding="utf-8")
            except Exception:
                pass

    return {"continue": True, "agentcore_prompt_capture": prompt_evidence}


def _is_write_operation(tool_name: str, tool_input: dict[str, Any]) -> bool:
    name = (tool_name or "").lower()
    write_tools = {
        "filesystem-write_file", "filesystem-edit_file", "filesystem-move_file",
        "filesystem-create_directory", "filesystem-delete_file", "write_file",
        "edit_file", "strreplace", "write", "delete"
    }
    if name in write_tools:
        return True
    if any(k in name for k in ("write", "edit", "create", "delete", "replace", "modify")):
        return True
    return False


def _get_target_path(tool_input: dict[str, Any]) -> Optional[str]:
    for key in ("path", "target_path", "filepath", "file_path", "destination", "dest"):
        val = tool_input.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _authority_relative_path(root_path: Path, target_p: Path) -> str | None:
    try:
        rel = target_p.relative_to(root_path)
    except ValueError:
        return None
    return rel.as_posix()


def _authority_path_class(root_path: Path, target_p: Path) -> str | None:
    rel = _authority_relative_path(root_path, target_p)
    if rel in AUTHORITY_OPERATOR_LOCKED:
        return "operator_locked"
    if rel in AUTHORITY_GENERATED_READ_ONLY:
        return "generated_read_only"
    if str(target_p).lower() in GLOBAL_GENERATED_READ_ONLY:
        return "generated_read_only"
    return None


def _has_authority_approval() -> bool:
    capability = os.environ.get("AGENTCORE_AUTHORITY_CAPABILITY")
    approval_id = os.environ.get("AGENTCORE_AUTHORITY_APPROVAL_ID")
    return (
        capability == "authority_maintainer"
        and bool(approval_id)
        and re.fullmatch(AUTHORITY_APPROVAL_PATTERN, approval_id) is not None
    )


def _has_projection_worker_provenance() -> bool:
    return (
        os.environ.get("AGENTCORE_AUTHORITY_CAPABILITY") == "projection_worker"
        or os.environ.get("AGENTCORE_GENERATED_FILE_OWNER") == "projection_worker"
    )


def handle_pre_tool(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage B preToolUse deterministic gating.
    
    Fail open for unexpected hook errors, but enforce deterministic deny for
    unauthorized or incomplete write/edit operations.
    """
    try:
        roots = payload.get("workspace_roots") or []
        workspace = str(_normalize_workspace_path(str(roots[0]))) if isinstance(roots, list) and roots else None
        root_path = _normalize_workspace_path(workspace)

        data = load_bootstrap_json(root_path)
        result_block = (data or {}).get("result") if isinstance(data, dict) else None
        
        tool_name = str(payload.get("tool_name") or payload.get("name") or "")
        tool_input = payload.get("tool_input") or payload.get("parameters") or {}
        if not isinstance(tool_input, dict):
            tool_input = {}

        is_write = _is_write_operation(tool_name, tool_input)

        if is_write:
            # 1. Project activated
            if not isinstance(result_block, dict) or not result_block.get("ok"):
                boot = run_bootstrap(workspace=str(root_path))
                if not boot.ok:
                    return {
                        "permission": "deny",
                        "user_message": f"AgentCore Stage B Deny: project is not activated ({boot.error})"
                    }
                result_block = boot.as_dict()

            # 2. Session open
            session_id = result_block.get("session_id")
            session_key = result_block.get("session_key")
            if not session_id or not session_key:
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Deny: session is not open"
                }

            # 3. Startup context completed
            flags = result_block.get("status_flags") or {}
            if not flags.get("startup_context_completed"):
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Deny: startup_context not completed"
                }
            if not flags.get("current_prompt_captured_before_tools"):
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Deny: current operator prompt is not durably captured",
                }

            # 4. Projection missing / stale
            global_state_file = Path(r"C:\Users\ynotf\.agentcore\GLOBAL_STATE.md")
            if not global_state_file.is_file():
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Deny: GLOBAL_STATE.md projection missing"
                }

            # Load SessionScope for remaining checks
            scope = SessionScope.load_or_create(root_path)

            # 5. Step 0 intent empty
            if not scope.intent or not scope.intent.strip():
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Deny: Step 0 intent is empty in session-scope.json"
                }

            # 6. Acceptance criteria empty
            if not scope.acceptance:
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Deny: acceptance criteria empty in session-scope.json"
                }

            # 7. Declared file scope empty
            if not scope.declared_files:
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Deny: declared_files scope empty in session-scope.json"
                }

            # 8. Target path outside assigned worktree
            target = _get_target_path(tool_input)
            if target:
                target_p = _normalize_workspace_path(target)
                root_p = _normalize_workspace_path(str(root_path))
                authority_class = _authority_path_class(root_p, target_p)
                if authority_class == "operator_locked" and not _has_authority_approval():
                    return {
                        "permission": "deny",
                        "user_message": (
                            "AgentCore Stage B Deny: operator_locked authority file requires "
                            "AGENTCORE_AUTHORITY_CAPABILITY=authority_maintainer and a valid "
                            "AGENTCORE_AUTHORITY_APPROVAL_ID"
                        ),
                    }
                if authority_class == "generated_read_only" and not _has_projection_worker_provenance():
                    return {
                        "permission": "deny",
                        "user_message": (
                            "AgentCore Stage B Deny: generated_read_only projection requires "
                            "projection_worker provenance"
                        ),
                    }
                is_under_root = False
                try:
                    target_p.relative_to(root_p)
                    is_under_root = True
                except ValueError:
                    pass
                
                # Allow runtime/agentcore internal dirs
                runtime_root = os.environ.get("AGENTCORE_RUNTIME_ROOT", r"F:\AgentCore\runtime")
                is_allowed_runtime = any(
                    str(target_p).lower().startswith(p.lower())
                    for p in (r"C:\Users\ynotf\.agentcore", runtime_root)
                )
                
                if not is_under_root and not is_allowed_runtime:
                    return {
                        "permission": "deny",
                        "user_message": f"AgentCore Stage B Deny: requested path '{target}' is outside assigned worktree {root_path}"
                    }

        return {"permission": "allow"}

    except Exception as exc:  # noqa: BLE001
        return {
            "permission": "allow",
            "agent_message": f"AgentCore preToolUse degraded: {type(exc).__name__}: {str(exc)[:150]}"
        }


DENY_SHELL_PATTERNS = [
    # Authority lock protected writes/deletes via shell
    (re.compile(
        r"(?is)(>|>>|out-file|set-content|add-content|remove-item|rename-item|move-item|del\s+|erase\s+).{0,240}"
        + AUTHORITY_SHELL_PROTECTED_FRAGMENT,
        re.IGNORECASE,
    ), "authority-lock protected file shell mutation forbidden"),
    # Remote shell pipes
    (re.compile(r"(curl|wget|iwr|invoke-webrequest).*\b(pipe|\|)\s*(bash|sh|powershell|pwsh|iex|cmd)", re.IGNORECASE), "remote shell pipe"),
    # Unversioned remote installers
    (re.compile(r"(curl\s+-sSL|iwr\s+-useb|wget\s+-qO-)\s+https?://", re.IGNORECASE), "unversioned remote installer"),
    # Force push
    (re.compile(r"git\s+push.*(--force|-f)\b", re.IGNORECASE), "force push forbidden"),
    # Destructive Git cleanup/reset
    (re.compile(r"git\s+(reset\s+--hard|clean\s+-[a-z]*f)", re.IGNORECASE), "destructive Git cleanup/reset forbidden"),
    # Drive format/partition
    (re.compile(r"\b(format\s+[a-zA-Z]:|format-volume|diskpart|remove-partition|clear-disk)", re.IGNORECASE), "drive format/partition forbidden"),
    # Recursive deletion outside worktree / root drives
    (re.compile(r"rm\s+-rf\s+(/|[a-zA-Z]:[/\\]?$)", re.IGNORECASE), "recursive root deletion forbidden"),
    (re.compile(r"remove-item\s+.*-recurse.*-force\s+[a-zA-Z]:[/\\]?$", re.IGNORECASE), "recursive root deletion forbidden"),
    # Service / scheduled task mutation
    (re.compile(r"\b(sc\s+(config|delete)|set-service|stop-service|unregister-scheduledtask|disable-scheduledtask)\b", re.IGNORECASE), "service or scheduled task mutation forbidden"),
    # Unapproved live DDL / migration
    (re.compile(r"\b(drop\s+database|drop\s+table|truncate\s+table)\b", re.IGNORECASE), "unapproved live DDL forbidden"),
    # Secret printing
    (re.compile(r"(echo|print|type|cat|get-content)\s+.*(\$env:BIFROST|\$env:AGENT_CORE_POSTGRES|auth\.json|credentials\.json)", re.IGNORECASE), "secret printing forbidden"),
    (re.compile(r"\b(get-childitem\s+env:|printenv\b|env\s*$)", re.IGNORECASE), "environment variable dump forbidden"),
]


def is_serena_maintenance_command(command: str) -> bool:
    """Accept only the fixed, audited Serena repair command shape."""

    normalized = re.sub(r"\s+", " ", command.strip().replace("/", "\\"))
    if any(operator in normalized for operator in (";", "&&", "||", "|", ">", "<")):
        return False
    script = re.escape(str(SERENA_MAINTENANCE_SCRIPT))
    script_token = rf'(?:"{script}"|{script})'
    pattern = (
        rf"^(?:python|python\.exe|py|py\.exe)\s+{script_token}\s+"
        rf"(?:repair|install_cursor_rule)"
        rf"\s+--capability\s+authority_maintainer"
        rf"\s+--approval-id\s+{SERENA_MAINTENANCE_APPROVAL_PATTERN}"
        rf"(?:\s+--dry-run)?$"
    )
    return re.fullmatch(pattern, normalized, flags=re.IGNORECASE) is not None


def _is_serena_maintenance_invocation(command: str) -> bool:
    normalized = command.strip().replace("/", "\\")
    script = re.escape(str(SERENA_MAINTENANCE_SCRIPT))
    return re.search(
        rf"(?i)(?:^|[;&|]\s*)(?:python|python\.exe|py|py\.exe)\s+"
        rf'(?:"{script}"|{script})\s+(?:repair|install_cursor_rule)\b',
        normalized,
    ) is not None


def handle_before_shell(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage B beforeShellExecution deterministic gating."""
    try:
        command = str(payload.get("command") or payload.get("text") or "").strip()
        if not command:
            return {"permission": "allow"}

        if _is_serena_maintenance_invocation(command):
            if is_serena_maintenance_command(command):
                return {
                    "permission": "allow",
                    "agent_message": "Approved bounded Serena maintenance command.",
                }
            return {
                "permission": "deny",
                "user_message": "AgentCore Stage B Shell Deny: unapproved Serena maintenance command",
            }

        for pattern, reason in DENY_SHELL_PATTERNS:
            if pattern.search(command):
                return {
                    "permission": "deny",
                    "user_message": f"AgentCore Stage B Shell Deny: {reason} matched in command: {command[:100]}"
                }

        return {"permission": "allow"}

    except Exception as exc:  # noqa: BLE001
        return {
            "permission": "allow",
            "agent_message": f"AgentCore beforeShellExecution degraded: {exc}"
        }


def handle_post_tool(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage B afterFileEdit / postToolUse footprint & evidence recorder."""
    try:
        roots = payload.get("workspace_roots") or []
        workspace = str(_normalize_workspace_path(str(roots[0]))) if isinstance(roots, list) and roots else None
        root_path = _normalize_workspace_path(workspace)

        file_path = payload.get("file_path") or payload.get("path")
        tool_name = str(payload.get("tool_name") or payload.get("name") or "")

        scope = SessionScope.load_or_create(root_path)

        if file_path and isinstance(file_path, str):
            norm_path = str(Path(file_path).resolve())
            if norm_path not in scope.observed_files:
                scope.observed_files.append(norm_path)

            # Detect undeclared file edits
            declared_norm = [str(Path(p).resolve()) for p in scope.declared_files]
            if norm_path not in declared_norm:
                undeclared = scope.required_tool_evidence.setdefault("undeclared_files", [])
                if norm_path not in undeclared:
                    undeclared.append(norm_path)

        scope.required_tool_evidence.setdefault("tool_events", []).append({
            "tool_name": tool_name,
            "file_path": file_path,
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        })

        scope.save_atomic()
        durable = _append_durable_hook_event(
            root_path,
            event_kind="tool_event",
            payload={
                "hook_event": str(
                    payload.get("hook_event_name") or "postToolUse"
                ),
                "tool_name": tool_name,
                "file_path": str(file_path or ""),
                "status": str(payload.get("status") or "completed"),
            },
        )
        if not durable.get("ok"):
            return {
                "agent_message": (
                    "AgentCore durable tool-event capture degraded: "
                    f"{durable.get('error', 'unknown')}"
                )
            }
        return {}

    except Exception:  # noqa: BLE001
        return {}


def handle_stop(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage B stop hook — performs 8-axis final review.
    
    Never emits followup_message or fabricates operator prompts.
    """
    try:
        roots = payload.get("workspace_roots") or []
        workspace = str(_normalize_workspace_path(str(roots[0]))) if isinstance(roots, list) and roots else None
        root_path = _normalize_workspace_path(workspace)

        scope = SessionScope.load_or_create(root_path)

        undeclared = list(scope.required_tool_evidence.get("undeclared_files", []))
        # Record only mechanically observed facts. A hook cannot truthfully claim
        # that tests, correctness, coverage, or wiring passed.
        review = {
            "intent_declared": bool(scope.intent.strip()),
            "acceptance_declared": bool(scope.acceptance),
            "file_scope_declared": bool(scope.declared_files),
            "observed_file_count": len(scope.observed_files),
            "undeclared_files": undeclared,
            "scope_conformance_observed": not undeclared,
            "correctness": "not_proven_by_hook",
            "tests": "not_proven_by_hook",
            "independent_review": "not_proven_by_hook",
            "review_timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        }

        scope.final_review = review
        scope.save_atomic()
        durable = _append_durable_hook_event(
            root_path,
            event_kind="handoff",
            payload={
                "source": "cursor.stop",
                "final_review": review,
            },
        )
        handoff = _build_durable_handoff(root_path) if durable.get("ok") else {}
        if not durable.get("ok") or not handoff.get("ok"):
            return {
                "agent_message": (
                    "AgentCore handoff checkpoint degraded; canonical session "
                    "remains open for recovery."
                )
            }
        return {}

    except Exception:  # noqa: BLE001
        return {}


def handle_session_end(payload: dict[str, Any]) -> dict[str, Any]:
    """Record interruption only — do not close durable task sessions on chat end."""
    _ = payload
    return {}


HANDLERS = {
    "sessionStart": handle_session_start,
    "beforeSubmitPrompt": handle_before_submit,
    "preToolUse": handle_pre_tool,
    "beforeShellExecution": handle_before_shell,
    "afterFileEdit": handle_post_tool,
    "postToolUse": handle_post_tool,
    "sessionEnd": handle_session_end,
    "stop": handle_stop,
}
