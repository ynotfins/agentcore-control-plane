#!/usr/bin/env python3
"""Semantic/temporal validator for per-IDE status dimensions.

Exit 0 = all invariants pass; exit 1 = failures listed.

Validates:
- status enum membership
- matrix <-> per-IDE profile equality for m8_enrollment and dimensions
- live_validated incompatible with pending/restart/fail gates
- application_launch=fail blocks overall enrollment
- native_memory_lifecycle pass requires same-client evidence artifact with timestamp
- temporal ordering: newer evidence wins; older evidence cannot silently supersede a newer claim
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[2]
PROFILES_DIR = REPO / "ide-profiles"
MATRIX_PATH = PROFILES_DIR / "IDE_CAPABILITY_MATRIX.yaml"

DIMENSIONS = [
    "application_launch",
    "gateway_configuration",
    "gateway_discovery",
    "native_memory_lifecycle",
    "fresh_chat_recovery",
    "persistence_after_restart",
    "operator_gate",
]

STATUS_VALUES = {
    "unverified",
    "fail",
    "configured_restart_required",
    "awaiting_operator_import",
    "awaiting_operator_cloud_mcp_enrollment",
    "manual_import_pending",
    "UI_only_pending",
    "unsupported_with_reason",
    "live_validated",
}

PENDING_OR_RESTART = {
    "configured_restart_required",
    "awaiting_operator_import",
    "awaiting_operator_cloud_mcp_enrollment",
    "manual_import_pending",
    "UI_only_pending",
}

FAILURES: list[str] = []


def fail(message: str) -> None:
    FAILURES.append(message)


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    # Accept ISO-8601 with or without seconds/timezone.
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def load_matrix() -> dict[str, Any]:
    raw = MATRIX_PATH.read_text(encoding="utf-8")
    return yaml.safe_load(raw)


def load_profiles() -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for profile_dir in sorted(PROFILES_DIR.iterdir()):
        if not profile_dir.is_dir():
            continue
        profile_path = profile_dir / "IDE_PROFILE.yaml"
        if not profile_path.exists():
            continue
        profiles[profile_dir.name] = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    return profiles


def validate_dimension_block(ide_id: str, context: str, dimensions: dict[str, Any]) -> None:
    """Validate one dimensions block (from matrix or profile)."""
    if not isinstance(dimensions, dict):
        fail(f"{context}: dimensions must be a mapping")
        return

    for dim in DIMENSIONS:
        if dim not in dimensions:
            fail(f"{context}: missing dimension {dim}")
            continue
        d = dimensions[dim]
        if not isinstance(d, dict):
            fail(f"{context}: dimension {dim} must be a mapping")
            continue
        status = d.get("status")
        if status not in STATUS_VALUES:
            fail(f"{context}: dimension {dim} has invalid status {status!r}")
        evidence_path = d.get("evidence_path")
        evidence_ts = d.get("evidence_ts")
        if status in {"live_validated", "configured_restart_required", "fail"} and not evidence_path:
            fail(f"{context}: dimension {dim} status={status} requires evidence_path")
        if evidence_ts and parse_ts(evidence_ts) is None:
            fail(f"{context}: dimension {dim} evidence_ts {evidence_ts!r} is not parseable")
        superseded_by = d.get("superseded_by")
        if superseded_by is not None and not isinstance(superseded_by, str):
            fail(f"{context}: dimension {dim} superseded_by must be a string or null")


def validate_matrix_invariants(matrix: dict[str, Any]) -> None:
    managed = matrix.get("managed_ides") or {}
    for ide_id, ide_data in managed.items():
        context = f"matrix:{ide_id}"
        m8 = ide_data.get("m8_enrollment")
        if m8 not in STATUS_VALUES:
            fail(f"{context}: invalid m8_enrollment {m8!r}")
        dimensions = ide_data.get("dimensions") or {}
        validate_dimension_block(ide_id, context, dimensions)

        # live_validated incompatible with pending/restart/fail gates.
        if m8 == "live_validated":
            for dim in DIMENSIONS:
                d = dimensions.get(dim) or {}
                if d.get("status") in PENDING_OR_RESTART | {"fail", "unverified", "unsupported_with_reason"}:
                    fail(f"{context}: m8_enrollment=live_validated but {dim}={d.get('status')}")

        # application_launch=fail blocks overall enrollment.
        app_launch = (dimensions.get("application_launch") or {}).get("status")
        if app_launch == "fail" and m8 in {"live_validated", "configured_restart_required"}:
            fail(f"{context}: application_launch=fail incompatible with m8_enrollment={m8}")

        # native_memory_lifecycle pass requires same-client evidence artifact with timestamp.
        lifecycle = dimensions.get("native_memory_lifecycle") or {}
        if lifecycle.get("status") == "live_validated":
            if not lifecycle.get("evidence_path") or not lifecycle.get("evidence_ts"):
                fail(f"{context}: native_memory_lifecycle=live_validated requires evidence_path and evidence_ts")
            else:
                # Evidence must be specific to this client (matrix or handoff/audit mentioning the client).
                ev_path = str(lifecycle["evidence_path"]).lower()
                if ide_id.replace("-", "") not in ev_path and ide_id.split("-")[0] not in ev_path:
                    fail(f"{context}: native_memory_lifecycle evidence_path {lifecycle['evidence_path']!r} must reference this client")


def validate_profile_matrix_equality(matrix: dict[str, Any], profiles: dict[str, dict[str, Any]]) -> None:
    managed = matrix.get("managed_ides") or {}
    for ide_id, ide_data in managed.items():
        profile = profiles.get(ide_id)
        if profile is None:
            fail(f"matrix:{ide_id}: missing profile ide-profiles/{ide_id}/IDE_PROFILE.yaml")
            continue
        context = f"matrix<->profile:{ide_id}"

        matrix_m8 = ide_data.get("m8_enrollment")
        profile_m8 = profile.get("m8_enrollment")
        if matrix_m8 != profile_m8:
            fail(f"{context}: m8_enrollment mismatch matrix={matrix_m8} profile={profile_m8}")

        matrix_dims = ide_data.get("dimensions") or {}
        profile_dims = profile.get("dimensions") or {}
        if set(matrix_dims.keys()) != set(profile_dims.keys()):
            fail(f"{context}: dimension keys mismatch")
        for dim in DIMENSIONS:
            m_dim = matrix_dims.get(dim) or {}
            p_dim = profile_dims.get(dim) or {}
            for key in ("status", "evidence_path", "evidence_ts", "superseded_by"):
                if m_dim.get(key) != p_dim.get(key):
                    fail(f"{context}: dimension {dim} {key} mismatch matrix={m_dim.get(key)!r} profile={p_dim.get(key)!r}")


def validate_temporal_ordering(matrix: dict[str, Any], profiles: dict[str, dict[str, Any]]) -> None:
    """Newer evidence wins; older evidence cannot silently supersede a newer claim."""
    managed = matrix.get("managed_ides") or {}
    for ide_id, ide_data in managed.items():
        dimensions = ide_data.get("dimensions") or {}
        for dim in DIMENSIONS:
            d = dimensions.get(dim) or {}
            superseded_by = d.get("superseded_by")
            if not superseded_by:
                continue
            ts = parse_ts(d.get("evidence_ts"))
            superseded_path = None
            superseded_ts = None
            for other_dim in DIMENSIONS:
                other = dimensions.get(other_dim) or {}
                if other.get("evidence_path") == superseded_by:
                    superseded_path = other.get("evidence_path")
                    superseded_ts = parse_ts(other.get("evidence_ts"))
                    break
            if superseded_path is None:
                # Also allow cross-reference to a handoff/audit file at repo root.
                if (REPO / superseded_by).exists():
                    superseded_ts = None
                else:
                    fail(f"matrix:{ide_id}: dimension {dim} superseded_by {superseded_by!r} does not resolve")
                    continue
            if ts is not None and superseded_ts is not None and ts < superseded_ts:
                fail(f"matrix:{ide_id}: dimension {dim} evidence_ts {d.get('evidence_ts')} is older than superseded_by {superseded_by} ({other.get('evidence_ts')})")


def main() -> int:
    matrix = load_matrix()
    profiles = load_profiles()

    validate_matrix_invariants(matrix)
    validate_profile_matrix_equality(matrix, profiles)
    validate_temporal_ordering(matrix, profiles)

    if FAILURES:
        print(f"FAIL {len(FAILURES)} client-status checks:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1

    print("OK: all client-status semantic/temporal checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
