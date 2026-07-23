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


def _stdin_preview(raw: str) -> str:
    """Bounded, redacted preview for diagnostics (never log full prompts/secrets).

    Includes a hex preview when the raw bytes contain non-ASCII or control
    characters, which helps diagnose encoding/escaping defects.
    """
    for token in ("Bearer ", "password", "api_key", "secret"):
        if token.lower() in raw.lower():
            return f"<redacted len={len(raw)}>"
    sample = raw[:120].replace("\r", "\\r").replace("\n", "\\n")
    prefix = raw[:40]
    if any(ord(c) > 127 or c in "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f" for c in prefix):
        hex_preview = prefix.encode("utf-8", errors="replace").hex()
        return f"len={len(raw)} hex_preview={hex_preview} text_preview={sample!r}"
    return f"len={len(raw)} preview={sample!r}"


def _parse_hook_json(raw: str) -> dict[str, Any] | None:
    """Parse the hook JSON payload, tolerating trailing garbage and embedded braces.

    Cursor occasionally appends extra whitespace, trailing control characters, or
    other data after the JSON object. The parser extracts the first valid object
    by scanning from the first ``{`` to each subsequent ``}`` rather than using
    the last ``}`` in the entire buffer, which avoids mis-parsing prompts that
    contain brace characters.
    """
    text = raw.strip()
    if not text:
        return {}
    # Fast path: a single well-formed object.
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return {}
    except json.JSONDecodeError:
        pass
    # Tolerate leading junk and trailing garbage by finding the first valid object.
    start = text.find("{")
    if start < 0:
        return None
    # Scan forward to each closing brace; return the first complete dict.
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    data = json.loads(text[start : i + 1])
                    if isinstance(data, dict):
                        return data
                except json.JSONDecodeError:
                    continue
    return None


def _read_stdin() -> dict[str, Any]:
    try:
        raw_bytes = sys.stdin.buffer.read()
    except Exception:  # noqa: BLE001
        raw_bytes = b""
    if not raw_bytes:
        return {}
    raw = raw_bytes.decode("utf-8-sig", errors="replace")
    parsed = _parse_hook_json(raw)
    if parsed is None:
        return {
            "_malformed_stdin": True,
            "_raw_len": len(raw),
            "_raw_preview": _stdin_preview(raw),
        }
    return parsed


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
        preview = str(payload.get("_raw_preview") or f"len={payload.get('_raw_len')}")
        _log(event, f"malformed stdin JSON ({preview})")
        if event == "sessionStart":
            return {"env": {"AGENTCORE_BOOTSTRAP_OK": "0"}}
        if event == "beforeSubmitPrompt":
            return {"continue": True}
        if event == "preToolUse":
            return {"permission": "allow"}
        return {}

    # Some Cursor builds include hook_event_name inside the JSON; prefer argv event.
    if not event and isinstance(payload.get("hook_event_name"), str):
        event = str(payload["hook_event_name"])

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
