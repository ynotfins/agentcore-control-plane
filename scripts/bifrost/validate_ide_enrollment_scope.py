#!/usr/bin/env python3
"""Fail when IDE-local enrollment prompts instruct multi-IDE live edits.

Scans AgentCore IDE enrollment / install prompts and fails when any prompt:
  1. Omits the CLIENT-LOCAL EXECUTION SCOPE hard rule, or
  2. Instructs the executing agent to inspect/back up/repair/restart/validate/modify
     live configuration paths belonging to two or more distinct IDEs.

Reference listings of other IDE paths are allowed when they are not paired with
edit-imperative language for multiple IDEs.

Run: python scripts/bifrost/validate_ide_enrollment_scope.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]

SCOPE_TITLE = "CLIENT-LOCAL EXECUTION SCOPE"
SCOPE_REQUIRED_PHRASES = (
    "may inspect and modify only its own live",
    "Configuration examples for other IDEs are reference material only",
    "Do not inspect, back up, repair, restart, validate, or modify another IDE",
    "Cross-IDE reconciliation is a separate AgentCore control-plane task",
)

# Imperative verbs that turn a live-path mention into an edit instruction.
EDIT_VERBS = re.compile(
    r"\b("
    r"edit|modify|update|write|patch|merge|replace|overwrite|install|"
    r"back\s*up|backup|repair|restart|reload|validate|fix|"
    r"add\s+or\s+merge|remove\s+direct|touch"
    r")\b",
    re.IGNORECASE,
)

# Broad multi-IDE enrollment instructions (even without concrete paths).
# Require an explicit plural/quantifier so single-IDE phrases like
# "restart client after MCP config changes" do not false-positive.
MULTI_IDE_EDIT_PHRASES = re.compile(
    r"(?is)"
    r"("
    r"(?:edit|modify|update|configure|enroll|install|back\s*up|backup|repair|restart|"
    r"validate|fix)\s+(?:all|every|each|both|multiple)\s+"
    r"(?:supported\s+)?(?:non[- ]swarm\s+)?(?:ides?|clients?|ide\s+configs?)"
    r"|"
    r"(?:edit|modify|update|configure|enroll|install|back\s*up|backup|repair|restart|"
    r"validate|fix)\s+(?:the\s+)?"
    r"(?:supported\s+)?(?:non[- ]swarm\s+)?(?:ides|clients|ide\s+configs)\b"
    r"|"
    r"(?:all|every|each|both)\s+(?:supported\s+)?(?:non[- ]swarm\s+)?"
    r"(?:ides?|clients?)\s+(?:must|should|need\s+to)?\s*"
    r"(?:be\s+)?(?:edited|modified|updated|configured|enrolled|backed\s+up|repaired|"
    r"restarted|validated|fixed)"
    r"|"
    r"across\s+(?:all|every|each|multiple)\s+(?:ides?|clients?)"
    r")",
)

WINDOW = 220  # chars of context around a live-path hit


def load_live_paths() -> dict[str, str]:
    """Map normalized live config path -> ide_id."""
    paths: dict[str, str] = {}

    profiles_root = REPO / "ide-profiles"
    for profile_path in sorted(profiles_root.glob("*/IDE_PROFILE.yaml")):
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        if not profile or profile.get("swarm_managed"):
            continue
        ide_id = str(profile.get("ide_id") or profile_path.parent.name)
        target = profile.get("live_mcp_config_target")
        if isinstance(target, str) and target.strip() and target.strip().lower() != "unverified":
            paths[_norm(target)] = ide_id

    gateway = json.loads((REPO / "contracts" / "agentcore-gateway-client.json").read_text(encoding="utf-8"))
    for ide_id, hint in (gateway.get("client_render_hints") or {}).items():
        if not isinstance(hint, dict):
            continue
        config_path = hint.get("config_path")
        if isinstance(config_path, str) and config_path.strip():
            paths[_norm(config_path)] = str(ide_id)

    return paths


def _norm(path: str) -> str:
    return path.replace("/", "\\").strip().lower()


def enrollment_files() -> list[Path]:
    files = [
        REPO / "docs" / "prompts" / "install-agentcore-gateway-in-ide.md",
        REPO / "MASTER_CONFIG_AND_PROMPT.md",
    ]
    for profile_dir in sorted((REPO / "ide-profiles").iterdir()):
        if not profile_dir.is_dir():
            continue
        install = profile_dir / "INSTALL_OR_UPDATE.md"
        if install.exists():
            files.append(install)
    return files


def missing_scope_phrases(text: str) -> list[str]:
    missing: list[str] = []
    if SCOPE_TITLE not in text:
        missing.append(f"missing title `{SCOPE_TITLE}`")
    for phrase in SCOPE_REQUIRED_PHRASES:
        if phrase not in text:
            missing.append(f"missing phrase `{phrase}`")
    return missing


def extract_master_prompt_block(text: str) -> str:
    """Prefer the copy-paste IDE setup prompt inside MASTER_CONFIG_AND_PROMPT.md."""
    marker = "## 10. Global IDE setup prompt"
    if marker not in text:
        return text
    chunk = text.split(marker, 1)[1]
    # Stop before the next major section when present.
    next_section = re.search(r"\n## 11\.", chunk)
    if next_section:
        chunk = chunk[: next_section.start()]
    return chunk


def find_imperative_ide_hits(text: str, live_paths: dict[str, str]) -> dict[str, list[str]]:
    """Return ide_id -> sample snippets where a live path is near an edit verb."""
    hits: dict[str, list[str]] = {}
    lowered = text.lower()
    for path, ide_id in live_paths.items():
        start = 0
        while True:
            idx = lowered.find(path, start)
            if idx < 0:
                break
            left = max(0, idx - WINDOW)
            right = min(len(text), idx + len(path) + WINDOW)
            snippet = text[left:right]
            if EDIT_VERBS.search(snippet):
                hits.setdefault(ide_id, []).append(" ".join(snippet.split())[:180])
            start = idx + len(path)
    return hits


def validate_file(path: Path, live_paths: dict[str, str]) -> list[str]:
    errors: list[str] = []
    raw = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path.relative_to(REPO)).replace("\\", "/")

    # MASTER embeds the prompt plus surrounding docs; scope-check the prompt block,
    # but still scan the whole enrollment-relevant section for multi-IDE edit orders.
    scope_text = extract_master_prompt_block(raw) if path.name == "MASTER_CONFIG_AND_PROMPT.md" else raw
    for miss in missing_scope_phrases(scope_text):
        errors.append(f"{rel}: {miss}")

    scan_text = scope_text if path.name == "MASTER_CONFIG_AND_PROMPT.md" else raw
    if MULTI_IDE_EDIT_PHRASES.search(scan_text):
        errors.append(f"{rel}: multi-IDE live edit instruction phrase detected")

    imperative_hits = find_imperative_ide_hits(scan_text, live_paths)
    if len(imperative_hits) >= 2:
        ide_list = ", ".join(sorted(imperative_hits))
        samples = []
        for ide_id in sorted(imperative_hits):
            samples.append(f"{ide_id}: {imperative_hits[ide_id][0]}")
        errors.append(
            f"{rel}: instructs live edits for multiple IDEs ({ide_list}); "
            + " | ".join(samples)
        )

    # Per-IDE install docs must not order edits against a foreign live path.
    if path.parent.parent.name == "ide-profiles" and path.name == "INSTALL_OR_UPDATE.md":
        own_ide = path.parent.name
        foreign = {ide: snips for ide, snips in imperative_hits.items() if ide != own_ide}
        if foreign:
            errors.append(
                f"{rel}: per-IDE install prompt orders live edits for foreign IDE(s): "
                + ", ".join(sorted(foreign))
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable summary")
    args = parser.parse_args(argv)

    live_paths = load_live_paths()
    if len(live_paths) < 2:
        print("FAIL: fewer than 2 live IDE config paths discovered for comparison", file=sys.stderr)
        return 1

    files = enrollment_files()
    errors: list[str] = []
    checked: list[str] = []
    for path in files:
        if not path.exists():
            errors.append(f"missing enrollment file: {path.relative_to(REPO)}")
            continue
        checked.append(str(path.relative_to(REPO)).replace("\\", "/"))
        errors.extend(validate_file(path, live_paths))

    summary = {
        "checked_files": checked,
        "live_path_count": len(live_paths),
        "live_ides": sorted(set(live_paths.values())),
        "errors": errors,
        "ok": not errors,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Checked {len(checked)} enrollment prompt file(s) against {len(live_paths)} live IDE path(s).")
        if errors:
            print(f"FAIL {len(errors)} issue(s):")
            for err in errors:
                print(f"  - {err}")
        else:
            print("OK: CLIENT-LOCAL EXECUTION SCOPE present; no multi-IDE live edit instructions.")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
