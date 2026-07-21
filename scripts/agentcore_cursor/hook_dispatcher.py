"""Deterministic Cursor hook dispatcher — JSON stdin, exactly one JSON stdout document.

Diagnostics go to stderr and bounded log files under H:\\AgentRuntime\\clients\\cursor\\logs\\hooks\\
Never emits followup_message or fabricates operator prompts.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from agentcore_cursor.hooks import HANDLERS  # noqa: E402

LOG_ROOT = Path(
    os.environ.get(
        "AGENTCORE_CURSOR_HOOK_LOG_ROOT",
        r"H:\AgentRuntime\clients\cursor\logs\hooks",
    )
)
MAX_STDOUT_BYTES = 512_000
EVENT_TIMEOUT_SEC = float(os.environ.get("AGENTCORE_HOOK_TIMEOUT_SEC", "85"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(event: str, message: str, *, exc: BaseException | None = None) -> None:
    try:
        LOG_ROOT.mkdir(parents=True, exist_ok=True)
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        line = f"{_now()} [{event}] {message}"
        if exc is not None:
            line += f" | {type(exc).__name__}: {exc}"
        path = LOG_ROOT / f"hook-{day}.log"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            if exc is not None:
                fh.write(traceback.format_exc() + "\n")
    except OSError:
        pass
    # Mirror concise diagnostics to stderr only (never stdout).
    sys.stderr.write(line + "\n")


def _read_stdin() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {"_malformed_stdin": True, "_raw_len": len(raw)}


def _emit(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    if len(text.encode("utf-8")) > MAX_STDOUT_BYTES:
        text = json.dumps(
            {
                "error": "response_truncated",
                "note": "AgentCore hook response exceeded size cap",
            },
            ensure_ascii=False,
        )
    sys.stdout.write(text)
    sys.stdout.flush()


def _controlled_error(event: str, exc: BaseException) -> dict[str, Any]:
    """Return a safe response that must not brick Cursor tools."""
    msg = f"{type(exc).__name__}: {str(exc)[:180]}"
    if event == "sessionStart":
        return {
            "env": {
                "AGENTCORE_BOOTSTRAP_OK": "0",
                "AGENTCORE_BOOTSTRAP_ERROR": msg,
            }
        }
    if event == "beforeSubmitPrompt":
        # Fail open: allow operator submission; spool/bootstrap may catch up later.
        return {"continue": True, "agent_message": f"AgentCore hook degraded: {msg}"}
    if event == "preToolUse":
        # Fail open: never deny all tools because the dispatcher crashed.
        return {"permission": "allow", "agent_message": f"AgentCore hook degraded: {msg}"}
    if event in ("sessionEnd", "stop"):
        return {}
    return {}


def _dispatch(event: str, payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("_malformed_stdin"):
        _log(event, "malformed stdin JSON")
        if event == "sessionStart":
            return {"env": {"AGENTCORE_BOOTSTRAP_OK": "0"}}
        if event == "beforeSubmitPrompt":
            return {"continue": True}
        if event == "preToolUse":
            return {"permission": "allow"}
        return {}

    handler = HANDLERS.get(event)
    if handler is None:
        return {}
    return handler(payload)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        _emit({"error": "missing_hook_event"})
        return 2

    event = args[0]
    payload = _read_stdin()

    try:
        result = _dispatch(event, payload)
        if not isinstance(result, dict):
            result = {}
        _emit(result)
        return 0
    except Exception as exc:  # noqa: BLE001
        _log(event, "dispatcher exception", exc=exc)
        _emit(_controlled_error(event, exc))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
