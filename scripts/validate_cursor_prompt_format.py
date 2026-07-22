#!/usr/bin/env python3
"""Validate Cursor prompt-format rules (absolute @-paths and continuation section).

Canonical policy: contracts/global-agent-policy.yaml rule cursor-prompt-path-format.

Checks a prompt/markdown file for:
1. File/folder references that look like required reads use @ + absolute Windows paths.
2. User-profile paths use the full C:\\Users\\ynotf prefix (no C:\\Users\\... ellipsis).
3. When the document claims further Cursor work is required, a
   CURSOR CONTINUATION PROMPT section is present.

Usage:
  python scripts/validate_cursor_prompt_format.py path1 [path2 ...]
  python scripts/validate_cursor_prompt_format.py --self-test

Exit codes: 0 pass, 1 fail, 2 usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Bare path-like tokens that should have been @-prefixed when instructing Cursor to read.
BARE_REPO_PATH = re.compile(
    r"(?m)(?<!@)(?<![\w./\\-])((?:[A-Za-z]:\\(?:Users\\[^\\\s]+)\\[^\s`\"')\]]+)|"
    r"(?:(?:docs|contracts|ide-profiles|audits|scripts|ops)\\[^\s`\"')\]]+\.(?:md|yaml|yml|json|py)))"
)
ELLIPSIS_USER = re.compile(r"C:\\Users\\\.\.\.", re.IGNORECASE)
ABS_AT_PATH = re.compile(r"@[A-Za-z]:\\[^\s`\"')\]]+")
CONTINUATION_HEADER = re.compile(r"(?im)^#{1,3}\s*CURSOR CONTINUATION PROMPT\b|^CURSOR CONTINUATION PROMPT\b")
FURTHER_WORK = re.compile(
    r"(?i)\b(further Cursor work|continuation prompt|ready-to-paste|follow-on Cursor|next Cursor)\b"
)


def validate_text(text: str, *, require_continuation_if_flagged: bool = True) -> list[str]:
    errors: list[str] = []
    if ELLIPSIS_USER.search(text):
        errors.append("found shortened user-profile path form C:\\Users\\...; use @C:\\Users\\ynotf\\...")

    # Flag bare absolute C:/D: paths that are not @-prefixed (common authority list mistakes).
    for m in re.finditer(r"(?m)(?<!@)(?<![A-Za-z0-9_])([A-Za-z]:\\(?:github|Users)\\[^\s`\"')\]]+)", text):
        path = m.group(1)
        # Allow inside code fences only if they are examples of bad forms — still flag.
        errors.append(f"absolute path missing @ prefix: {path}")

    if require_continuation_if_flagged and FURTHER_WORK.search(text) and not CONTINUATION_HEADER.search(text):
        errors.append("document references further Cursor work but lacks a CURSOR CONTINUATION PROMPT section")

    # Presence of at least one valid @-path is expected when authority files are listed.
    if "authority" in text.lower() and "read" in text.lower() and not ABS_AT_PATH.search(text):
        # Soft signal only when the file looks like a Cursor prompt packet.
        if re.search(r"(?i)cursor|@d:\\\\github|required authority", text):
            errors.append("authority/read prompt has no @-prefixed absolute Windows paths")

    return errors


def validate_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: {e}" for e in validate_text(text)]


def self_test() -> int:
    good = (
        "Read @D:\\github\\agentcore-control-plane\\BLUEPRINT.md and "
        "@C:\\Users\\ynotf\\.cursor\\plans\\x.plan.md\n\n"
        "## CURSOR CONTINUATION PROMPT\n\nContinue MiniMax Classic acceptance.\n"
    )
    bad = (
        "Read BLUEPRINT.md and docs\\operations\\x.md and C:\\Users\\...\\.cursor\\plans\\x.plan.md\n"
        "Further Cursor work is required.\n"
    )
    g_err = validate_text(good)
    b_err = validate_text(bad)
    if g_err:
        print("SELF-TEST FAIL: good sample errors:", g_err)
        return 1
    if not b_err:
        print("SELF-TEST FAIL: bad sample produced no errors")
        return 1
    print("SELF-TEST PASS")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.paths:
        parser.print_help()
        return 2
    errors: list[str] = []
    for p in args.paths:
        if not p.is_file():
            errors.append(f"{p}: not a file")
            continue
        errors.extend(validate_file(p))
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print(f"PASS: {len(args.paths)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
