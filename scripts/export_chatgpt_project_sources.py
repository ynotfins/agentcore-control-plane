"""Retired ChatGPT static source-package entry point.

The former exporter embedded mutable hashes and a dated handoff in its default
source set. Current AgentCore context is read from the repository authority
chain and recovered through agentcore-memory. Git history preserves the former
implementation for forensic use.
"""

from __future__ import annotations

import argparse


RETIREMENT_MESSAGE = (
    "RETIRED: the static ChatGPT project-source export is not a current context "
    "path. Read PROJECT_ANCHOR.md -> DOC_AUTHORITY.md -> BLUEPRINT.md -> "
    "CONTEXT_BLOCK.md and use agentcore-memory for live recovery."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report retirement of the static ChatGPT source exporter")
    parser.add_argument("--check", action="store_true", help="Confirm that this path is formally retired")
    parser.add_argument("--export-dir", help="Unsupported retired export target")
    args = parser.parse_args()

    print(RETIREMENT_MESSAGE)
    if args.export_dir:
        print("REFUSED: no files were copied; use the live repository authority chain.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
