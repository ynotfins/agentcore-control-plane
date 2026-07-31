#!/usr/bin/env python3
"""Validate AgentCore/Swarm separation header + prohibited continuity language.

Scoped gate for the four authority docs rewritten in the 2026-07-31 reconciliation.
Exit: 0 pass, 1 fail.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [
    REPO / "PROJECT_ANCHOR.md",
    REPO / "MASTER_CONFIG_AND_PROMPT.md",
    REPO / "MILESTONES.md",
    REPO / "BLUEPRINT.md",
]
HEADER = "## Ecosystem and Drive Separation — Read First"
REQUIRED_PHRASES = [
    "independent control planes",
    r"F:\\AgentCore",
    r"E:\\AgentCore",
    r"E:\\Swarm",
    "No canonical resource may be jointly owned",
    "historical evidence only",
]
# Allowed only when clearly revoking / forbidding the old continuity model.
FORBIDDEN_ALLOWANCE = re.compile(
    r"(?is)may use AgentCore for development continuity on\s+Swarm"
)


def main() -> int:
    errors: list[str] = []
    for path in FILES:
        if not path.is_file():
            errors.append(f"missing: {path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        # Header must appear early (within first ~40 non-empty lines after title).
        lines = [ln for ln in text.splitlines() if ln.strip()]
        head = "\n".join(lines[:40])
        if HEADER not in head:
            errors.append(f"{path.name}: missing early '{HEADER}'")
        for phrase in REQUIRED_PHRASES:
            if not re.search(phrase, text, re.IGNORECASE):
                errors.append(f"{path.name}: missing required separation phrase / pattern: {phrase}")
        # H:\AgentRuntime must not be asserted as the live Bifrost/current AgentCore home.
        for m in re.finditer(r"(?im)^(.*H:\\AgentRuntime.*)$", text):
            line = m.group(1)
            if re.search(
                r"(?i)(historical|vacated|not |must not|forbidden|treating|do not|never|refuse|rollback|inventory|retired)",
                line,
            ):
                continue
            if re.search(r"(?i)(live Bifrost|current (state|Bifrost|runtime)|runtime is at H:)", line):
                errors.append(f"{path.name}: H:\\AgentRuntime framed as current AgentCore runtime: {line.strip()[:120]}")
        if FORBIDDEN_ALLOWANCE.search(text):
            errors.append(f"{path.name}: restores AgentCore IDE continuity allowance on Swarm projects")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print(f"PASS: separation header + continuity gate for {len(FILES)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
