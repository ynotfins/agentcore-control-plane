"""Operator CLI: python -m agentcore cursor {recover,status,new-task,resume}."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from agentcore_cursor.bootstrap import (  # noqa: E402
    DEFAULT_AGENT_KEY,
    load_bootstrap_json,
    run_bootstrap,
)


def _summarize_bootstrap(data: dict[str, Any]) -> dict[str, Any]:
    """Extract key fields from a bootstrap JSON payload."""
    result = data.get("result") if isinstance(data, dict) else None
    if not isinstance(result, dict):
        result = {}
    return {
        "session_key": result.get("session_key"),
        "session_id": result.get("session_id"),
        "continuity_status": result.get("continuity_status"),
    }


def _read_session_scope(root: Path) -> dict[str, Any]:
    """Optionally read .agentcore/runtime/session-scope.json without creating it."""
    summary: dict[str, Any] = {
        "intent_declared": None,
        "acceptance_count": 0,
        "declared_file_count": 0,
        "observed_file_count": 0,
        "tool_event_count": 0,
        "final_review_present": False,
    }
    scope_path = root / ".agentcore" / "runtime" / "session-scope.json"
    if not scope_path.is_file():
        return summary
    try:
        payload = json.loads(scope_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return summary
    if not isinstance(payload, dict):
        return summary
    intent = payload.get("intent")
    if intent is not None:
        summary["intent_declared"] = bool(intent)
    for key, target in (
        ("acceptance", "acceptance_count"),
        ("declared_files", "declared_file_count"),
        ("observed_files", "observed_file_count"),
    ):
        value = payload.get(key)
        if isinstance(value, list):
            summary[target] = len(value)
    evidence = payload.get("required_tool_evidence")
    if isinstance(evidence, dict) and isinstance(evidence.get("tool_events"), list):
        summary["tool_event_count"] = len(evidence["tool_events"])
    review = payload.get("final_review")
    if review is not None:
        summary["final_review_present"] = bool(review)
    return summary


def _print(data: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, default=str))
    elif isinstance(data, dict):
        for key, value in data.items():
            if key in {"startup_summary"} and isinstance(value, str):
                print(f"{key}:")
                print(value[:2000])
            else:
                print(f"{key}: {value}")
    else:
        print(data)


def cmd_recover(args: argparse.Namespace) -> int:
    result = run_bootstrap(
        workspace=args.workspace,
        agent_key=args.agent_key,
        force_new_task=False,
    )
    _print(result.as_dict(), args.json)
    return 0 if result.ok else 2


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.workspace).resolve() if args.workspace else Path.cwd().resolve()
    data = load_bootstrap_json(root) or {}
    summary = _summarize_bootstrap(data)
    scope = _read_session_scope(root)
    out = {
        "workspace": str(root),
        "bootstrap": data.get("result"),
        "session_key": summary.get("session_key"),
        "session_id": summary.get("session_id"),
        "continuity_status": summary.get("continuity_status"),
        "bootstrap_generated_at": data.get("generated_at"),
        "session_scope": scope,
    }
    _print(out, args.json)
    return 0


def cmd_new_task(args: argparse.Namespace) -> int:
    result = run_bootstrap(
        workspace=args.workspace,
        agent_key=args.agent_key,
        force_new_task=True,
        task_slug=args.slug,
    )
    _print(result.as_dict(), args.json)
    return 0 if result.ok else 2


def cmd_resume(args: argparse.Namespace) -> int:
    root = Path(args.workspace).resolve() if args.workspace else Path.cwd().resolve()
    result = run_bootstrap(
        workspace=str(root),
        agent_key=args.agent_key,
        force_new_task=False,
        session_key=args.session_key,
    )
    _print(result.as_dict(), args.json)
    return 0 if result.ok else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentcore cursor")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_recover = sub.add_parser("recover", help="Run new-chat bootstrap now")
    p_recover.add_argument("--workspace", default=None)
    p_recover.add_argument("--agent-key", default=DEFAULT_AGENT_KEY)
    p_recover.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    p_recover.set_defaults(func=cmd_recover)

    p_status = sub.add_parser("status", help="Show project-bound bootstrap + session scope")
    p_status.add_argument("--workspace", default=None)
    p_status.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    p_status.set_defaults(func=cmd_status)

    p_new = sub.add_parser("new-task", help="Start a new task session")
    p_new.add_argument("--workspace", default=None)
    p_new.add_argument("--agent-key", default=DEFAULT_AGENT_KEY)
    p_new.add_argument("--slug", default=None)
    p_new.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    p_new.set_defaults(func=cmd_new_task)

    p_resume = sub.add_parser(
        "resume",
        help="Bind session_key and bootstrap (no global pointer file)",
    )
    p_resume.add_argument("--session-key", required=True)
    p_resume.add_argument("--workspace", default=None)
    p_resume.add_argument("--project-key", default=None)
    p_resume.add_argument("--agent-key", default=DEFAULT_AGENT_KEY)
    p_resume.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    p_resume.set_defaults(func=cmd_resume)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
