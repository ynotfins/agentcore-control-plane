"""Bootstrap AgentCore Deep Agent prompts in Langfuse.

Usage (from D:\\github\\agentcore-control-plane):
    python scripts/agentcore_workflow/langfuse_bootstrap_prompts.py
    python scripts/agentcore_workflow/langfuse_bootstrap_prompts.py --dry-run

Requires Windows User-scope env vars (names only):
    LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from agentcore_workflow.langfuse_integration import (  # noqa: E402
    PROMPT_DEFINITIONS,
    bootstrap_prompts,
    has_langfuse_credentials,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload AgentCore prompts to Langfuse")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompt inventory without calling Langfuse",
    )
    args = parser.parse_args()

    if not args.dry_run and not has_langfuse_credentials():
        print(
            "ERROR: Langfuse credentials missing. Set LANGFUSE_PUBLIC_KEY, "
            "LANGFUSE_SECRET_KEY, and LANGFUSE_BASE_URL in Windows User env.",
            file=sys.stderr,
        )
        return 2

    inventory = {
        name: {
            "type": spec["type"],
            "labels": spec.get("labels", []),
            "variable_count": spec["prompt"].count("{{"),
        }
        for name, spec in PROMPT_DEFINITIONS.items()
    }
    print(json.dumps({"prompts": inventory}, indent=2))

    if args.dry_run:
        print("Dry run — no prompts uploaded.")
        return 0

    results = bootstrap_prompts(dry_run=False)
    print(json.dumps({"uploaded": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
