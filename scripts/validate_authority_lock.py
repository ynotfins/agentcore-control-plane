#!/usr/bin/env python3
"""Validate AgentCore authority-lock and foreign-boundary manifests."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_LOCK = REPO_ROOT / "contracts" / "authority-lock.yaml"
FOREIGN_BOUNDARIES = REPO_ROOT / "contracts" / "foreign-ecosystem-boundaries.yaml"
AUTHORITY_DOC = REPO_ROOT / "AUTHORITY_LOCK.md"
SWARM_BOUNDARY_DOC = REPO_ROOT / "docs" / "boundaries" / "SWARM_FOREIGN_BOUNDARY.md"

REQUIRED_CLASSES = {
    "operator_locked",
    "governed_mutable",
    "generated_read_only",
    "normal_workstream",
}
ALLOWED_CAPABILITIES = {
    "authority_maintainer",
    "projection_worker",
    "normal_builder",
    "independent_reviewer",
}
FORBIDDEN_AUTH_IDENTITIES = re.compile(
    r"\b(?:gpt|claude|gemini|cursor|sonnet|opus|haiku|model)\b", re.IGNORECASE
)
STALE_SWARM_RUNTIME = (
    "Swarm runtime has its own memory, databases (PostgreSQL 16 :55432)",
)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected mapping")
    return data


def rel_exists(rel: str) -> bool:
    if re.match(r"^[A-Za-z]:\\", rel):
        return True
    if "*" in rel:
        return True
    return (REPO_ROOT / rel.replace("/", "\\")).exists()


def validate_authority_lock() -> list[str]:
    errors: list[str] = []
    manifest = load_yaml(AUTHORITY_LOCK)

    if manifest.get("schema_version") != 1:
        errors.append("authority-lock: schema_version must be 1")
    if manifest.get("authority_owner") != "agentcore-control-plane":
        errors.append("authority-lock: authority_owner must be agentcore-control-plane")

    policy = manifest.get("approval_identity_policy") or {}
    capabilities = set(policy.get("allowed_capabilities") or [])
    if capabilities != ALLOWED_CAPABILITIES:
        errors.append(f"authority-lock: allowed_capabilities mismatch: {sorted(capabilities)}")
    if not policy.get("model_names_are_not_authorization"):
        errors.append("authority-lock: model_names_are_not_authorization must be true")

    classes = manifest.get("classes") or {}
    if set(classes) != REQUIRED_CLASSES:
        errors.append(f"authority-lock: class set mismatch: {sorted(classes)}")

    for class_name, class_def in classes.items():
        capability = class_def.get("permitted_writer_capability")
        if capability not in ALLOWED_CAPABILITIES:
            errors.append(f"{class_name}: invalid permitted_writer_capability {capability!r}")
        paths = class_def.get("paths") or []
        if not paths:
            errors.append(f"{class_name}: paths must not be empty")
        for rel in paths:
            if not isinstance(rel, str) or not rel.strip():
                errors.append(f"{class_name}: invalid path entry {rel!r}")
            elif not rel_exists(rel):
                errors.append(f"{class_name}: path does not exist or is not a glob: {rel}")

    generated = classes.get("generated_read_only") or {}
    if generated.get("generated_file_owner") != "projection_worker":
        errors.append("generated_read_only: generated_file_owner must be projection_worker")

    for required in (
        "PROJECT_ANCHOR.md",
        "BLUEPRINT.md",
        "MILESTONES.md",
        "AUTHORITY_LOCK.md",
        "contracts/authority-lock.yaml",
    ):
        if required not in (classes.get("operator_locked") or {}).get("paths", []):
            errors.append(f"operator_locked: missing {required}")

    master = REPO_ROOT / "MASTER_CONFIG_AND_PROMPT.md"
    if master.is_file():
        text = master.read_text(encoding="utf-8", errors="replace")
        for stale in STALE_SWARM_RUNTIME:
            if stale in text:
                errors.append("MASTER_CONFIG_AND_PROMPT.md contains stale mutable Swarm runtime fact")

    return errors


def validate_foreign_boundaries() -> list[str]:
    errors: list[str] = []
    manifest = load_yaml(FOREIGN_BOUNDARIES)
    if manifest.get("schema_version") != 1:
        errors.append("foreign-boundaries: schema_version must be 1")
    if manifest.get("owner") != "agentcore-control-plane":
        errors.append("foreign-boundaries: owner must be agentcore-control-plane")
    capsules = manifest.get("capsules") or []
    if len(capsules) != 1:
        errors.append("foreign-boundaries: expected exactly one Swarm capsule")
        return errors

    capsule = capsules[0]
    if capsule.get("foreign_ecosystem") != "Swarm":
        errors.append("foreign-boundaries: foreign_ecosystem must be Swarm")
    if capsule.get("canonical_control_plane_path") != r"D:\github\swarm-ecosystem-control":
        errors.append("foreign-boundaries: canonical_control_plane_path mismatch")
    for key in (
        "canonical_repository_url",
        "source_commit",
        "authority_pointer",
        "stable_forbidden_dependencies",
        "permitted_developer_relationship",
        "shared_machine_collision_constraints",
        "last_verification_timestamp",
    ):
        if not capsule.get(key):
            errors.append(f"foreign-boundaries: missing {key}")

    authority_pointer = capsule.get("authority_pointer") or []
    for path in authority_pointer:
        if not Path(path).exists():
            errors.append(f"foreign-boundaries: authority pointer missing on disk: {path}")

    return errors


def main() -> int:
    errors: list[str] = []
    for path in (AUTHORITY_DOC, AUTHORITY_LOCK, SWARM_BOUNDARY_DOC, FOREIGN_BOUNDARIES):
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(REPO_ROOT)}")
    if not errors:
        errors.extend(validate_authority_lock())
        errors.extend(validate_foreign_boundaries())

    if errors:
        print(f"FAILED ({len(errors)} errors)")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("OK: authority lock manifest valid")
    print("OK: foreign ecosystem boundary capsule valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
