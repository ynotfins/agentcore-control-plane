#!/usr/bin/env python3
"""Validate the source-only MCP admission catalog and fail-closed boundaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
SCHEMA_PATH = (
    REPO_ROOT / "contracts" / "schemas" / "bifrost-upstream-mcp-registry.schema.json"
)

CATALOGUED_SERVER_IDS = frozenset({"shadcn", "posthog", "agentmail"})
REJECTED_SERVER_IDS = frozenset(
    {
        "fetch-mcp",
        "wcgw",
        "docker-mcp-toolkit",
        "postgresql-mcp",
        "sqlite-mcp",
        "ref-mcp",
    }
)
CANDIDATE_SERVER_IDS = CATALOGUED_SERVER_IDS | REJECTED_SERVER_IDS
PRIMARY_EXISTING_SERVER_IDS = frozenset(
    {
        "serena",
        "sequential-thinking",
        "tentra",
        "depwire",
        "filesystem",
        "github-mcp",
        "playwright",
    }
)
FORBIDDEN_NFA_MARKERS = (
    r"D:\github\nfa-platform",
    "nfa_devin_dev",
    "nfa_ingest_capture",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _candidate_sensitive_fields(server: dict[str, Any]) -> dict[str, Any]:
    evidence = server.get("admission_evidence") or {}
    return {
        "candidate_roots": (evidence.get("storage") or {}).get("candidate_roots") or [],
        "arguments": server.get("arguments") or [],
        "headers": server.get("headers") or {},
        "dsn_references": (evidence.get("authentication") or {}).get("dsn_references") or [],
        "profiles": server.get("capability_profiles") or [],
        "canaries": (evidence.get("canary") or {}).get("probes") or [],
        "database_allowlist": evidence.get("database_allowlist") or [],
    }


def validate_admission_contract(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    servers = registry.get("servers") or {}
    profiles = registry.get("capability_profiles") or {}

    missing = sorted((CANDIDATE_SERVER_IDS | PRIMARY_EXISTING_SERVER_IDS) - set(servers))
    if missing:
        errors.append(f"missing primary MCP admission records: {missing}")

    profile_members = {
        server_id
        for profile in profiles.values()
        for server_id in (profile.get("allowed_server_ids") or [])
    }

    for server_id in sorted(CANDIDATE_SERVER_IDS):
        server = servers.get(server_id)
        if not server:
            continue
        expected_status = "rejected" if server_id in REJECTED_SERVER_IDS else "catalogued_unverified"
        if server.get("status") != expected_status:
            errors.append(f"servers.{server_id}: status must be {expected_status}")
        if server.get("enabled") is not False:
            errors.append(f"servers.{server_id}: candidate must be disabled")
        if server.get("capability_profiles") != []:
            errors.append(f"servers.{server_id}: candidate must have zero capability profiles")
        if server.get("permitted_tools") != []:
            errors.append(f"servers.{server_id}: candidate must have zero permitted tools")
        if server_id in profile_members:
            errors.append(f"servers.{server_id}: candidate must not appear in allowed_server_ids")

        evidence = server.get("admission_evidence") or {}
        disposition = evidence.get("default_disposition") or {}
        expected_disposition = "rejected" if server_id in REJECTED_SERVER_IDS else "catalogued_zero_profile"
        if disposition.get("state") != expected_disposition:
            errors.append(
                f"servers.{server_id}: default disposition must be {expected_disposition}"
            )
        if not str(disposition.get("replacement_route") or "").strip():
            errors.append(f"servers.{server_id}: replacement_route is required")

        for location, value in _candidate_sensitive_fields(server).items():
            for text in _strings(value):
                lowered = text.replace("/", "\\").lower()
                for marker in FORBIDDEN_NFA_MARKERS:
                    normalized_marker = marker.replace("/", "\\").lower()
                    if normalized_marker in lowered:
                        errors.append(
                            f"servers.{server_id}.{location}: forbidden NFA marker {marker!r}"
                        )

    for server_id in sorted(CANDIDATE_SERVER_IDS | PRIMARY_EXISTING_SERVER_IDS):
        server = servers.get(server_id)
        if not server:
            continue
        evidence = server.get("admission_evidence")
        if not isinstance(evidence, dict):
            errors.append(f"servers.{server_id}: admission_evidence is required")
            continue
        artifact = evidence.get("artifact") or {}
        if artifact.get("version") != server.get("pinned_version"):
            errors.append(
                f"servers.{server_id}: admission artifact version must match pinned_version"
            )
        if server.get("enabled") and "*" in (server.get("permitted_tools") or []):
            errors.append(f"servers.{server_id}: enabled admission record requires named tools")

        inventory = evidence.get("tool_inventory") or {}
        if inventory.get("status") == "verified":
            declared = set(server.get("permitted_tools") or []) | set(server.get("denied_tools") or [])
            inventoried = set(inventory.get("tools") or [])
            if declared != inventoried:
                errors.append(
                    f"servers.{server_id}: verified tool inventory must equal permitted plus denied tools"
                )

    dormant_expected = {
        "serena": "dormant_project_scoped",
        "tentra": "dormant_project_scoped",
        "depwire": "dormant_project_scoped",
        "filesystem": "dormant_project_scoped",
    }
    for server_id, expected_status in dormant_expected.items():
        server = servers.get(server_id) or {}
        if (
            server.get("status") != expected_status
            or server.get("enabled") is not False
            or server.get("capability_profiles") != []
        ):
            errors.append(
                f"servers.{server_id}: must remain disabled {expected_status} with zero profiles"
            )

    playwright = servers.get("playwright") or {}
    playwright_groups = playwright.get("tool_groups") or {}
    expected_group_policies = {
        "playwright-inspection": "default_profile",
        "playwright-interaction": "default_profile",
        "playwright-high-risk": "default_profile",
    }
    for group_id, access_policy in expected_group_policies.items():
        group = playwright_groups.get(group_id) or {}
        if group.get("access_policy") != access_policy:
            errors.append(
                f"servers.playwright.tool_groups.{group_id}: access_policy must be {access_policy}"
            )
    if playwright.get("is_code_mode_client") is not True:
        errors.append("servers.playwright: Code Mode must remain enabled")

    github = servers.get("github-mcp") or {}
    github_digest = "sha256:5c83359327a0bacc3d34db730bea6557d39d341cee0bf6c58c9a896e33150e80"
    github_ref = f"ghcr.io/github/github-mcp-server:1.3.0@{github_digest}"
    github_artifact = (github.get("admission_evidence") or {}).get("artifact") or {}
    if (
        github.get("pinned_version") != "1.3.0"
        or github_ref not in (github.get("arguments") or [])
        or github_artifact.get("digest") != github_digest
        or github.get("status") != "deferred"
        or github.get("enabled") is not False
        or github.get("permitted_tools") != []
        or github.get("capability_profiles") != []
    ):
        errors.append("servers.github-mcp: must remain digest-pinned and deferred fail-closed")

    for server_id in ("postgresql-mcp", "sqlite-mcp"):
        server = servers.get(server_id) or {}
        evidence = server.get("admission_evidence") or {}
        protected = evidence.get("protected_resources") or {}
        if (
            server.get("status") != "rejected"
            or server.get("permitted_tools") != []
            or server.get("capability_profiles") != []
            or protected.get("default_access") not in {"none", "rejected"}
            or evidence.get("database_allowlist") != []
        ):
            errors.append(f"servers.{server_id}: normal IDE database write surface is forbidden")

    return errors


def _schema_errors(registry: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(registry), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"schema {path}: {error.message}")
    return errors


def main() -> int:
    registry = _load(REGISTRY_PATH)
    schema = _load(SCHEMA_PATH)
    errors = _schema_errors(registry, schema) + validate_admission_contract(registry)
    if errors:
        print(f"FAILED ({len(errors)} errors)")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("OK: source-only MCP admission contract valid")
    print(f"OK: catalogued={len(CATALOGUED_SERVER_IDS)} rejected={len(REJECTED_SERVER_IDS)}")
    print("OK: NFA roots, DSNs, profiles, canaries, and database allowlists excluded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
