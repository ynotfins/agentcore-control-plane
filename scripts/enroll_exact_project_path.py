#!/usr/bin/env python3
"""Add one EXACT path to contracts/agentcore-project-enrollment.json.

Cursor/operator only. Devin and other builders must not invoke this.
match_enrolled_path remains exact equality; this helper never adds a prefix matcher.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agentcore_project_boundary import (  # noqa: E402
    CONTRACT_ENV,
    DEFAULT_CONTRACT,
    ProjectBoundaryError,
    _foreign_reason,
    _normal_path,
    load_enrollment_contract,
    require_enrolled_path,
)

ALLOWED_CALLERS = frozenset({"cursor", "operator"})
WILDCARD_MARKERS = ("*", "?", "<", ">", "|")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _store_path(value: str) -> str:
    return str(value).strip().replace("/", "\\").rstrip("\\")


def add_exact_enrolled_path(
    *,
    project_key: str,
    path: str,
    caller: str,
    contract_path: Path | None = None,
    rollback_root: Path | None = None,
    require_exists: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    if caller not in ALLOWED_CALLERS:
        raise ProjectBoundaryError("caller_not_authorized")
    if not project_key or not path:
        raise ProjectBoundaryError("exact_path_required")
    if any(marker in path for marker in WILDCARD_MARKERS):
        raise ProjectBoundaryError("exact_path_required")

    stored = _store_path(path)
    if require_exists and not Path(stored).exists():
        raise ProjectBoundaryError("path_not_found")

    contract_file = Path(contract_path or os.environ.get(CONTRACT_ENV, str(DEFAULT_CONTRACT)))
    prior_env = os.environ.get(CONTRACT_ENV)
    os.environ[CONTRACT_ENV] = str(contract_file)
    try:
        contract = load_enrollment_contract()
        foreign = _foreign_reason(stored, contract)
        if foreign:
            raise ProjectBoundaryError(foreign)

        project = next(
            (item for item in contract["projects"] if item.get("project_key") == project_key),
            None,
        )
        if project is None:
            raise ProjectBoundaryError("project_not_enrolled")

        existing = [_normal_path(item) for item in project.get("paths", [])]
        already = _normal_path(stored) in existing
        result = {
            "ok": True,
            "project_key": project_key,
            "path": stored,
            "already_enrolled": already,
            "dry_run": dry_run,
            "rollback": None,
        }
        if already:
            require_enrolled_path(stored)
            return result

        if dry_run:
            result["would_add"] = stored
            return result

        rollback_parent = Path(rollback_root or (REPO_ROOT / ".agentcore" / "rollback"))
        rollback_dir = rollback_parent / f"{_timestamp()}-enroll-exact-path"
        rollback_dir.mkdir(parents=True, exist_ok=False)
        shutil.copy2(contract_file, rollback_dir / "agentcore-project-enrollment.json")
        result["rollback"] = str(rollback_dir)

        project.setdefault("paths", []).append(stored)
        contract_file.write_text(
            json.dumps(contract, indent=2) + "\n",
            encoding="utf-8",
        )
        enrolled = require_enrolled_path(stored)
        if enrolled.get("project_key") != project_key:
            raise ProjectBoundaryError("project_identity_mismatch")
        return result
    finally:
        if prior_env is None:
            os.environ.pop(CONTRACT_ENV, None)
        else:
            os.environ[CONTRACT_ENV] = prior_env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Operator/Cursor-only helper: enroll one exact project path."
    )
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--caller", required=True, choices=sorted(ALLOWED_CALLERS))
    parser.add_argument("--contract", type=Path, default=None)
    parser.add_argument("--rollback-root", type=Path, default=None)
    parser.add_argument("--allow-missing-path", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = add_exact_enrolled_path(
            project_key=args.project_key,
            path=args.path,
            caller=args.caller,
            contract_path=args.contract,
            rollback_root=args.rollback_root,
            require_exists=not args.allow_missing_path,
            dry_run=args.dry_run,
        )
    except ProjectBoundaryError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
