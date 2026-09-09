"""Shared enrollment-bound session identity for Bifrost HTTP shims.

Resolves caller project identity from Bifrost-forwarded headers against
contracts/agentcore-project-enrollment.json. Default-deny. Swarm refuse.
Never uses machine-global active-project.json as a security boundary.
Never falls back to a default enrolled project.

Authority: docs/adr/ADR-2026-09-09-serena-http-session-shim.md
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
ENROLLMENT_CONTRACT = REPO_ROOT / "contracts" / "agentcore-project-enrollment.json"

PROJECT_HEADER_NAMES = ("x-agentcore-project", "x-project-key")
SESSION_HEADER_NAMES = ("x-bf-session-id", "x-session-id")
PATH_ARG_NAMES = ("relative_path", "path", "project", "project_path", "root_path")

ERROR_NOT_ENROLLED = "PROJECT_NOT_ENROLLED"
ERROR_SWARM_REFUSED = "swarm_project_refused"


@dataclass(frozen=True)
class ProjectResolution:
    project_key: Optional[str]
    primary_path: Optional[Path]
    error: Optional[str]

    @property
    def ok(self) -> bool:
        return (
            self.error is None
            and self.project_key is not None
            and self.primary_path is not None
        )


def load_enrollment_contract(path: Optional[Path] = None) -> dict[str, Any]:
    contract_path = path or ENROLLMENT_CONTRACT
    try:
        return json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception:
        return {"projects": [], "foreign_markers": [], "foreign_roots": []}


def _normalize_path(raw: str) -> str:
    return str(Path(raw).resolve()).lower()


class EnrollmentRegistry:
    """Default-deny resolver against contracts/agentcore-project-enrollment.json."""

    def __init__(self, contract: Optional[dict[str, Any]] = None):
        self._contract = contract or load_enrollment_contract()
        self._projects: dict[str, dict[str, Any]] = {}
        self._path_to_key: dict[str, str] = {}
        self._foreign_markers: list[str] = [
            str(m).lower() for m in self._contract.get("foreign_markers", [])
        ]
        self._foreign_roots: list[str] = []
        for raw in self._contract.get("foreign_roots", []):
            try:
                self._foreign_roots.append(_normalize_path(str(raw)))
            except Exception:
                continue
        self._reload_projects()

    def _reload_projects(self) -> None:
        self._projects.clear()
        self._path_to_key.clear()
        for project in self._contract.get("projects", []):
            pkey = project.get("project_key")
            if not pkey:
                continue
            paths = [Path(raw).resolve() for raw in project.get("paths", []) if raw]
            self._projects[str(pkey)] = {
                "project_key": str(pkey),
                "name": project.get("name", pkey),
                "paths": paths,
                "primary_path": paths[0] if paths else None,
            }
            for path_obj in paths:
                self._path_to_key[str(path_obj).lower()] = str(pkey)

    def is_swarm_refused(self, candidate: str) -> bool:
        lower = candidate.lower()
        if any(marker in lower for marker in self._foreign_markers):
            return True
        try:
            resolved = _normalize_path(candidate)
            if any(
                resolved == root or resolved.startswith(root + os.sep)
                for root in self._foreign_roots
            ):
                return True
        except Exception:
            return False
        return False

    def resolve(
        self,
        project_key: Optional[str] = None,
        candidate_path: Optional[str] = None,
    ) -> ProjectResolution:
        key = (project_key or "").strip() or None
        path = (candidate_path or "").strip() or None

        if path and self.is_swarm_refused(path):
            return ProjectResolution(None, None, ERROR_SWARM_REFUSED)
        if key and self.is_swarm_refused(key):
            return ProjectResolution(None, None, ERROR_SWARM_REFUSED)

        if key:
            enrolled = self._projects.get(key)
            if not enrolled or enrolled.get("primary_path") is None:
                return ProjectResolution(None, None, ERROR_NOT_ENROLLED)
            return ProjectResolution(key, enrolled["primary_path"], None)

        if path:
            try:
                resolved_str = _normalize_path(path)
                for norm_path, pkey in self._path_to_key.items():
                    if resolved_str == norm_path or resolved_str.startswith(
                        norm_path + os.sep
                    ):
                        primary = self._projects[pkey]["primary_path"]
                        return ProjectResolution(pkey, primary, None)
            except Exception:
                pass
            return ProjectResolution(None, None, ERROR_NOT_ENROLLED)

        # No project_key and no candidate_path: default-deny. Never fall back.
        return ProjectResolution(None, None, ERROR_NOT_ENROLLED)


def extract_project_header(headers: dict[str, str]) -> Optional[str]:
    lowered = {str(k).lower(): str(v) for k, v in headers.items()}
    for name in PROJECT_HEADER_NAMES:
        value = (lowered.get(name) or "").strip()
        if value:
            return value
    return None


def extract_session_id(headers: dict[str, str]) -> Optional[str]:
    lowered = {str(k).lower(): str(v) for k, v in headers.items()}
    for name in SESSION_HEADER_NAMES:
        value = (lowered.get(name) or "").strip()
        if value:
            return value
    return None


def extract_candidate_path(args: dict[str, Any]) -> Optional[str]:
    for name in PATH_ARG_NAMES:
        raw = args.get(name)
        if isinstance(raw, str) and raw.strip() and Path(raw.strip()).is_absolute():
            return raw.strip()
    return None


def resolve_request_identity(
    registry: EnrollmentRegistry,
    headers: dict[str, str],
    args: Optional[dict[str, Any]] = None,
    session_bindings: Optional[dict[str, str]] = None,
) -> ProjectResolution:
    """Resolve an MCP tool call to an enrolled project. Default-deny."""
    project_header = extract_project_header(headers)
    session_id = extract_session_id(headers)
    bound_key = None
    if not project_header and session_id and session_bindings:
        bound_key = session_bindings.get(session_id)
    return registry.resolve(
        project_key=project_header or bound_key,
        candidate_path=extract_candidate_path(args or {}),
    )
