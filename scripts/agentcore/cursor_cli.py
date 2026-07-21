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
    load_pointer,
    run_bootstrap,
    save_pointer,
)


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
    pointer = load_pointer()
    out = {
        "workspace": str(root),
        "bootstrap": data.get("result"),
        "pointer": pointer,
        "bootstrap_generated_at": data.get("generated_at"),
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
    project_key = args.project_key or root.name
    pointer = load_pointer()
    pointer[project_key] = {
        "session_key": args.session_key,
        "agent_key": args.agent_key,
        "client_key": "cursor",
        "updated_at": __import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .isoformat(),
    }
    save_pointer(pointer)
    result = run_bootstrap(
        workspace=str(root),
        agent_key=args.agent_key,
        force_new_task=False,
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
    p_recover.set_defaults(func=cmd_recover)

    p_status = sub.add_parser("status", help="Show bootstrap + active task pointer")
    p_status.add_argument("--workspace", default=None)
    p_status.set_defaults(func=cmd_status)

    p_new = sub.add_parser("new-task", help="Start a new task session")
    p_new.add_argument("--workspace", default=None)
    p_new.add_argument("--agent-key", default=DEFAULT_AGENT_KEY)
    p_new.add_argument("--slug", default=None)
    p_new.set_defaults(func=cmd_new_task)

    p_resume = sub.add_parser("resume", help="Bind pointer to a session_key and bootstrap")
    p_resume.add_argument("--session-key", required=True)
    p_resume.add_argument("--workspace", default=None)
    p_resume.add_argument("--project-key", default=None)
    p_resume.add_argument("--agent-key", default=DEFAULT_AGENT_KEY)
    p_resume.set_defaults(func=cmd_resume)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
