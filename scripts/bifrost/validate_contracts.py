#!/usr/bin/env python3
"""Validate Bifrost upstream registry and gateway client contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
REGISTRY_SCHEMA = REPO_ROOT / "contracts" / "schemas" / "bifrost-upstream-mcp-registry.schema.json"
GATEWAY = REPO_ROOT / "contracts" / "agentcore-gateway-client.json"
GATEWAY_SCHEMA = REPO_ROOT / "contracts" / "schemas" / "agentcore-gateway-client.schema.json"

HYPHEN_OK = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
UNDERSCORE_ONLY = re.compile(r"^[a-z][a-z0-9_]*$")
SWARM_MARKERS = ("swarmrecall", "swarmvault", "swarmclaw", "agentswarm")


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_schema(instance: Any, schema: dict[str, Any], label: str) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    out: list[str] = []
    for err in errors:
        path = ".".join(str(p) for p in err.path) or "<root>"
        out.append(f"{label}: {path}: {err.message}")
    return out


def semantic_registry_checks(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("gateway_id") != "agentcore-gateway":
        errors.append("gateway_id must be agentcore-gateway")

    for marker in registry.get("swarm_exclusion") or []:
        if not isinstance(marker, str) or not marker.strip():
            errors.append("swarm_exclusion entries must be non-empty strings")

    for key, server in (registry.get("servers") or {}).items():
        cid = server.get("canonical_id")
        bname = server.get("bifrost_client_name")
        if cid != key:
            errors.append(f"servers.{key}: canonical_id must match object key")
        if cid and not HYPHEN_OK.match(cid):
            errors.append(f"servers.{key}: invalid canonical_id")
        if bname and not UNDERSCORE_ONLY.match(bname):
            errors.append(f"servers.{key}: bifrost_client_name must be underscore-only")
        if bname and "-" in bname:
            errors.append(f"servers.{key}: bifrost_client_name must not contain hyphens")
        lowered = (cid or "").lower()
        if any(m in lowered for m in SWARM_MARKERS):
            errors.append(f"servers.{key}: Swarm servers must not appear in Bifrost registry")
        if server.get("connection_type") == "router" and not server.get("wrapper_script"):
            errors.append(f"servers.{key}: router requires wrapper_script")
        # No secret literals
        blob = json.dumps(server)
        for needle in ("sk-proj-", "sk-ant-", "ghp_", "Bearer sk-"):
            if needle in blob:
                errors.append(f"servers.{key}: possible secret literal ({needle})")

        # depwire must not force DEPWIRE_NO_TELEMETRY
        if cid == "depwire":
            envs = server.get("env_var_names") or []
            if "DEPWIRE_NO_TELEMETRY" in envs:
                errors.append("depwire must not set DEPWIRE_NO_TELEMETRY by default")

    # Profile references
    profiles = registry.get("capability_profiles") or {}
    for pid, profile in profiles.items():
        for sid in profile.get("allowed_server_ids") or []:
            if sid not in registry.get("servers", {}):
                errors.append(f"capability_profiles.{pid}: unknown server {sid}")

    return errors


def stub_master_config_drift() -> list[str]:
    """Placeholder for later MASTER_CONFIG section drift checks."""
    # Intentionally soft: report notice only when file missing.
    master = REPO_ROOT / "MASTER_CONFIG_AND_PROMPT.md"
    if not master.exists():
        return ["MASTER_CONFIG_AND_PROMPT.md missing (drift check stub)"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-master-drift", action="store_true", help="Treat master drift stub notices as errors")
    args = parser.parse_args()

    errors: list[str] = []
    notices: list[str] = []

    registry = load(REGISTRY)
    registry_schema = load(REGISTRY_SCHEMA)
    gateway = load(GATEWAY)
    gateway_schema = load(GATEWAY_SCHEMA)

    errors.extend(validate_schema(registry, registry_schema, "registry"))
    errors.extend(validate_schema(gateway, gateway_schema, "gateway-client"))
    errors.extend(semantic_registry_checks(registry))
    notices.extend(stub_master_config_drift())

    if notices:
        for n in notices:
            print(f"NOTICE: {n}")
        if args.strict_master_drift and notices:
            errors.extend(notices)

    if errors:
        print(f"FAILED ({len(errors)} errors)")
        for e in errors:
            print(f"  - {e}")
        return 1

    enabled = [k for k, v in registry["servers"].items() if v.get("enabled")]
    print("OK: registry + gateway-client schemas valid")
    print(f"OK: enabled servers={len(enabled)} disabled/deferred={len(registry['servers']) - len(enabled)}")
    print("OK: master-config drift check stub (no hard failures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
