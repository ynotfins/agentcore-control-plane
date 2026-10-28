#!/usr/bin/env python3
"""Transparent MCP stdio normalizer for the AgentCore Bifrost gateway.

Sits between Bifrost and one upstream MCP stdio server. It is a byte-faithful
JSON-RPC relay except for two additive transforms:

  tools/list result -> every tool without an outputSchema gets the AgentCore
                       envelope schema for its contract-declared family.
  tools/call result -> every result without a conforming structuredContent gets
                       one built from the upstream payload. content[] blocks are
                       never modified, reordered, or dropped.

Design constraints:
  * No new MCP route and no new tool. This is an in-line adapter on an existing
    upstream stdio connection, injected by scripts/bifrost/render_bifrost_config.py.
  * Fail open. Any load/parse/transform problem degrades to raw passthrough so a
    schema bug can never take the gateway tool surface down.
  * stdlib only.

Usage (as rendered into Bifrost stdio_config):
  python -u mcp_output_schema_adapter.py --server <canonical_id> \
      [--contract <path>] [--allow-env NAME] [--alias-env CHILD=PARENT] \
      -- <upstream_command> [upstream_args...]

Offline check:
  python mcp_output_schema_adapter.py --self-test
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mcp_output_schema as mos  # noqa: E402

MAX_PENDING = 4096

# These are the Windows process variables needed by cmd-backed launchers,
# Node/npm, Python, and PowerShell. All other values are opt-in per upstream.
WINDOWS_REQUIRED_ENV_NAMES = (
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "PATH",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
)
ENV_NAME_PATTERN = re.compile(r"[A-Z_][A-Z0-9_]*\Z")


def _read_windows_user_environment(name: str) -> str | None:
    """Read one explicitly requested value from the current user's environment."""
    if os.name != "nt":
        return None

    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Environment",
            access=winreg.KEY_QUERY_VALUE,
        ) as environment_key:
            value, value_type = winreg.QueryValueEx(environment_key, name)
    except (ImportError, OSError):
        return None

    if value_type not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
        return None
    return value if isinstance(value, str) else None


def build_child_environment(
    parent_env: Mapping[str, str],
    *,
    declared_env_names: list[str],
    static_env: dict[str, str],
    user_env_resolver: Callable[[str], str | None] | None = None,
    env_aliases: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return the minimal environment permitted to one STDIO upstream child."""
    parent_by_name = {name.upper(): value for name, value in parent_env.items()}
    declared_by_name = {name.upper() for name in declared_env_names}
    reserved_child_names = {
        *(name.upper() for name in WINDOWS_REQUIRED_ENV_NAMES),
        *declared_by_name,
        *(name.upper() for name in static_env),
    }
    for child_name in env_aliases or {}:
        if child_name.upper() in reserved_child_names:
            raise ValueError(
                "env alias child conflicts with existing child environment: "
                f"{child_name}"
            )
    allowed_names = dict.fromkeys([*WINDOWS_REQUIRED_ENV_NAMES, *declared_env_names])
    child_env: dict[str, str] = {}
    for name in allowed_names:
        normalized_name = name.upper()
        if normalized_name in parent_by_name:
            value = parent_by_name[normalized_name]
        elif normalized_name in declared_by_name and user_env_resolver is not None:
            value = user_env_resolver(name)
        else:
            value = None
        if value:
            child_env[name] = value
    for child_name, parent_name in (env_aliases or {}).items():
        normalized_parent_name = parent_name.upper()
        if normalized_parent_name in parent_by_name:
            value = parent_by_name[normalized_parent_name]
        elif user_env_resolver is not None:
            value = user_env_resolver(parent_name)
        else:
            value = None
        if value:
            child_env[child_name] = value
    child_env.update(static_env)
    return child_env


def launch_upstream(
    child_argv: list[str],
    *,
    declared_env_names: list[str],
    static_env: dict[str, str],
    parent_env: Mapping[str, str] | None = None,
    env_aliases: Mapping[str, str] | None = None,
) -> subprocess.Popen[str]:
    """Launch an upstream child with its reviewed Windows environment only."""
    return subprocess.Popen(  # noqa: S603 - command comes from the rendered registry
        child_argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=build_child_environment(
            os.environ if parent_env is None else parent_env,
            declared_env_names=declared_env_names,
            static_env=static_env,
            user_env_resolver=(
                _read_windows_user_environment if parent_env is None else None
            ),
            env_aliases=env_aliases,
        ),
    )


def _log(message: str) -> None:
    sys.stderr.write(f"[mcp-output-schema-adapter] {message}\n")
    sys.stderr.flush()


def _terminate(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


class Relay:
    def __init__(self, server_id: str, resolver: mos.OutputSchemaResolver | None) -> None:
        self.server_id = server_id
        self.resolver = resolver
        self._pending: dict[str, tuple[str, str]] = {}
        self._lock = threading.Lock()

    # -- request side (Bifrost -> upstream) ---------------------------------
    def note_request(self, msg: dict[str, Any]) -> None:
        method = msg.get("method")
        req_id = msg.get("id")
        if req_id is None or method not in ("tools/list", "tools/call"):
            return
        tool = ""
        if method == "tools/call":
            params = msg.get("params")
            if isinstance(params, dict) and isinstance(params.get("name"), str):
                tool = params["name"]
        with self._lock:
            if len(self._pending) >= MAX_PENDING:
                self._pending.clear()
            self._pending[str(req_id)] = (str(method), tool)

    # -- response side (upstream -> Bifrost) --------------------------------
    def transform_response(self, msg: dict[str, Any]) -> dict[str, Any]:
        req_id = msg.get("id")
        if req_id is None:
            return msg
        with self._lock:
            entry = self._pending.pop(str(req_id), None)
        if entry is None or self.resolver is None:
            return msg
        method, tool = entry
        result = msg.get("result")
        if not isinstance(result, dict):
            return msg
        if method == "tools/list":
            mos.inject_output_schemas(result, server=self.server_id, resolver=self.resolver)
        elif method == "tools/call" and tool:
            mos.normalize_call_result(
                result, tool=tool, server=self.server_id, resolver=self.resolver
            )
        return msg


def _pump_stdin(proc: subprocess.Popen[str], relay: Relay) -> None:
    """Bifrost -> upstream. Never rewrites the request payload."""
    try:
        for line in sys.stdin:
            if proc.stdin is None:
                break
            stripped = line.strip()
            if stripped:
                try:
                    parsed = json.loads(stripped)
                except ValueError:
                    parsed = None
                if isinstance(parsed, dict):
                    relay.note_request(parsed)
                elif isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict):
                            relay.note_request(item)
            try:
                proc.stdin.write(line if line.endswith("\n") else line + "\n")
                proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                break
    finally:
        try:
            if proc.stdin is not None:
                proc.stdin.close()
        except (BrokenPipeError, OSError, ValueError):
            pass


def _pump_stdout(proc: subprocess.Popen[str], relay: Relay) -> None:
    """Upstream -> Bifrost, with additive schema/structuredContent injection."""
    assert proc.stdout is not None
    for line in proc.stdout:
        stripped = line.strip()
        if not stripped:
            continue
        out = stripped
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                parsed = relay.transform_response(parsed)
                out = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)
            elif isinstance(parsed, list):
                parsed = [
                    relay.transform_response(item) if isinstance(item, dict) else item
                    for item in parsed
                ]
                out = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001 - fail open, never drop a message
            _log(f"passthrough (transform skipped): {exc.__class__.__name__}")
            out = stripped
        try:
            sys.stdout.write(out + "\n")
            sys.stdout.flush()
        except (BrokenPipeError, OSError, ValueError):
            break


def _split_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    if "--" in argv:
        index = argv.index("--")
        return argv[:index], argv[index + 1 :]
    return argv, []


def _parse_options(options: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    index = 0
    while index < len(options):
        token = options[index]
        if token in ("--server", "--contract"):
            if index + 1 >= len(options):
                raise SystemExit(f"{token} requires a value")
            parsed[token.lstrip("-")] = options[index + 1]
            index += 2
            continue
        if token in ("--allow-env", "--alias-env", "--static-env"):
            if index + 1 >= len(options):
                raise SystemExit(f"{token} requires a value")
            parsed.setdefault(token.lstrip("-"), []).append(options[index + 1])
            index += 2
            continue
        if token == "--no-transform":
            parsed["no-transform"] = True
            index += 1
            continue
        if token == "--self-test":
            parsed["self-test"] = "1"
            index += 1
            continue
        raise SystemExit(f"unknown adapter option: {token}")
    return parsed


def _parse_static_env(values: list[str]) -> dict[str, str]:
    static_env: dict[str, str] = {}
    for value in values:
        name, separator, env_value = value.partition("=")
        if not separator or not name:
            raise SystemExit("--static-env requires NAME=VALUE")
        static_env[name] = env_value
    return static_env


def _parse_env_aliases(
    values: list[str],
    *,
    reserved_child_names: list[str] | tuple[str, ...] = (),
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    reserved = {name.upper() for name in reserved_child_names}
    for value in values:
        child_name, separator, parent_name = value.partition("=")
        if (
            not separator
            or not ENV_NAME_PATTERN.fullmatch(child_name)
            or not ENV_NAME_PATTERN.fullmatch(parent_name)
        ):
            raise SystemExit(
                "--alias-env requires CHILD=PARENT with uppercase environment identifiers"
            )
        if child_name in aliases:
            raise SystemExit(f"duplicate --alias-env child: {child_name}")
        if child_name in reserved:
            raise SystemExit(
                "--alias-env child conflicts with existing child environment: "
                f"{child_name}"
            )
        aliases[child_name] = parent_name
    return aliases


def main(argv: list[str] | None = None) -> int:
    raw = list(argv if argv is not None else sys.argv[1:])
    options_argv, child_argv = _split_argv(raw)
    options = _parse_options(options_argv)

    if options.get("self-test"):
        failures = mos.self_test(
            mos.OutputSchemaResolver(contract_path=options.get("contract"))
        )
        if failures:
            print(f"FAILED ({len(failures)})")
            for item in failures:
                print(f"  - {item}")
            return 1
        print("OK: adapter self-test passed")
        return 0

    server_id = options.get("server")
    if not server_id:
        raise SystemExit("--server <canonical_id> is required")
    if not child_argv:
        raise SystemExit("upstream command required after --")

    resolver: mos.OutputSchemaResolver | None = None
    if not options.get("no-transform"):
        try:
            resolver = mos.OutputSchemaResolver(contract_path=options.get("contract"))
            if resolver.adapter_mode(server_id) != "stdio_envelope":
                _log(
                    f"{server_id}: contract adapter mode is "
                    f"{resolver.adapter_mode(server_id)!r}; relaying without transforms"
                )
                resolver = None
        except Exception as exc:  # noqa: BLE001 - never block the upstream launch
            _log(f"{server_id}: contract unavailable ({exc.__class__.__name__}); raw passthrough")
            resolver = None

    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass

    declared_env_names = list(options.get("allow-env") or [])
    static_env = _parse_static_env(list(options.get("static-env") or []))
    env_aliases = _parse_env_aliases(
        list(options.get("alias-env") or []),
        reserved_child_names=[
            *WINDOWS_REQUIRED_ENV_NAMES,
            *declared_env_names,
            *static_env,
        ],
    )
    proc = launch_upstream(
        child_argv,
        declared_env_names=declared_env_names,
        static_env=static_env,
        env_aliases=env_aliases,
    )

    relay = Relay(server_id, resolver)
    writer = threading.Thread(target=_pump_stdin, args=(proc, relay), daemon=True)
    writer.start()
    try:
        _pump_stdout(proc, relay)
        return proc.wait()
    finally:
        _terminate(proc)


if __name__ == "__main__":
    raise SystemExit(main())
