"""AgentCore Stage B Rollback Script — restores Stage A hook configuration.

Usage:
  python scripts/agentcore_cursor/rollback_stage_b.py [--fixture-root PATH] [--backup-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGE_A_HOOKS_JSON = {
    "version": 1,
    "hooks": {
        "sessionStart": [
            {
                "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/agentcore-hook.ps1 -Event sessionStart",
                "timeout": 90
            }
        ],
        "beforeSubmitPrompt": [
            {
                "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/agentcore-hook.ps1 -Event beforeSubmitPrompt",
                "timeout": 90
            }
        ]
    }
}


def backup_current_state(repo_root: Path, backup_base: Path) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target_backup = backup_base / f"cursor-stage-b-{ts}"
    target_backup.mkdir(parents=True, exist_ok=True)

    # Backup hooks.json
    hooks_json = repo_root / ".cursor" / "hooks.json"
    if hooks_json.is_file():
        shutil.copy2(hooks_json, target_backup / "hooks.json")

    # Backup scripts/agentcore_cursor/
    agentcore_cursor_dir = repo_root / "scripts" / "agentcore_cursor"
    if agentcore_cursor_dir.is_dir():
        shutil.copytree(agentcore_cursor_dir, target_backup / "agentcore_cursor", dirs_exist_ok=True)

    # Backup .cursor/hooks/
    hooks_dir = repo_root / ".cursor" / "hooks"
    if hooks_dir.is_dir():
        shutil.copytree(hooks_dir, target_backup / "hooks", dirs_exist_ok=True)

    print(f"Backed up current state to: {target_backup}")
    return target_backup


def restore_stage_a(repo_root: Path) -> bool:
    print(f"Restoring Stage A on: {repo_root}")

    # Restore .cursor/hooks.json to Stage A
    hooks_json = repo_root / ".cursor" / "hooks.json"
    hooks_json.parent.mkdir(parents=True, exist_ok=True)
    hooks_json.write_text(json.dumps(STAGE_A_HOOKS_JSON, indent=2) + "\n", encoding="utf-8")

    # Verify hooks.json only has sessionStart and beforeSubmitPrompt
    data = json.loads(hooks_json.read_text(encoding="utf-8"))
    registered = list(data.get("hooks", {}).keys())
    assert registered == ["sessionStart", "beforeSubmitPrompt"], f"Rollback failed, unexpected hooks: {registered}"

    print("Stage A restoration COMPLETE:")
    print(f"  hooks.json registered events: {registered}")
    print("  preToolUse: REMOVED")
    print("  beforeShellExecution: REMOVED")
    print("  stop: REMOVED")
    print("  afterFileEdit / postToolUse: REMOVED")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="AgentCore Stage B Rollback")
    parser.add_argument("--repo-root", type=str, default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--backup-base", type=str, default=r"E:\AgentCore-Backups\agentcore-control-plane")
    parser.add_argument("--skip-backup", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    backup_base = Path(args.backup_base).resolve()

    if not args.skip_backup and backup_base.parent.exists():
        backup_current_state(repo_root, backup_base)

    success = restore_stage_a(repo_root)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
