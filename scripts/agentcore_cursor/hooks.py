"""Cursor hook entrypoints — invoked by hook_dispatcher.py only."""

from __future__ import annotations

import hashlib
import fnmatch
import glob
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any

import yaml


def _normalize_workspace_path(path_str: str | None) -> Path:
    if not path_str:
        raise ValueError("workspace root is required")
    raw = str(path_str).strip().strip('"').strip("'")

    # Cursor workspace.json / hook payloads often use file:// URIs
    # (e.g. file:///d%3A/OpenHands). Those are absolute roots, but
    # pathlib treats the URI string as relative unless we decode it.
    if raw.lower().startswith("file:"):
        from urllib.parse import unquote, urlparse
        from urllib.request import url2pathname

        parsed = urlparse(raw)
        if parsed.scheme.lower() != "file":
            raise ValueError("workspace root must be absolute")
        # url2pathname handles /D:/... and /d%3A/... on Windows.
        raw = url2pathname(unquote(parsed.path))
        if parsed.netloc and not raw.startswith("\\\\"):
            # UNC file://server/share to \\server\share
            raw = f"\\\\{parsed.netloc}{raw}"

    match = re.match(r"^([a-zA-Z]):([^\\/].*)$", raw)
    if match:
        raw = f"{match.group(1)}:\\{match.group(2)}"
    path = Path(raw)
    if not path.is_absolute():
        label_root = _resolve_enrolled_workspace_label(raw)
        if label_root is None:
            raise ValueError("workspace root must be absolute")
        return label_root
    return path.resolve()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _read_enrolled_workspace_roots() -> list[tuple[str, str, Path]]:
    contract_path = Path(__file__).resolve().parents[2] / "contracts" / "agentcore-project-enrollment.json"
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows: list[tuple[str, str, Path]] = []
    for project in contract.get("projects") or []:
        if not isinstance(project, dict):
            continue
        project_key = str(project.get("project_key") or "").strip()
        project_name = str(project.get("name") or "").strip()
        for raw_path in project.get("paths") or []:
            if not isinstance(raw_path, str) or not raw_path.strip():
                continue
            path = Path(raw_path)
            if path.is_absolute():
                rows.append((project_key, project_name, path.resolve()))
    return rows


def _project_key_marker_matches(root: Path, project_key: str) -> bool:
    marker = root / ".agentcore" / "project_key"
    try:
        return marker.is_file() and marker.read_text(encoding="utf-8").strip() == project_key
    except OSError:
        return False


def _verified_current_workspace_root() -> Path | None:
    """Return the hook process cwd only when it is an enrolled AgentCore root."""
    try:
        cwd = Path.cwd().resolve()
    except OSError:
        return None
    for project_key, _project_name, root in _read_enrolled_workspace_roots():
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if cwd == resolved and resolved.is_dir() and _project_key_marker_matches(resolved, project_key):
            return resolved
    return None


def _resolve_enrolled_workspace_label(raw: str) -> Path | None:
    """Resolve Cursor's folder-label root shape without accepting relative paths.

    Cursor can emit the displayed workspace label (for example
    "agentcore-control-plane") instead of a filesystem path. Only admit that
    shape when it uniquely maps to an enrolled project root that carries the
    matching .agentcore/project_key marker.
    """
    label = raw.strip().strip(".\\/ ")
    if not label or any(sep in label for sep in ("/", "\\")) or ":" in label:
        return None
    wanted = {_slug(label)}
    candidates: list[Path] = []
    for project_key, project_name, root in _read_enrolled_workspace_roots():
        aliases = {
            _slug(project_key),
            _slug(project_name),
            _slug(root.name),
        }
        if not (wanted & aliases):
            continue
        if root.is_dir() and _project_key_marker_matches(root, project_key):
            candidates.append(root)
    unique = {str(path).lower(): path for path in candidates}
    if len(unique) == 1:
        return next(iter(unique.values()))
    return None


def _workspace_root_candidate(value: Any) -> str | None:
    """Extract a path string from Cursor hook workspace root payload shapes."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in (
            "path",
            "fsPath",
            "fs_path",
            "uri",
            "folder",
            "workspace_root",
            "workspaceRoot",
            "rootPath",
            "name",
            "label",
            "workspaceName",
            "workspace_name",
        ):
            nested = value.get(key)
            if isinstance(nested, (str, dict)):
                candidate = _workspace_root_candidate(nested)
                if candidate:
                    return candidate
    return str(value)


def _first_workspace_root(payload: dict[str, Any]) -> Path | None:
    candidates: list[Any] = []
    roots = payload.get("workspace_roots") or payload.get("workspaceRoots") or []
    if isinstance(roots, list):
        candidates.extend(roots)
    elif roots:
        candidates.append(roots)
    for key in (
        "workspace_root",
        "workspaceRoot",
        "workspaceFolder",
        "workspace_folder",
        "project_root",
        "projectRoot",
        "root",
        "cwd",
        "currentWorkingDirectory",
        "current_working_directory",
    ):
        if payload.get(key) is not None:
            candidates.append(payload.get(key))

    errors: list[Exception] = []
    for candidate in candidates:
        try:
            return _normalize_workspace_path(_workspace_root_candidate(candidate))
        except (OSError, ValueError) as exc:
            errors.append(exc)

    if errors:
        cwd_root = _verified_current_workspace_root()
        if cwd_root is not None:
            return cwd_root
        raise errors[0]
    return None

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
AUTHORITY_LOCK_MANIFEST = Path(__file__).resolve().parents[2] / "contracts" / "authority-lock.yaml"
GLOBAL_STATE_FILE = Path(r"C:\Users\ynotf\.agentcore\GLOBAL_STATE.md")
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
    workspace = None
    root_path = _first_workspace_root(payload)
    if root_path is not None:
        workspace = str(root_path)
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
        md_path = Path(result.bootstrap_path).with_name("cursor-bootstrap.md")
        if md_path.is_file():
            additional = md_path.read_text(encoding="utf-8", errors="replace")[:120000]
    # Never mutate a rejected workspace or claim prompt capture at session start.
    try:
        boot_p = Path(result.bootstrap_path) if result.bootstrap_path else None
        if result.ok and boot_p is not None and boot_p.is_file():
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


_HEALTHY_PROMPT_CONTINUITY = {"current", "healthy", "open_no_events"}
_UNHEALTHY_PROMPT_CONTINUITY = {
    "stale",
    "projection_stale",
    "closed",
    "closed_no_handoff",
    "unknown",
}


def _cost_control_prompt_block(result_block: Any) -> str | None:
    if not isinstance(result_block, dict):
        return (
            "AgentCore cost-control gate blocked this prompt before model submission: "
            "durable session recovery did not return a structured health result. "
            "Run `python -m agentcore cursor recover`, verify agentcore-gateway/auth health, "
            "then resubmit."
        )

    if not result_block.get("ok"):
        error = str(result_block.get("error") or "unknown bootstrap failure")[:180]
        return (
            "AgentCore cost-control gate blocked this prompt before model submission: "
            f"durable project session is unhealthy ({error}). "
            "Run `python -m agentcore cursor recover`, verify agentcore-gateway/auth health, "
            "then resubmit."
        )

    flags = result_block.get("status_flags") or {}
    if isinstance(flags, dict):
        required_flags = {
            "durable_backend_available": "agentcore-memory backend is unavailable",
            "project_automatically_resolved": "project identity was not resolved",
        }
        startup_ok = bool(
            flags.get("startup_context_automatically_injected")
            or flags.get("startup_context_completed")
        )
        for flag, detail in required_flags.items():
            if flags.get(flag) is False:
                return (
                    "AgentCore cost-control gate blocked this prompt before model submission: "
                    f"{detail}. "
                    "Verify agentcore-gateway/auth health, then resubmit."
                )
        if not startup_ok:
            return (
                "AgentCore cost-control gate blocked this prompt before model submission: "
                "session recovery did not complete startup_context. "
                "Run `python -m agentcore cursor recover`, then resubmit."
            )

    continuity = str(result_block.get("continuity_status") or "").strip().lower()
    if continuity in _UNHEALTHY_PROMPT_CONTINUITY:
        return (
            "AgentCore cost-control gate blocked this prompt before model submission: "
            f"session recovery is `{continuity}`. "
            "Run `python -m agentcore cursor recover` or resume the correct session, "
            "then resubmit."
        )
    if continuity and continuity not in _HEALTHY_PROMPT_CONTINUITY:
        return (
            "AgentCore cost-control gate blocked this prompt before model submission: "
            f"session recovery returned unrecognized continuity_status `{continuity}`. "
            "Run `python -m agentcore cursor status`, verify the intended session, "
            "then resubmit."
        )
    return None


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
    try:
        root_path = _first_workspace_root(payload)
    except (OSError, ValueError) as exc:
        return {
            "continue": False,
            "user_message": f"AgentCore rejected the workspace root: {exc}",
        }
    if root_path is None:
        return {
            "continue": False,
            "user_message": "AgentCore cannot bind this prompt without an explicit workspace root.",
        }
    workspace = str(root_path)

    # A previous turn must never authorize tools for this prompt. Disarm before
    # bootstrap, network I/O, parsing, or any other fallible operation.
    boot_path = root_path / ".agentcore" / "runtime" / "cursor-bootstrap.json"
    if boot_path.exists() and not _set_prompt_capture_flag(root_path, captured=False):
        return {
            "continue": False,
            "user_message": (
                "AgentCore could not disarm the prior prompt gate. "
                "Recover the Cursor session, then resubmit safely."
            ),
        }

    data = load_bootstrap_json(root_path)
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

    if prompt:
        block_reason = _cost_control_prompt_block(result_block)
        if block_reason:
            return {
                "continue": False,
                "user_message": block_reason,
            }

    session_id = (result_block or {}).get("session_id") if isinstance(result_block, dict) else None
    project_key = (result_block or {}).get("project_key") if isinstance(result_block, dict) else None
    if prompt and (not session_id or not project_key):
        return {
            "continue": False,
            "user_message": (
                "AgentCore durable session identity is incomplete. "
                "Recover the session, then resubmit."
            ),
        }
    prompt_evidence: dict[str, Any] = {}
    if session_id and prompt and project_key:
        append_result = append_prompt(
            session_id=str(session_id),
            prompt=prompt,
            conversation_id=str(conversation_id) if conversation_id else None,
            project_key=str(project_key),
            project_root=str(root_path),
        )
        event_id = (
            str(append_result.get("event_id") or "").strip()
            if isinstance(append_result, dict)
            else ""
        )
        accepted = bool(
            isinstance(append_result, dict) and append_result.get("ok") is True and event_id
        )
        if not accepted:
            return {
                "continue": False,
                "user_message": (
                    "AgentCore failed to durably capture the operator prompt. "
                    "Fix gateway/memory health, then resubmit."
                ),
            }
        prompt_evidence = {
            "event_id": event_id,
            "idempotent_replay": bool(append_result.get("idempotent_replay")),
        }
        if not _set_prompt_capture_flag(
            root_path,
            captured=True,
            event_id=event_id,
            prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            session_id=str(session_id),
            conversation_id=str(conversation_id or ""),
        ):
            return {
                "continue": False,
                "user_message": (
                    "AgentCore captured the prompt but could not arm the local tool gate. "
                    "Recover the Cursor session, then resubmit safely."
                ),
            }

    return {"continue": True, "agentcore_prompt_capture": prompt_evidence}


def _is_write_operation(tool_name: str, tool_input: dict[str, Any]) -> bool:
    name = re.sub(r"[^a-z0-9]+", "", (tool_name or "").lower())
    write_tools = {
        "filesystemwritefile", "filesystemeditfile", "filesystemmovefile",
        "filesystemcreatedirectory", "filesystemdeletefile", "writefile",
        "editfile", "strreplace", "write", "delete", "applypatch",
        "movefile", "renamefile", "copyfile", "createfile",
    }
    if name in write_tools:
        return True
    if any(k in name for k in ("write", "edit", "create", "delete", "replace", "modify")):
        return True
    return False


def _tool_mutation_targets(tool_name: str, tool_input: dict[str, Any]) -> list[str] | None:
    """Return the complete affected path set, or None if it is not provable."""
    name = re.sub(r"[^a-z0-9]+", "", (tool_name or "").lower())
    if name == "applypatch":
        patch_text = tool_input.get("patch") or tool_input.get("input")
        if not isinstance(patch_text, str) or not patch_text.strip():
            return None
        paths = [
            match.group(1).strip()
            for match in re.finditer(
                r"(?m)^\*\*\* (?:Add|Update|Delete) File:\s*(.+?)\s*$", patch_text
            )
        ]
        paths.extend(
            match.group(1).strip()
            for match in re.finditer(r"(?m)^\*\*\* Move to:\s*(.+?)\s*$", patch_text)
        )
        return list(dict.fromkeys(paths)) or None

    keys = (
        "path", "target_path", "filepath", "file_path", "destination", "dest",
        "source", "src", "source_path", "old_path", "new_path",
    )
    paths: list[str] = []
    for key in keys:
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            paths.append(value.strip())
        elif isinstance(value, list):
            paths.extend(str(item).strip() for item in value if str(item).strip())
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict):
                for key in keys:
                    value = edit.get(key)
                    if isinstance(value, str) and value.strip():
                        paths.append(value.strip())
    return list(dict.fromkeys(paths)) or None


def _resolve_mutation_target(root_path: Path, raw_target: str) -> Path:
    target = Path(raw_target)
    if not target.is_absolute():
        target = root_path / target
    return target.resolve()


def _authority_relative_path(root_path: Path, target_p: Path) -> str | None:
    try:
        rel = target_p.relative_to(root_path)
    except ValueError:
        return None
    return rel.as_posix()


def _authority_path_class(root_path: Path, target_p: Path) -> str | None:
    rel = _authority_relative_path(root_path, target_p)
    if rel is not None:
        try:
            manifest = yaml.safe_load(AUTHORITY_LOCK_MANIFEST.read_text(encoding="utf-8"))
            classes = manifest.get("classes") if isinstance(manifest, dict) else None
            if not isinstance(classes, dict):
                raise ValueError("authority classes missing")
            for class_name in ("operator_locked", "governed_mutable", "generated_read_only"):
                block = classes.get(class_name)
                paths = block.get("paths") if isinstance(block, dict) else None
                if isinstance(paths, list) and any(
                    fnmatch.fnmatchcase(rel.lower(), str(pattern).replace("\\", "/").lower())
                    for pattern in paths
                ):
                    return class_name
        except (OSError, TypeError, ValueError, yaml.YAMLError):
            # Protected baseline paths remain classified even if the manifest
            # cannot be parsed; the caller will deny unresolved classifications.
            if rel in AUTHORITY_OPERATOR_LOCKED:
                return "operator_locked"
            if rel in AUTHORITY_GENERATED_READ_ONLY:
                return "generated_read_only"
            return "authority_manifest_unavailable"
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
    
    Mutation paths fail closed. Read-only tool calls remain available when the
    mutation classifier proves they cannot change state.
    """
    tool_name = str(payload.get("tool_name") or payload.get("name") or "")
    raw_tool_input = payload.get("tool_input") or payload.get("parameters") or {}
    tool_input = raw_tool_input if isinstance(raw_tool_input, dict) else {}
    is_write = _is_write_operation(tool_name, tool_input)
    try:
        root_path = _first_workspace_root(payload)
        if root_path is None:
            if is_write:
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Deny: explicit workspace root is required",
                }
            return {"permission": "allow"}

        data = load_bootstrap_json(root_path)
        result_block = (data or {}).get("result") if isinstance(data, dict) else None

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
            capture = data.get("current_prompt_capture") if isinstance(data, dict) else None
            current_session_id = str(result_block.get("session_id") or "")
            current_conversation_id = str(
                payload.get("conversation_id") or payload.get("composer_id") or ""
            )
            if (
                not isinstance(capture, dict)
                or not str(capture.get("event_id") or "").strip()
                or not re.fullmatch(r"[0-9a-f]{64}", str(capture.get("prompt_sha256") or ""))
                or str(capture.get("session_id") or "") != current_session_id
                or (
                    current_conversation_id
                    and str(capture.get("conversation_id") or "") != current_conversation_id
                )
            ):
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Deny: prompt capture is not bound to this session/turn",
                }

            # 4. Projection missing / stale
            if not GLOBAL_STATE_FILE.is_file():
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
            targets = _tool_mutation_targets(tool_name, tool_input)
            if not targets:
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Deny: mutation path set is not completely resolvable",
                }
            declared = {
                str(_resolve_mutation_target(root_path, declared_path)).lower()
                for declared_path in scope.declared_files
            }
            for target in targets:
                target_p = _resolve_mutation_target(root_path, target)
                root_p = root_path
                authority_class = _authority_path_class(root_p, target_p)
                if authority_class in {"operator_locked", "governed_mutable"} and not _has_authority_approval():
                    return {
                        "permission": "deny",
                        "user_message": (
                            f"AgentCore Stage B Deny: {authority_class} authority file requires "
                            "AGENTCORE_AUTHORITY_CAPABILITY=authority_maintainer and a valid "
                            "AGENTCORE_AUTHORITY_APPROVAL_ID"
                        ),
                    }
                if authority_class == "authority_manifest_unavailable":
                    return {
                        "permission": "deny",
                        "user_message": "AgentCore Stage B Deny: authority manifest is unavailable",
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
                if is_under_root and str(target_p).lower() not in declared:
                    return {
                        "permission": "deny",
                        "user_message": (
                            "AgentCore Stage B Deny: target not declared in session-scope.json: "
                            f"{target_p}"
                        ),
                    }

        return {"permission": "allow"}

    except Exception as exc:  # noqa: BLE001
        if is_write:
            return {
                "permission": "deny",
                "user_message": (
                    "AgentCore Stage B Deny: mutation authorization failed closed: "
                    f"{type(exc).__name__}: {str(exc)[:120]}"
                ),
            }
        return {"permission": "allow"}


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


SHELL_FILE_MUTATOR_ALIASES = {
    "rm": "remove-item",
    "del": "remove-item",
    "erase": "remove-item",
    "ri": "remove-item",
    "mv": "move-item",
    "move": "move-item",
    "cp": "copy-item",
    "copy": "copy-item",
    "ren": "rename-item",
    "ni": "new-item",
    "sc": "set-content",
    "tee": "tee-object",
}
SHELL_FILE_MUTATORS = {
    "set-content",
    "add-content",
    "clear-content",
    "out-file",
    "new-item",
    "remove-item",
    "move-item",
    "copy-item",
    "rename-item",
    "tee-object",
} | set(SHELL_FILE_MUTATOR_ALIASES)


def _set_prompt_capture_flag(
    root_path: Path,
    *,
    captured: bool,
    event_id: str = "",
    prompt_sha256: str = "",
    session_id: str = "",
    conversation_id: str = "",
) -> bool:
    boot_path = root_path / ".agentcore" / "runtime" / "cursor-bootstrap.json"
    if not boot_path.is_file():
        return False
    try:
        blob = json.loads(boot_path.read_text(encoding="utf-8"))
        blob.setdefault("result", {}).setdefault("status_flags", {})[
            "current_prompt_captured_before_tools"
        ] = captured
        if captured:
            if (
                not event_id.strip()
                or not re.fullmatch(r"[0-9a-f]{64}", prompt_sha256)
                or not session_id.strip()
            ):
                return False
            blob["current_prompt_capture"] = {
                "event_id": event_id.strip(),
                "prompt_sha256": prompt_sha256,
                "session_id": session_id.strip(),
                "conversation_id": conversation_id.strip(),
            }
        else:
            blob.pop("current_prompt_capture", None)
        timestamp_key = "last_prompt_capture_at" if captured else "prompt_capture_reset_at"
        blob[timestamp_key] = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat()
        boot_path.write_text(json.dumps(blob, indent=2) + "\n", encoding="utf-8")
        return True
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _shell_file_mutation_targets(command: str) -> tuple[bool, list[str] | None]:
    """Return every affected path, or None when the complete set is ambiguous."""
    mutator_pattern = r"(?i)\b(?:" + "|".join(SHELL_FILE_MUTATORS) + r")\b"
    ambiguous_mutation_patterns = (
        r"(?i)\bsed\s+[^\r\n]*-[a-z]*i[a-z]*\b",
        r"(?i)\b(?:python|python\.exe|py|py\.exe|node|node\.exe|ruby|perl)\s+-[a-z]*c\b",
        r"(?i)\b(?:powershell|pwsh)(?:\.exe)?\s+-(?:command|encodedcommand)\b",
        r"(?i)\bcmd(?:\.exe)?\s+/c\b",
        r"(?i)\b(?:bash|sh)\s+-c\b",
    )
    if any(re.search(pattern, command) for pattern in ambiguous_mutation_patterns):
        return True, None
    if re.search(mutator_pattern, command) and re.search(
        r"\$\(|`|\$[A-Za-z_{]|%[A-Za-z_][A-Za-z0-9_]*%", command
    ):
        return True, None
    redirect_matches = list(
        re.finditer(
            r"(?<!>)>{1,2}\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s;&|]+))",
            command,
        )
    )
    if re.search(r";|&&|\|\|?|<", command) and (
        re.search(mutator_pattern, command) or redirect_matches
    ):
        return True, None
    if redirect_matches:
        targets = [
            target
            for match in redirect_matches
            for target in [next((value for value in match.groups() if value), None)]
            if target
        ]
        return (True, targets) if targets else (True, None)

    try:
        tokens = shlex.split(command, posix=False)
    except ValueError:
        return bool(re.search(mutator_pattern, command)), None
    command_index = next(
        (index for index, token in enumerate(tokens) if token.strip("'\"").lower() in SHELL_FILE_MUTATORS),
        None,
    )
    if command_index is None:
        return False, None
    if any(token in {";", "&&", "|", "||"} for token in tokens):
        return True, None

    invoked_mutator = tokens[command_index].strip("'\"").lower()
    mutator = SHELL_FILE_MUTATOR_ALIASES.get(invoked_mutator, invoked_mutator)
    tail = tokens[command_index + 1 :]
    target_value_names = (
        {"-destination", "-newname"}
        if mutator in {"move-item", "copy-item", "rename-item"}
        else {"-literalpath", "-path", "-filepath"}
    )
    option_value_names = {
        "-encoding",
        "-value",
        "-inputobject",
        "-filter",
        "-include",
        "-exclude",
        "-stream",
        "-width",
        "-itemtype",
    }
    if mutator in {"move-item", "copy-item", "rename-item"}:
        option_value_names.update({"-literalpath", "-path"})
    flag_names = {
        "-force",
        "-whatif",
        "-confirm",
        "-passthru",
        "-nonewline",
        "-append",
        "-noclobber",
        "-recurse",
    }
    positional: list[str] = []
    explicit_sources: list[str] = []
    explicit_targets: list[str] = []
    index = 0
    while index < len(tail):
        token = tail[index]
        normalized = token.strip("'\"")
        if normalized.startswith("-"):
            option = normalized.lower()
            if option in target_value_names or option in option_value_names:
                if index + 1 >= len(tail) or tail[index + 1].startswith("-"):
                    return True, None
                value = tail[index + 1].strip("'\"")
                if option in target_value_names:
                    explicit_targets.append(value)
                elif (
                    mutator in {"move-item", "copy-item", "rename-item"}
                    and option in {"-literalpath", "-path"}
                ):
                    explicit_sources.append(value)
                index += 2
                continue
            if option in flag_names:
                index += 1
                continue
            return True, None
        positional.append(normalized)
        index += 1

    if explicit_sources or explicit_targets:
        affected = explicit_sources + explicit_targets
        return (True, affected) if affected else (True, None)
    if not positional:
        return True, None
    if mutator in {"move-item", "copy-item", "rename-item"}:
        return (True, positional) if len(positional) == 2 else (True, None)
    if mutator in {"remove-item", "clear-content"}:
        return True, positional
    return True, [positional[0]]


def _expand_shell_mutation_paths(target: str, workspace: Path) -> list[Path] | None:
    """Resolve one target and fail closed when a wildcard matches nothing."""
    target_path = Path(target)
    if not target_path.is_absolute():
        target_path = workspace / target_path
    target_text = str(target_path)
    if not glob.has_magic(target_text):
        return [target_path.resolve()]
    matches = [Path(match).resolve() for match in glob.glob(target_text)]
    return sorted(set(matches), key=lambda path: str(path).lower()) or None


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

        is_mutation, targets = _shell_file_mutation_targets(command)
        if is_mutation:
            if not targets:
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Shell Deny: file mutation target is not safely resolvable",
                }
            root_path = _first_workspace_root(payload)
            if root_path is None:
                return {
                    "permission": "deny",
                    "user_message": "AgentCore Stage B Shell Deny: explicit workspace root is required",
                }
            workspace = str(root_path)
            resolved_targets: list[Path] = []
            for target in targets:
                expanded = _expand_shell_mutation_paths(target, Path(workspace))
                if not expanded:
                    return {
                        "permission": "deny",
                        "user_message": "AgentCore Stage B Shell Deny: file mutation target is not safely resolvable",
                    }
                resolved_targets.extend(expanded)
            for target_path in dict.fromkeys(resolved_targets):
                decision = handle_pre_tool(
                    {
                        "workspace_roots": [workspace],
                        "tool_name": "write_file",
                        "tool_input": {"path": str(target_path)},
                    }
                )
                if decision.get("permission") != "allow":
                    return decision
            return {"permission": "allow"}

        return {"permission": "allow"}

    except Exception as exc:  # noqa: BLE001
        return {
            "permission": "deny",
            "user_message": f"AgentCore Stage B Shell Deny: authorization failed closed: {exc}"
        }


def handle_post_tool(payload: dict[str, Any]) -> dict[str, Any]:
    """Stage B afterFileEdit / postToolUse footprint & evidence recorder."""
    try:
        root_path = _first_workspace_root(payload)
        if root_path is None:
            return {}

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
        root_path = _first_workspace_root(payload)
        if root_path is None:
            return {}

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
        if not _set_prompt_capture_flag(root_path, captured=False):
            return {
                "agent_message": (
                    "AgentCore handoff captured, but the prompt gate could not be reset; "
                    "restart the Cursor session before further tool use."
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
