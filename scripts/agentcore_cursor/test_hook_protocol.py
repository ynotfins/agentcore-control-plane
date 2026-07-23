"""Offline Cursor hook protocol test harness.

Run:
  python scripts/agentcore_cursor/test_hook_protocol.py
  python scripts/agentcore_cursor/test_hook_protocol.py --iterations 100
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
HOOK_CMD = REPO / ".cursor" / "hooks" / "agentcore-hook.cmd"
HOOK_PS1 = REPO / ".cursor" / "hooks" / "agentcore-hook.ps1"
DISPATCHER = REPO / "scripts" / "agentcore_cursor" / "hook_dispatcher.py"
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|password|secret|bearer)\s*[:=]\s*\S+"),
    re.compile(r"(?i)Authorization:\s*Bearer\s+\S+"),
]

FIXTURES: dict[str, dict[str, Any]] = {
    "sessionStart": {
        "event": "sessionStart",
        "session_id": "hook-test-session",
        "workspace_roots": [str(REPO)],
    },
    "beforeSubmitPrompt": {
        "event": "beforeSubmitPrompt",
        "prompt": "Continue.",
        "conversation_id": "hook-test-conv",
        "workspace_roots": [str(REPO)],
    },
    "preToolUse": {
        "event": "preToolUse",
        "tool_name": "Shell",
        "tool_input": {"command": "echo hook-test"},
        "workspace_roots": [str(REPO)],
    },
    "sessionEnd": {
        "event": "sessionEnd",
        "session_id": "hook-test-session",
        "workspace_roots": [str(REPO)],
    },
}


def _run_hook(event: str, payload: dict[str, Any], *, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    body = json.dumps(payload)
    # Prefer the Stage A PowerShell wrapper (reliable stdin on Windows Cursor hosts).
    if HOOK_PS1.is_file():
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(HOOK_PS1),
            "-Event",
            event,
        ]
        cwd = str(REPO)
    elif HOOK_CMD.is_file():
        cmd = [str(HOOK_CMD), event]
        cwd = str(REPO)
    else:
        cmd = [sys.executable, str(DISPATCHER), event]
        cwd = str(REPO)
    proc = subprocess.run(
        cmd,
        input=body,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=cwd,
        env={**os.environ, **(env or {})},
    )
    return proc.returncode, proc.stdout, proc.stderr


def _parse_stdout(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        raise ValueError("empty stdout")
    if "\n" in text:
        raise ValueError("stdout contains extra newlines beyond one JSON document")
    return json.loads(text)


def _assert_no_secrets(text: str) -> None:
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            raise ValueError("secret-like pattern detected in hook output")


def _validate_event(event: str, doc: dict[str, Any]) -> None:
    if event == "sessionStart":
        assert "env" in doc, "sessionStart missing env"
    elif event == "beforeSubmitPrompt":
        assert "continue" in doc, "beforeSubmitPrompt missing continue"
        assert "followup_message" not in doc, "forbidden followup_message"
    elif event == "preToolUse":
        assert doc.get("permission") in ("allow", "deny", "ask"), "preToolUse permission"
    elif event in ("sessionEnd", "stop"):
        assert "followup_message" not in doc, "forbidden followup_message"


def run_fixture(event: str, payload: dict[str, Any], iterations: int) -> None:
    print(f"  fixture {event} x{iterations} ...", flush=True)
    for i in range(iterations):
        code, out, err = _run_hook(event, payload)
        if code not in (0, 2):
            raise RuntimeError(f"{event} iter {i}: unexpected exit {code}, stderr={err[:200]}")
        doc = _parse_stdout(out)
        _assert_no_secrets(out)
        _validate_event(event, doc)
    print(f"    PASS ({iterations} iterations)")


def test_malformed_input() -> None:
    code, out, _ = _run_hook("sessionStart", {"_force_bad": True})
    if code not in (0, 2):
        raise RuntimeError("malformed sessionStart bad exit")
    # Empty stdin path tested via dispatcher directly
    proc = subprocess.run(
        [sys.executable, str(DISPATCHER), "sessionStart"],
        input="",
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(REPO),
    )
    doc = _parse_stdout(proc.stdout)
    _validate_event("sessionStart", doc)


def test_missing_gateway_degraded() -> None:
    env = {"BIFROST_MCP_VIRTUAL_KEY": "", "AGENT_CORE_POSTGRES_PASSWORD": ""}
    code, out, _ = _run_hook(
        "beforeSubmitPrompt",
        FIXTURES["beforeSubmitPrompt"],
        env=env,
    )
    if code != 0:
        raise RuntimeError(f"degraded beforeSubmitPrompt exit {code}")
    doc = _parse_stdout(out)
    assert doc.get("continue") is True, "degraded beforeSubmitPrompt must fail open"


def test_idempotency() -> None:
    payload = FIXTURES["beforeSubmitPrompt"].copy()
    payload["conversation_id"] = f"idempotent-{int(time.time())}"
    code1, out1, _ = _run_hook("beforeSubmitPrompt", payload)
    code2, out2, _ = _run_hook("beforeSubmitPrompt", payload)
    if code1 != 0 or code2 != 0:
        raise RuntimeError("idempotency run failed exit codes")
    d1 = _parse_stdout(out1)
    d2 = _parse_stdout(out2)
    assert d1.get("continue") is True and d2.get("continue") is True


def test_no_orphan_processes() -> None:
    before = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process python,py -ErrorAction SilentlyContinue | Measure-Object).Count"],
        text=True,
    ).strip()
    _run_hook("sessionStart", FIXTURES["sessionStart"])
    time.sleep(0.5)
    after = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process python,py -ErrorAction SilentlyContinue | Measure-Object).Count"],
        text=True,
    ).strip()
    if int(after) > int(before) + 2:
        raise RuntimeError(f"possible orphan python processes: before={before} after={after}")


def test_drive_relative_root_rejected() -> None:
    """Drive-relative workspace roots must not create a phantom tree under the repo."""
    phantom = REPO / "github" / "agentcore-control-plane"
    if phantom.exists():
        shutil.rmtree(phantom)
    payload = {
        "event": "sessionStart",
        "session_id": "hook-test-drive-relative",
        "workspace_roots": ["d:github\\agentcore-control-plane"],
    }
    code, out, err = _run_hook("sessionStart", payload)
    if code not in (0, 2):
        raise RuntimeError(f"sessionStart drive-relative exit {code}, stderr={err[:200]}")
    doc = _parse_stdout(out)
    _validate_event("sessionStart", doc)
    if phantom.exists():
        raise RuntimeError("phantom tree regenerated from drive-relative workspace root")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--events", nargs="*", default=list(FIXTURES))
    args = parser.parse_args()

    if not DISPATCHER.is_file():
        print("FAIL: hook dispatcher missing", file=sys.stderr)
        return 2
    if not HOOK_CMD.is_file():
        print("WARN: agentcore-hook.cmd missing; testing dispatcher directly", file=sys.stderr)

    print("AgentCore Cursor hook protocol harness")
    print(f"  repo={REPO}")
    print(f"  hook_cmd={HOOK_CMD}")
    print(f"  dispatcher={DISPATCHER}")

    for event in args.events:
        if event not in FIXTURES:
            print(f"SKIP unknown event {event}")
            continue
        run_fixture(event, FIXTURES[event], args.iterations)

    print("  special: malformed input")
    test_malformed_input()
    print("    PASS")

    print("  special: missing gateway degraded")
    test_missing_gateway_degraded()
    print("    PASS")

    print("  special: idempotency")
    test_idempotency()
    print("    PASS")

    print("  special: orphan process check")
    test_no_orphan_processes()
    print("    PASS")

    print("  special: drive-relative root rejected")
    test_drive_relative_root_rejected()
    print("    PASS")

    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
