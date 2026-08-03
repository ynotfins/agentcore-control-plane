"""Default-deny AgentCore project enrollment shared by every host boundary."""

from __future__ import annotations

import json
import ntpath
import os
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "contracts" / "agentcore-project-enrollment.json"
CONTRACT_ENV = "AGENTCORE_PROJECT_ENROLLMENT_CONTRACT"


class ProjectBoundaryError(ValueError):
    """Raised before persistence or project-scoped process activation."""


def _contract_path() -> Path:
    return Path(os.environ.get(CONTRACT_ENV, str(DEFAULT_CONTRACT)))


def _normal_path(value: str | Path) -> str:
    text = str(value).strip().replace("/", "\\")
    return ntpath.normcase(ntpath.normpath(text)).rstrip("\\")


def load_enrollment_contract() -> dict[str, Any]:
    data = json.loads(_contract_path().read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("default_policy") != "deny":
        raise ProjectBoundaryError("invalid_project_enrollment_contract")
    if not isinstance(data.get("projects"), list):
        raise ProjectBoundaryError("invalid_project_enrollment_contract")
    return data


def _foreign_reason(value: str, contract: dict[str, Any]) -> str | None:
    normalized = _normal_path(value)
    for marker in contract.get("foreign_markers", []):
        if str(marker).lower() in normalized.lower():
            return "swarm_project_refused"
    for root in contract.get("foreign_roots", []):
        prefix = _normal_path(root)
        if normalized == prefix or normalized.startswith(prefix + "\\"):
            return "swarm_project_refused"
    return None


def enrolled_projects() -> list[dict[str, Any]]:
    return list(load_enrollment_contract()["projects"])


def match_enrolled_path(value: str | Path) -> dict[str, Any] | None:
    contract = load_enrollment_contract()
    normalized = _normal_path(value)
    if _foreign_reason(normalized, contract):
        raise ProjectBoundaryError("swarm_project_refused")
    for project in contract["projects"]:
        if any(normalized == _normal_path(path) for path in project.get("paths", [])):
            return project
    return None


def require_enrolled_path(value: str | Path) -> dict[str, Any]:
    project = match_enrolled_path(value)
    if project is None:
        raise ProjectBoundaryError("project_not_enrolled")
    return project


def require_enrolled_project_key(project_key: str) -> dict[str, Any]:
    contract = load_enrollment_contract()
    reason = _foreign_reason(project_key, contract)
    if reason:
        raise ProjectBoundaryError(reason)
    for project in contract["projects"]:
        if project_key == project.get("project_key"):
            return project
    raise ProjectBoundaryError("project_not_enrolled")


def validate_project_identity(args: dict[str, Any]) -> dict[str, Any]:
    """Require every supplied repository/worktree path to map to one enrollment."""
    contract = load_enrollment_contract()
    identity_values = [
        str(args.get(field) or "")
        for field in ("project_key", "project_name", "repo_key")
    ]
    for value in identity_values:
        if value and _foreign_reason(value, contract):
            raise ProjectBoundaryError("swarm_project_refused")

    supplied_paths = [
        str(args.get(field) or "")
        for field in (
            "project_root",
            "canonical_repo_path",
            "worktree_path",
        )
        if args.get(field)
    ]
    if not supplied_paths:
        raise ProjectBoundaryError("project_path_required")

    for path in supplied_paths:
        reason = _foreign_reason(path, contract)
        if reason:
            raise ProjectBoundaryError(reason)
    matches = [require_enrolled_path(path) for path in supplied_paths]
    project_keys = {str(project["project_key"]) for project in matches}
    if len(project_keys) != 1:
        raise ProjectBoundaryError("project_identity_mismatch")
    project = matches[0]
    if str(args.get("project_key") or "") != str(project["project_key"]):
        raise ProjectBoundaryError("project_identity_mismatch")
    return project
