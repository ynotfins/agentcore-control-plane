"""Cursor hook entrypoints — invoked by hook_dispatcher.py only."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

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


def _read_stdin() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def handle_session_start(payload: dict[str, Any]) -> dict[str, Any]:
    conversation_id = (
        payload.get("session_id")
        or payload.get("conversation_id")
        or payload.get("composer_id")
    )
    roots = payload.get("workspace_roots") or []
    workspace = None
    if isinstance(roots, list) and roots:
        workspace = str(roots[0])
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
    out: dict[str, Any] = {"env": env}
    if additional:
        out["additional_context"] = additional[:120000]
    return out


def handle_before_submit(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = str(payload.get("prompt") or "")
    conversation_id = (
        payload.get("conversation_id")
        or payload.get("session_id")
        or os_environ_get("AGENTCORE_CURSOR_CONVERSATION_ID")
    )
    roots = payload.get("workspace_roots") or []
    workspace = str(roots[0]) if isinstance(roots, list) and roots else None

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
    if session_id and prompt and project_key:
        append_result = append_prompt(
            session_id=str(session_id),
            prompt=prompt,
            conversation_id=str(conversation_id) if conversation_id else None,
            project_key=str(project_key),
        )
        accepted = isinstance(append_result, dict) and (
            append_result.get("ok") or append_result.get("spooled")
        )
        if not accepted:
            return {
                "continue": False,
                "user_message": (
                    "AgentCore failed to durably capture the operator prompt. "
                    "Fix gateway/memory health or inspect the local spool, then resubmit."
                ),
            }
        root = Path(workspace) if workspace else Path.cwd()
        boot_path = root / ".agentcore" / "runtime" / "cursor-bootstrap.json"
        if boot_path.is_file():
            blob = json.loads(boot_path.read_text(encoding="utf-8"))
            blob.setdefault("result", {}).setdefault("status_flags", {})[
                "current_prompt_captured_before_tools"
            ] = True
            blob["last_prompt_capture_at"] = __import__(
                "datetime"
            ).datetime.now(__import__("datetime").timezone.utc).isoformat()
            boot_path.write_text(json.dumps(blob, indent=2) + "\n", encoding="utf-8")

    return {"continue": True}


def os_environ_get(name: str) -> str | None:
    import os

    return os.environ.get(name)


def handle_pre_tool(payload: dict[str, Any]) -> dict[str, Any]:
    """Defense-in-depth only — fail open unless an explicit policy violation is detected."""
    roots = payload.get("workspace_roots") or []
    workspace = str(roots[0]) if isinstance(roots, list) and roots else None
    data = load_bootstrap_json(Path(workspace) if workspace else None)
    result_block = (data or {}).get("result") if isinstance(data, dict) else None
    if not isinstance(result_block, dict) or not result_block.get("ok"):
        try:
            boot = run_bootstrap(workspace=workspace)
            if not boot.ok:
                return {
                    "permission": "allow",
                    "agent_message": (
                        f"AgentCore bootstrap incomplete ({boot.error}). "
                        "Proceed with caution; run `python -m agentcore cursor recover`."
                    ),
                }
            result_block = boot.as_dict()
        except Exception as exc:  # noqa: BLE001
            return {
                "permission": "allow",
                "agent_message": f"AgentCore preToolUse degraded: {exc}",
            }
    if result_block.get("ambiguity"):
        return {
            "permission": "allow",
            "agent_message": (
                "AgentCore session ambiguity detected. Prefer resolving via "
                "`python -m agentcore cursor status` before destructive work."
            ),
        }
    flags = result_block.get("status_flags") or {}
    messages: list[str] = []
    if not flags.get("current_prompt_captured_before_tools"):
        messages.append(
            "WARNING: operator prompt may not have been durably appended yet."
        )
    out: dict[str, Any] = {"permission": "allow"}
    if messages:
        out["agent_message"] = " ".join(messages)
    return out


def handle_session_end(payload: dict[str, Any]) -> dict[str, Any]:
    """Record interruption only — do not close durable task sessions on chat end."""
    _ = payload
    return {}


HANDLERS = {
    "sessionStart": handle_session_start,
    "beforeSubmitPrompt": handle_before_submit,
    "preToolUse": handle_pre_tool,
    "sessionEnd": handle_session_end,
    "stop": handle_session_end,
}
