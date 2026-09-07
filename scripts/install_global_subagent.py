#!/usr/bin/env python3
"""Install a canonical sub-agent definition into the global Cursor agents directory.

Safety contract (deliberately narrow):
  * Only ever writes a single ``*.md`` file.
  * The ONLY writable destination is the global Cursor agents dir
    (``~/.cursor/agents`` by default, override with ``--agents-dir``). Any resolved
    destination outside that directory is refused.
  * The source must be a real ``*.md`` file with valid sub-agent frontmatter
    (``name`` + ``description`` at minimum).
  * Any existing destination file is backed up to ``<name>.<UTC-timestamp>.bak``
    before being overwritten.
  * ``--dry-run`` performs every check and prints the plan without writing.

This script performs a client-local IDE-configuration write only. It does not touch
project source, contracts, governed docs, or runtime state.

Usage:
  python scripts/install_global_subagent.py --source global-subagents/docs-guardian.md
  python scripts/install_global_subagent.py --source <file.md> --dry-run
  python scripts/install_global_subagent.py --source <file.md> --name my-agent
  python scripts/install_global_subagent.py --source <file.md> \
      --agents-dir "C:\\Users\\ynotf\\.cursor\\agents"
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import shutil
import sys
from pathlib import Path

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _fail(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract a minimal YAML frontmatter block. Values are returned as raw strings.

    We intentionally avoid a YAML dependency: we only need top-level scalar keys
    (``name``, ``description``, ``mode``). Block scalars (``>-``/``|``) are tolerated
    for values but their content is not required beyond presence.
    """
    if not text.startswith("---"):
        _fail("source has no leading '---' frontmatter block")
    end = text.find("\n---", 3)
    if end == -1:
        _fail("source frontmatter is not terminated by a closing '---'")
    block = text[3:end].strip("\n")

    fields: dict[str, str] = {}
    current_key: str | None = None
    for raw in block.splitlines():
        # top-level "key: value" (no leading whitespace)
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", raw)
        if m:
            current_key = m.group(1).strip()
            value = m.group(2).strip()
            # strip block-scalar indicators; presence is what we validate
            if value in (">-", ">", "|", "|-", ">+", "|+"):
                value = ""
            fields[current_key] = value
        elif current_key and (raw.startswith("  ") or raw.startswith("\t")):
            # continuation line of a block scalar -> append (single-spaced)
            cont = raw.strip()
            fields[current_key] = (fields[current_key] + " " + cont).strip()
    return fields


def derive_name(fields: dict[str, str], override: str | None) -> str:
    name = (override or fields.get("name", "")).strip().strip('"').strip("'")
    if not name:
        _fail("could not determine sub-agent name (frontmatter 'name' missing and no --name)")
    if not _NAME_RE.match(name):
        _fail(
            f"invalid sub-agent name '{name}': use lowercase letters, digits, and hyphens "
            "(1-64 chars, must start alphanumeric)"
        )
    return name


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Install a global Cursor sub-agent (*.md) safely.")
    ap.add_argument("--source", required=True, help="Path to the canonical sub-agent .md file.")
    ap.add_argument("--name", default=None, help="Override the installed file name (without .md).")
    ap.add_argument(
        "--agents-dir",
        default=str(Path.home() / ".cursor" / "agents"),
        help="Target global agents directory (default: ~/.cursor/agents).",
    )
    ap.add_argument("--dry-run", action="store_true", help="Validate and print the plan; write nothing.")
    args = ap.parse_args(argv)

    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        _fail(f"source not found or not a file: {source}")
    if source.suffix.lower() != ".md":
        _fail(f"source must be a .md file, got: {source.suffix or '(none)'}")

    text = source.read_text(encoding="utf-8")
    fields = parse_frontmatter(text)
    if not fields.get("name"):
        _fail("frontmatter missing required key: name")
    if not fields.get("description"):
        _fail("frontmatter missing required key: description")

    name = derive_name(fields, args.name)

    agents_dir = Path(args.agents_dir).expanduser().resolve()
    dest = (agents_dir / f"{name}.md").resolve()

    # Hard boundary: destination MUST be a direct child of agents_dir.
    if dest.parent != agents_dir:
        _fail(f"refusing to write outside agents dir: {dest} (agents dir: {agents_dir})")
    if dest.suffix.lower() != ".md":
        _fail("refusing to write a non-.md destination")

    backup: Path | None = None
    if dest.exists():
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%SZ")
        backup = dest.with_name(f"{name}.{stamp}.bak")

    print("install_global_subagent plan")
    print(f"  source     : {source}")
    print(f"  agent name : {name}")
    print(f"  destination: {dest}")
    print(f"  overwrite  : {'yes' if dest.exists() else 'no'}")
    print(f"  backup     : {backup if backup else '(none)'}")
    print(f"  mode       : {fields.get('mode', '(unset)')}")

    if args.dry_run:
        print("DRY-RUN: no files written.")
        return 0

    agents_dir.mkdir(parents=True, exist_ok=True)
    if backup is not None:
        shutil.copy2(dest, backup)
        print(f"backed up existing -> {backup}")
    dest.write_text(text, encoding="utf-8")
    print(f"installed -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
