#!/usr/bin/env python3
"""Fail-closed stdio guard for the AgentCore clasp MCP integration.

The upstream clasp 3.4.1 server accepts paths beneath either the process home
directory or its current working directory, including implicit discovery by
the otherwise read-only listing tool. AgentCore therefore exposes none of the
upstream tools until an isolation adapter can enforce the Apps Script root;
this process keeps direct JSON-RPC access fail-closed as a second boundary.
"""

from __future__ import annotations

import argparse
import copy
import json
import ntpath
import os
import stat
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Iterable


ALLOWED_TOOLS: frozenset[str] = frozenset()
TOOL_INVENTORY_ORDER: tuple[str, ...] = ()
PATH_TOOLS = frozenset({"pull_files", "clone_project"})
DENIED_TOOLS = frozenset(
    {"list_projects", "push_files", "create_project", "pull_files", "clone_project"}
)
DOS_DEVICE_NAMES = frozenset({"con", "prn", "aux", "nul"})


class GuardViolation(ValueError):
    """A caller-visible policy rejection represented only by a stable code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _path_violation() -> GuardViolation:
    return GuardViolation("path_outside_workspace")


def _screen_windows_path(value: Any, *, relative_only: bool = False) -> str:
    """Reject ambiguous Windows spellings before filesystem resolution."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise GuardViolation("invalid_arguments")
    raw = value.strip()
    normalized = raw.replace("\\", "/")
    lowered = normalized.casefold()
    if lowered.startswith("~/") or lowered == "~":
        raise _path_violation()
    if normalized.startswith("//") or normalized.startswith("/"):
        raise _path_violation()

    drive, _ = ntpath.splitdrive(raw)
    is_absolute = ntpath.isabs(raw)
    if drive and not is_absolute:
        raise _path_violation()
    if relative_only and (drive or is_absolute):
        raise _path_violation()

    # Reject traversal rather than normalizing it away. This keeps the accepted
    # spelling and the directory clasp will later consume unambiguous.
    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if ".." in parts:
        raise _path_violation()
    for part in parts:
        if part != part.rstrip(" ."):
            # Win32 commonly strips these suffixes before lookup, which can
            # turn a spelling we inspected into a different filesystem name.
            raise _path_violation()
        # Windows resolves device aliases even when they carry an extension or
        # trailing spaces/dots (for example NUL.txt and AUX ).
        base_name = part.rstrip(" .").split(".", 1)[0].rstrip(" .").casefold()
        if (
            base_name in DOS_DEVICE_NAMES
            or (
                len(base_name) == 4
                and base_name[:3] in {"com", "lpt"}
                and base_name[3] in "123456789"
            )
        ):
            raise _path_violation()

    # A colon is valid only as the separator of an absolute drive prefix. Any
    # other colon can address an NTFS alternate data stream.
    remainder = raw[len(drive) :] if drive else raw
    if ":" in remainder:
        raise _path_violation()
    return raw


def _contains(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath(
            (os.path.normcase(str(root)), os.path.normcase(str(candidate)))
        ) == os.path.normcase(str(root))
    except ValueError:
        return False


def _canonical_workspace_root(root: Path) -> Path:
    """Validate the lexical authority path before resolving its boundary."""
    try:
        lexical = Path(os.path.abspath(root))
        parts = lexical.parts
        if not parts:
            raise OSError
        cursor = Path(parts[0])
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        for index, part in enumerate(parts):
            if index:
                cursor /= part
            metadata = os.lstat(cursor)
            attributes = getattr(metadata, "st_file_attributes", 0)
            if stat.S_ISLNK(metadata.st_mode) or attributes & reparse_flag:
                raise OSError
        if not lexical.is_dir():
            raise OSError
        return lexical.resolve(strict=True)
    except (OSError, RuntimeError):
        raise GuardViolation("workspace_unavailable") from None


def _resolved_nonexistent(path: Path) -> Path:
    """Resolve the nearest existing parent, including junctions and symlinks."""
    missing: list[str] = []
    cursor = path
    while not os.path.lexists(cursor):
        if cursor.parent == cursor:
            raise _path_violation()
        missing.append(cursor.name)
        cursor = cursor.parent
    try:
        resolved = cursor.resolve(strict=True)
    except (OSError, RuntimeError):
        raise _path_violation() from None
    for part in reversed(missing):
        resolved /= part
    return resolved


def _javascript_truthy(value: Any) -> bool:
    """Return JSON value truthiness using JavaScript's Boolean conversion."""
    if value is None or value is False:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value != ""
    # JavaScript arrays and objects are truthy, including empty ones.
    return True


def _invalid_json_constant(_: str) -> None:
    raise ValueError("non-standard JSON numeric constant")


def _validate_project_config(project: Path) -> None:
    """Validate clasp's config file and effective local content directory."""
    config_path = _resolve_within(
        ".clasp.json",
        base=project,
        boundary=project,
        relative_only=True,
    )
    if not config_path.exists():
        return
    if not config_path.is_file():
        raise GuardViolation("invalid_project_config")
    try:
        raw_config = config_path.read_text(encoding="utf-8")
        config = json.loads(raw_config, parse_constant=_invalid_json_constant)
    except (OSError, UnicodeError, ValueError, TypeError):
        raise GuardViolation("invalid_project_config") from None
    if not isinstance(config, dict):
        raise GuardViolation("invalid_project_config")
    if _javascript_truthy(config.get("allowSymlinks")):
        raise GuardViolation("invalid_project_config")

    effective: Any = "."
    for field in ("srcDir", "rootDir"):
        candidate = config.get(field)
        if _javascript_truthy(candidate):
            effective = candidate
            break
    if not isinstance(effective, str):
        raise GuardViolation("invalid_project_config")
    try:
        _resolve_within(
            effective,
            base=project,
            boundary=project,
            relative_only=True,
        )
    except GuardViolation:
        raise GuardViolation("invalid_project_config") from None


def _validate_claspignore(project: Path) -> None:
    """Require an existing clasp ignore file to resolve inside the project."""
    lexical = project / ".claspignore"
    if not os.path.lexists(lexical):
        return
    try:
        resolved = _resolve_within(
            ".claspignore",
            base=project,
            boundary=project,
            relative_only=True,
        )
    except GuardViolation:
        raise GuardViolation("unsafe_project_tree") from None
    if not resolved.is_file():
        raise GuardViolation("unsafe_project_tree")


def _preflight_project_tree(project: Path) -> None:
    """Reject link-mediated writes before a destructive clasp sync."""
    if not project.exists():
        return
    if not project.is_dir():
        raise GuardViolation("unsafe_project_tree")

    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

    def scan(directory: Path) -> None:
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    # DirEntry.stat(...).st_nlink is not reliable on the
                    # supported Windows Python build; os.lstat returns the
                    # native hard-link count while still avoiding link follow.
                    metadata = os.lstat(entry.path)
                    attributes = getattr(metadata, "st_file_attributes", 0)
                    if entry.is_symlink() or attributes & reparse_flag:
                        raise GuardViolation("unsafe_project_tree")
                    if stat.S_ISREG(metadata.st_mode):
                        if metadata.st_nlink > 1:
                            raise GuardViolation("unsafe_project_tree")
                        continue
                    if stat.S_ISDIR(metadata.st_mode):
                        scan(Path(entry.path))
                        continue
                    raise GuardViolation("unsafe_project_tree")
        except GuardViolation:
            raise
        except OSError:
            raise GuardViolation("unsafe_project_tree") from None

    scan(project)


def _resolve_within(
    value: Any,
    *,
    base: Path,
    boundary: Path,
    relative_only: bool = False,
) -> Path:
    raw = _screen_windows_path(value, relative_only=relative_only)
    drive, _ = ntpath.splitdrive(raw)
    candidate = Path(raw) if drive or ntpath.isabs(raw) else base / Path(raw)

    # Check the lexical path first, then the filesystem-resolved path. The
    # latter catches existing junction/symlink escapes as well as a nonexistent
    # child whose nearest existing parent is a link outside the boundary.
    lexical = Path(os.path.abspath(candidate))
    if not _contains(boundary, lexical):
        raise _path_violation()
    try:
        resolved = (
            lexical.resolve(strict=True)
            if lexical.exists()
            else _resolved_nonexistent(lexical)
        )
    except (OSError, RuntimeError):
        raise _path_violation() from None
    if not _contains(boundary, resolved):
        raise _path_violation()
    return resolved


def validate_tool_call(tool_name: Any, arguments: Any, root: Path) -> Path | None:
    """Authorize one call and return its canonical project path when relevant."""
    if not isinstance(tool_name, str) or tool_name not in ALLOWED_TOOLS:
        raise GuardViolation("tool_denied")
    if tool_name == "list_projects":
        return None
    if not isinstance(arguments, dict):
        raise GuardViolation("invalid_arguments")

    canonical_root = _canonical_workspace_root(root)

    project = _resolve_within(
        arguments.get("projectDir"),
        base=canonical_root,
        boundary=canonical_root,
    )
    _validate_project_config(project)
    _validate_claspignore(project)
    if "sourceDir" in arguments and arguments["sourceDir"] is not None:
        _resolve_within(
            arguments["sourceDir"],
            base=project,
            boundary=project,
            relative_only=True,
        )
    _preflight_project_tree(project)
    return project


def filter_tools_list(response: dict[str, Any]) -> dict[str, Any]:
    """Return a copy containing only tools the guard can authorize."""
    filtered = copy.deepcopy(response)
    result = filtered.get("result")
    if not isinstance(result, dict):
        return filtered
    tools = result.get("tools")
    if not isinstance(tools, list):
        result["tools"] = []
        return filtered
    approved = [
        item
        for item in tools
        if isinstance(item, dict) and item.get("name") in ALLOWED_TOOLS
    ]
    order = {name: index for index, name in enumerate(TOOL_INVENTORY_ORDER)}
    approved.sort(key=lambda item: order[str(item["name"])])
    result["tools"] = approved
    return filtered


def denied_tool_response(
    *, request_id: Any, violation: GuardViolation
) -> dict[str, Any]:
    """Build a generic MCP error result without echoing arguments or paths."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [{"type": "text", "text": "Request denied by AgentCore policy."}],
            "structuredContent": {"error_code": violation.code},
            "isError": True,
        },
    }


def _audit(event: str, *, tool: str = "", reason: str = "") -> None:
    record = {"component": "clasp-mcp-guard", "event": event}
    if tool:
        record["tool"] = tool
    if reason:
        record["reason"] = reason
    sys.stderr.write(json.dumps(record, separators=(",", ":")) + "\n")
    sys.stderr.flush()


def _write_json(payload: Any, lock: threading.Lock) -> None:
    rendered = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    with lock:
        sys.stdout.write(rendered + "\n")
        sys.stdout.flush()


def _pump_upstream_stdout(
    proc: subprocess.Popen[str],
    pending_tools_lists: set[str],
    pending_lock: threading.Lock,
    outstanding: set[str],
    outstanding_condition: threading.Condition,
    output_lock: threading.Lock,
) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except ValueError:
            _audit("upstream_protocol_error", reason="non_json_stdout")
            continue
        if isinstance(payload, dict) and payload.get("id") is not None:
            key = str(payload["id"])
            with pending_lock:
                is_tools_list = key in pending_tools_lists
                pending_tools_lists.discard(key)
            if is_tools_list:
                payload = filter_tools_list(payload)
        _write_json(payload, output_lock)
        if isinstance(payload, dict) and payload.get("id") is not None:
            with outstanding_condition:
                outstanding.discard(str(payload["id"]))
                outstanding_condition.notify_all()


def _forward(proc: subprocess.Popen[str], payload: Any) -> None:
    if proc.stdin is None:
        raise BrokenPipeError
    proc.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
    proc.stdin.flush()


def _handle_message(
    message: Any,
    *,
    root: Path,
    proc: subprocess.Popen[str],
    pending_tools_lists: set[str],
    pending_lock: threading.Lock,
    outstanding: set[str],
    outstanding_condition: threading.Condition,
    output_lock: threading.Lock,
) -> None:
    if not isinstance(message, dict):
        _write_json(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}},
            output_lock,
        )
        return

    method = message.get("method")
    request_id = message.get("id")
    if method is None:
        # JSON-RPC responses carry an id but no method. They belong upstream
        # and must never become locally tracked requests.
        _forward(proc, message)
        return
    if method == "tools/list" and request_id is not None:
        with pending_lock:
            pending_tools_lists.add(str(request_id))
        with outstanding_condition:
            outstanding.add(str(request_id))
        _forward(proc, message)
        return
    if method != "tools/call":
        if request_id is not None:
            with outstanding_condition:
                outstanding.add(str(request_id))
        _forward(proc, message)
        return

    params = message.get("params")
    tool_name = params.get("name") if isinstance(params, dict) else None
    arguments = params.get("arguments", {}) if isinstance(params, dict) else None
    try:
        canonical_project = validate_tool_call(tool_name, arguments, root)
    except GuardViolation as violation:
        _audit(
            "request_denied",
            tool=tool_name if isinstance(tool_name, str) else "invalid",
            reason=violation.code,
        )
        if request_id is not None:
            # A local rejection has no upstream response to sequence it. Wait
            # for already-forwarded requests so initialize always reaches the
            # client before a subsequent guarded result.
            with outstanding_condition:
                outstanding_condition.wait_for(lambda: not outstanding)
            _write_json(
                denied_tool_response(request_id=request_id, violation=violation),
                output_lock,
            )
        return

    _audit("request_forwarded", tool=tool_name)
    forwarded = message
    if canonical_project is not None:
        # Forward the canonical project path we validated so clasp cannot apply
        # a different interpretation to case, separators, or dot components.
        forwarded = copy.deepcopy(message)
        forwarded["params"]["arguments"]["projectDir"] = str(canonical_project)
    # A same-user process can race a path change after validation. Keeping this
    # guard immediately adjacent to dispatch minimizes that unavoidable window;
    # it never confers privileges outside those already held by the local user.
    _forward(proc, forwarded)


def _terminate(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill.exe", "/PID", str(proc.pid), "/T", "/F"],
            check=False,
            capture_output=True,
            text=True,
        )
    else:
        proc.terminate()


def _parse_args(argv: Iterable[str]) -> tuple[Path, list[str]]:
    raw = list(argv)
    if "--" not in raw:
        raise SystemExit("upstream command required after --")
    split = raw.index("--")
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", required=True, type=Path)
    options = parser.parse_args(raw[:split])
    child_argv = raw[split + 1 :]
    if not child_argv:
        raise SystemExit("upstream command required after --")
    return options.root, child_argv


def main(argv: Iterable[str] | None = None) -> int:
    root, child_argv = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        canonical_root = _canonical_workspace_root(root)
    except GuardViolation:
        _audit("startup_denied", reason="workspace_unavailable")
        return 1

    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8", errors="strict")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass

    proc = subprocess.Popen(  # noqa: S603 - exact command is supplied by wrapper
        child_argv,
        cwd=canonical_root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    pending_tools_lists: set[str] = set()
    pending_lock = threading.Lock()
    outstanding: set[str] = set()
    outstanding_condition = threading.Condition()
    output_lock = threading.Lock()
    reader = threading.Thread(
        target=_pump_upstream_stdout,
        args=(
            proc,
            pending_tools_lists,
            pending_lock,
            outstanding,
            outstanding_condition,
            output_lock,
        ),
        daemon=True,
    )
    reader.start()
    try:
        for line in sys.stdin:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except ValueError:
                _write_json(
                    {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
                    output_lock,
                )
                continue
            messages = payload if isinstance(payload, list) else [payload]
            for message in messages:
                _handle_message(
                    message,
                    root=canonical_root,
                    proc=proc,
                    pending_tools_lists=pending_tools_lists,
                    pending_lock=pending_lock,
                    outstanding=outstanding,
                    outstanding_condition=outstanding_condition,
                    output_lock=output_lock,
                )
    except (BrokenPipeError, OSError, ValueError):
        return proc.poll() or 1
    finally:
        try:
            if proc.stdin is not None:
                proc.stdin.close()
        except (BrokenPipeError, OSError, ValueError):
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _terminate(proc)
    return proc.returncode or 0


if __name__ == "__main__":
    raise SystemExit(main())
