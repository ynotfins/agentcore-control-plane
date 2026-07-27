"""Bounded, audited maintenance for the local Serena project registry.

This command is intentionally narrower than a general configuration editor.
It can repair only the Serena registry and the two control-plane project
configurations that are part of the dual-control-plane workspace.

The command requires the current authority-maintainer capability and approval
identifier, creates a rollback copy outside Git before writing, validates the
result, and restores the originals if validation fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable


GLOBAL_CONFIG = Path(r"C:\Users\ynotf\.serena\serena_config.yml")
AGENTCORE_PROJECT = Path(r"D:\github\agentcore-control-plane")
SWARM_PROJECT = Path(r"D:\github\swarm-ecosystem-control")
BACKUP_ROOT = Path(r"E:\AgentCore-Backups\agentcore-control-plane")
SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
CURSOR_GLOBAL_RULE = Path(r"C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc")
CURSOR_GENERATED_RULE = REPO_ROOT / "ide-profiles" / "cursor" / "GLOBAL_RULES.md"

REQUIRED_CAPABILITY = "authority_maintainer"
APPROVAL_ID_PATTERN = re.compile(r"^AUTH-[0-9]{4}-[0-9]{2}-[0-9]{2}-[A-Z0-9_-]+$")

PROJECT_LANGUAGES = {
    AGENTCORE_PROJECT: ["python", "powershell"],
    SWARM_PROJECT: ["powershell", "typescript"],
}

PROJECT_CONFIG_TEMPLATE = """\
project_name: "swarm-ecosystem-control"
languages:
- powershell
- typescript
encoding: "utf-8"
line_ending:
language_backend: LSP
ignore_all_files_in_gitignore: true
ls_specific_settings: {}
ls_workspace_folders:
- .
ls_additional_workspace_folders: []
ignored_paths: []
read_only: false
excluded_tools: []
included_optional_tools: []
fixed_tools: []
default_modes:
added_modes:
initial_prompt: ""
symbol_info_budget:
read_only_memory_patterns: []
ignored_memory_patterns: []
activation_command:
activation_command_timeout: 180
"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _newline_for(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _replace_project_languages(text: str, languages: Iterable[str]) -> str:
    """Replace either the current or legacy language list in one project file."""

    newline = _newline_for(text)
    lines = text.splitlines()
    key_index = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip() in {"languages:", "language_servers:"}
        ),
        None,
    )
    replacement = ["languages:", *[f"- {language}" for language in languages]]
    if key_index is None:
        insertion_index = next(
            (
                index
                for index, line in enumerate(lines)
                if line.startswith("project_name:")
            ),
            -1,
        )
        if insertion_index < 0:
            raise ValueError("project config has no project_name key")
        lines[insertion_index + 1 : insertion_index + 1] = replacement
    else:
        end_index = key_index + 1
        while end_index < len(lines) and (
            not lines[end_index].strip()
            or lines[end_index].lstrip().startswith("- ")
        ):
            end_index += 1
        lines[key_index:end_index] = replacement
    return newline.join(lines).rstrip("\r\n") + newline


def _replace_global_projects(text: str, projects: Iterable[Path]) -> str:
    """Replace the top-level registered-project list without rewriting other settings."""

    newline = _newline_for(text)
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == "projects:")
    except StopIteration as exc:
        raise ValueError("Serena global config has no projects key") from exc

    end = start + 1
    while end < len(lines) and (
        not lines[end].strip() or lines[end].lstrip().startswith("- ")
    ):
        end += 1

    replacement = ["projects:", *[f"- {path}" for path in projects], ""]
    lines[start:end] = replacement
    return newline.join(lines).rstrip("\r\n") + newline


def _validate_yaml(path: Path, expected_projects: list[Path] | None = None) -> None:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment-specific guard
        raise RuntimeError("PyYAML is required for Serena maintenance validation") from exc

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse as a YAML mapping")

    if path == GLOBAL_CONFIG:
        projects = data.get("projects")
        actual = [Path(item) for item in projects or []]
        if actual != (expected_projects or []):
            raise ValueError(f"unexpected Serena project registry: {actual}")
        return

    languages = data.get("languages")
    if not isinstance(languages, list) or not languages:
        raise ValueError(f"{path} has no non-empty languages list")
    if "language_servers" in data:
        raise ValueError(f"{path} still contains legacy language_servers")
    if not isinstance(data.get("project_name"), str) or not data["project_name"]:
        raise ValueError(f"{path} has no project_name")
    if data.get("language_backend") not in (None, "LSP", "JetBrains"):
        raise ValueError(f"{path} has an invalid language_backend")


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.serena-maintenance.tmp")
    try:
        temporary.write_text(content, encoding="utf-8", newline="")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _cursor_global_rule_content() -> str:
    if not CURSOR_GENERATED_RULE.is_file():
        raise FileNotFoundError(CURSOR_GENERATED_RULE)
    frontmatter = """\
---
description: AgentCore foundation and Serena-centered powerhouse toolchain for Cursor.
globs: ["**/*"]
alwaysApply: true
---

"""
    return frontmatter + CURSOR_GENERATED_RULE.read_text(encoding="utf-8")


def _validate_cursor_global_rule(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required = (
        text.startswith("---\n"),
        "alwaysApply: true" in text,
        "policy_revision 2026-07-26" in text,
        "Serena-centered powerhouse toolchain" in text,
        "STAGING ONLY" not in text,
    )
    if not all(required):
        raise ValueError(f"{path} does not contain the current active Cursor foundation rule")
    if re.search(r"sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA|OPENSSH|PRIVATE) KEY", text):
        raise ValueError(f"{path} contains a secret-like literal")


def install_cursor_rule(*, approval_id: str, dry_run: bool = False) -> dict[str, object]:
    """Install the generated Cursor foundation rule through one audited target."""

    content = _cursor_global_rule_content()
    if dry_run:
        current = (
            CURSOR_GLOBAL_RULE.read_text(encoding="utf-8")
            if CURSOR_GLOBAL_RULE.is_file()
            else ""
        )
        return {
            "ok": True,
            "dry_run": True,
            "approval_id": approval_id,
            "target": str(CURSOR_GLOBAL_RULE),
            "source": str(CURSOR_GENERATED_RULE),
            "changed": current != content,
        }

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUP_ROOT / f"cursor-global-rule-{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    before = (
        _sha256(CURSOR_GLOBAL_RULE)
        if CURSOR_GLOBAL_RULE.is_file()
        else None
    )
    backup_file = backup_dir / "agentcore-foundation.mdc.before"
    try:
        if CURSOR_GLOBAL_RULE.is_file():
            shutil.copy2(CURSOR_GLOBAL_RULE, backup_file)
        _atomic_write(CURSOR_GLOBAL_RULE, content)
        _validate_cursor_global_rule(CURSOR_GLOBAL_RULE)
        manifest = {
            "operation": "cursor_global_rule_install",
            "approval_id": approval_id,
            "capability": REQUIRED_CAPABILITY,
            "generated_at": datetime.now().astimezone().isoformat(),
            "source": str(CURSOR_GENERATED_RULE),
            "target": str(CURSOR_GLOBAL_RULE),
            "before_sha256": before,
            "after_sha256": _sha256(CURSOR_GLOBAL_RULE),
            "backup_dir": str(backup_dir),
            "validated": True,
        }
        (backup_dir / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        return {"ok": True, **manifest}
    except Exception:
        if backup_file.is_file():
            _atomic_write(CURSOR_GLOBAL_RULE, backup_file.read_text(encoding="utf-8"))
        elif before is None and CURSOR_GLOBAL_RULE.exists():
            CURSOR_GLOBAL_RULE.unlink()
        raise


def _backup_path(path: Path, backup_dir: Path) -> Path:
    if path == GLOBAL_CONFIG:
        return backup_dir / "serena_config.yml.before"
    if path == AGENTCORE_PROJECT / ".serena" / "project.yml":
        return backup_dir / "agentcore-project.yml.before"
    return backup_dir / "swarm-project.yml.before"


def _prepare_backup(paths: list[Path], backup_dir: Path) -> dict[str, str | None]:
    backup_dir.mkdir(parents=True, exist_ok=False)
    originals: dict[str, str | None] = {}
    for path in paths:
        key = str(path)
        if path.exists():
            shutil.copy2(path, _backup_path(path, backup_dir))
            originals[key] = _sha256(path)
        else:
            originals[key] = None
    return originals


def _restore(paths: list[Path], originals: dict[str, str | None], backup_dir: Path) -> None:
    for path in paths:
        backup = _backup_path(path, backup_dir)
        if backup.exists():
            _atomic_write(path, backup.read_text(encoding="utf-8"))
        elif originals.get(str(path)) is None and path.exists():
            path.unlink()


def _manifest(
    backup_dir: Path,
    paths: list[Path],
    before: dict[str, str | None],
    approval_id: str,
) -> dict[str, object]:
    return {
        "operation": "serena_dual_control_plane_repair",
        "approval_id": approval_id,
        "capability": REQUIRED_CAPABILITY,
        "generated_at": datetime.now().astimezone().isoformat(),
        "backup_dir": str(backup_dir),
        "paths": [
            {
                "path": str(path),
                "before_sha256": before.get(str(path)),
                "after_sha256": _sha256(path) if path.exists() else None,
                "created": before.get(str(path)) is None,
            }
            for path in paths
        ],
        "validated": True,
    }


def repair(*, approval_id: str, dry_run: bool = False) -> dict[str, object]:
    """Repair all approved Serena targets as one validated operation."""

    project_configs = [
        AGENTCORE_PROJECT / ".serena" / "project.yml",
        SWARM_PROJECT / ".serena" / "project.yml",
    ]
    paths = [GLOBAL_CONFIG, *project_configs]
    if not GLOBAL_CONFIG.is_file():
        raise FileNotFoundError(GLOBAL_CONFIG)
    if not AGENTCORE_PROJECT.is_dir() or not SWARM_PROJECT.is_dir():
        raise FileNotFoundError("Both control-plane roots must exist")

    global_before = GLOBAL_CONFIG.read_text(encoding="utf-8")
    agentcore_before = project_configs[0].read_text(encoding="utf-8")
    swarm_before = (
        project_configs[1].read_text(encoding="utf-8")
        if project_configs[1].is_file()
        else PROJECT_CONFIG_TEMPLATE
    )

    global_after = _replace_global_projects(
        global_before,
        [AGENTCORE_PROJECT, SWARM_PROJECT],
    )
    agentcore_after = _replace_project_languages(
        agentcore_before,
        PROJECT_LANGUAGES[AGENTCORE_PROJECT],
    )
    swarm_after = (
        _replace_project_languages(swarm_before, PROJECT_LANGUAGES[SWARM_PROJECT])
        if project_configs[1].is_file()
        else PROJECT_CONFIG_TEMPLATE
    )

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "approval_id": approval_id,
            "targets": [str(path) for path in paths],
            "registered_projects": [str(AGENTCORE_PROJECT), str(SWARM_PROJECT)],
            "changes": {
                str(GLOBAL_CONFIG): global_before != global_after,
                str(project_configs[0]): agentcore_before != agentcore_after,
                str(project_configs[1]): swarm_before != swarm_after
                or not project_configs[1].exists(),
            },
        }

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUP_ROOT / f"serena-maintenance-{timestamp}"
    before = _prepare_backup(paths, backup_dir)
    try:
        _atomic_write(GLOBAL_CONFIG, global_after)
        _atomic_write(project_configs[0], agentcore_after)
        _atomic_write(project_configs[1], swarm_after)

        _validate_yaml(GLOBAL_CONFIG, [AGENTCORE_PROJECT, SWARM_PROJECT])
        _validate_yaml(project_configs[0])
        _validate_yaml(project_configs[1])
        manifest = _manifest(backup_dir, paths, before, approval_id)
        (backup_dir / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        return {"ok": True, **manifest}
    except Exception:
        _restore(paths, before, backup_dir)
        raise


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["repair", "install_cursor_rule"])
    parser.add_argument("--capability", required=True)
    parser.add_argument("--approval-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.capability != REQUIRED_CAPABILITY:
        raise SystemExit("invalid Serena maintenance capability")
    if not APPROVAL_ID_PATTERN.fullmatch(args.approval_id):
        raise SystemExit("invalid Serena maintenance approval identifier")
    if args.operation == "repair":
        result = repair(approval_id=args.approval_id, dry_run=args.dry_run)
    else:
        result = install_cursor_rule(
            approval_id=args.approval_id,
            dry_run=args.dry_run,
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
