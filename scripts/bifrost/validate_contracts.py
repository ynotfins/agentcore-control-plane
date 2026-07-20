#!/usr/bin/env python3
"""Validate Bifrost upstream registry and gateway client contracts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

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

        # Wildcard permitted_tools cannot coexist with named denied_tools on enabled servers.
        # An explicit allowlist must be materialized from discovered inventory instead.
        # Deferred/disabled servers are exempt (transitional wildcard state is documented in
        # tool_lifecycle_note; enforcement is for servers that actually render into Bifrost config).
        permitted = server.get("permitted_tools") or []
        denied = server.get("denied_tools") or []
        if permitted == ["*"] and denied and server.get("enabled"):
            errors.append(
                f"servers.{key}: wildcard permitted_tools ['*'] combined with named "
                f"denied_tools {denied!r} is forbidden on an enabled server — materialize "
                f"an explicit allowlist from the discovered tool inventory"
            )

        # Tool group consistency: every tool in a group must appear in permitted_tools or denied_tools.
        tool_groups = server.get("tool_groups") or {}
        all_declared = set(permitted) | set(denied)
        if all_declared and tool_groups:
            for gname, gdef in tool_groups.items():
                for t in gdef.get("tools") or []:
                    if t not in all_declared:
                        errors.append(
                            f"servers.{key}.tool_groups.{gname}: "
                            f"tool {t!r} not in permitted_tools or denied_tools"
                        )

    # Profile references
    profiles = registry.get("capability_profiles") or {}
    for pid, profile in profiles.items():
        for sid in profile.get("allowed_server_ids") or []:
            if sid not in registry.get("servers", {}):
                errors.append(f"capability_profiles.{pid}: unknown server {sid}")

    # OpenRouter invariant: must be registered dormant; must not appear in any allowed_server_ids.
    if "openrouter" in (registry.get("servers") or {}):
        or_server = registry["servers"]["openrouter"]
        if or_server.get("status") not in ("dormant", "disabled", "deferred"):
            errors.append(
                "openrouter server must have status 'dormant' (registered dormant by default; "
                "tools require a live M6 capability lease)"
            )
        for pid, profile in profiles.items():
            if "openrouter" in (profile.get("allowed_server_ids") or []):
                errors.append(
                    f"capability_profiles.{pid}: openrouter must not appear in allowed_server_ids — "
                    f"zero tools are exposed without an active M6 capability lease"
                )

    # General dormant zero-default-exposure: status dormant must not receive permanent profile grants.
    for sid, server in (registry.get("servers") or {}).items():
        if server.get("status") == "dormant":
            for pid, profile in profiles.items():
                if sid in (profile.get("allowed_server_ids") or []):
                    errors.append(
                        f"capability_profiles.{pid}: dormant server {sid!r} must not appear in "
                        f"allowed_server_ids (zero tools without lease)"
                    )

    # Authority-blocked servers must never be registered.
    for blocked in ("context7", "hostinger"):
        for sid in (registry.get("servers") or {}):
            if blocked in sid.lower():
                errors.append(
                    f"servers.{sid}: blocked_authority ({blocked}) — remove or keep catalog-only; "
                    f"see docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md"
                )

    return errors


def stub_master_config_drift() -> list[str]:
    """Verify MASTER_CONFIG_AND_PROMPT.md contains the required universal IDE setup rules."""
    master = REPO_ROOT / "MASTER_CONFIG_AND_PROMPT.md"
    if not master.exists():
        return ["MASTER_CONFIG_AND_PROMPT.md missing"]
    content = master.read_text(encoding="utf-8")
    errors: list[str] = []

    required_phrases = [
        # Gate architecture
        ("agentcore-gateway", "missing single agentcore-gateway entry rule"),
        ("http://127.0.0.1:8080/mcp", "missing canonical gateway URL"),
        # Ten-tool surface
        ("memory_status", "missing memory_status tool"),
        ("startup_context", "missing startup_context tool"),
        ("retrieve_context", "missing retrieve_context tool"),
        ("append_event", "missing append_event tool"),
        ("propose_fact", "missing propose_fact tool"),
        ("expand_source", "missing expand_source tool"),
        ("session_open", "missing session_open tool"),
        ("session_close", "missing session_close tool"),
        ("build_handoff", "missing build_handoff tool"),
        ("docs_search", "missing docs_search tool"),
        # Durable memory contract
        ("effectively unbounded", "missing unbounded-memory contract language"),
        ("model-limit-aware", "missing model-limit-aware contract language"),
        ("non-destructive", "missing non-destructive compaction language"),
        # Database gating
        ("no direct database access" if "no direct database access" in content.lower() else
         "Never put" if "Never put" in content else "AGENT_CORE_PG",
         "missing no-database-credentials-in-IDE rule"),
        # Projections
        ("never directly edit", "missing projection non-edit rule (agents never edit STATE/CONTEXT_INDEX)"),
        # Swarm exclusion
        ("SwarmRecall", "missing Swarm exclusion rule"),
        # Resource location (M8 consolidation additions)
        ("CONTEXT_INDEX", "missing CONTEXT_INDEX location-map behavior"),
        ("register_artifact_location", "missing resource-location registration requirement"),
        ("unregistered", "missing no-unregistered-paths rule"),
        ("v_project_resource_map", "missing project resource map view reference"),
        # Identity binding
        ("session_open", "missing session/worktree identity binding (session_open)"),
    ]

    for phrase, description in required_phrases:
        if phrase not in content:
            errors.append(f"MASTER_CONFIG: {description} (expected: {phrase!r})")

    return errors


def authority_policy_checks(registry: dict[str, Any]) -> list[str]:
    """Deterministic authority-reconciliation checks (2026-07-14)."""
    errors: list[str] = []

    # Policy contracts present and (for JSON) schema-valid.
    policy_pairs = [
        ("contracts/project-execution-policy.json", "contracts/schemas/project-execution-policy.schema.json"),
        ("contracts/project-tool-lifecycle.json", "contracts/schemas/project-tool-lifecycle.schema.json"),
        ("contracts/model-context-profiles.json", "contracts/schemas/model-context-profiles.schema.json"),
    ]
    for contract_rel, schema_rel in policy_pairs:
        contract_path = REPO_ROOT / contract_rel
        schema_path = REPO_ROOT / schema_rel
        if not contract_path.exists():
            errors.append(f"{contract_rel} missing")
            continue
        if not schema_path.exists():
            errors.append(f"{schema_rel} missing")
            continue
        errors.extend(validate_schema(load(contract_path), load(schema_path), contract_rel))

    profile_path = REPO_ROOT / "contracts" / "model-context-profiles.json"
    if profile_path.exists():
        profiles = load(profile_path)
        by_name = {row["profile_name"]: row for row in profiles.get("profiles", [])}
        one_million = by_name.get("one-million-context") or {}
        future = by_name.get("future-above-million") or {}
        if one_million.get("hard_context_limit") != 1_000_000:
            errors.append("one-million-context hard_context_limit must remain exactly 1000000")
        if int(future.get("hard_context_limit") or 0) <= 1_000_000:
            errors.append("future-above-million must prove context limits above 1000000 are accepted")
        if profiles.get("default_profile") in {"acceptance-small", "legacy-4096"}:
            errors.append("small/4096 acceptance profiles cannot be the production default")

    # Canonical global agent policy (YAML) present and schema-valid.
    gap_path = REPO_ROOT / "contracts" / "global-agent-policy.yaml"
    gap_schema_path = REPO_ROOT / "contracts" / "schemas" / "global-agent-policy.schema.json"
    if not gap_path.exists():
        errors.append("contracts/global-agent-policy.yaml missing")
    elif not gap_schema_path.exists():
        errors.append("contracts/schemas/global-agent-policy.schema.json missing")
    else:
        try:
            import yaml  # noqa: PLC0415 - optional dependency guarded at runtime

            policy = yaml.safe_load(gap_path.read_text(encoding="utf-8"))
            errors.extend(validate_schema(policy, load(gap_schema_path), "global-agent-policy"))
        except ImportError:
            errors.append("PyYAML required to validate contracts/global-agent-policy.yaml")

    # Memory-platform execution authority present.
    plan_path = REPO_ROOT / "docs" / "memory-platform" / "MEMORY_PLATFORM_EXECUTION_PLAN.md"
    if not plan_path.exists():
        errors.append("docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md missing")

    # BLUEPRINT.md present and classified as current in DOC_AUTHORITY.
    blueprint_path = REPO_ROOT / "BLUEPRINT.md"
    if not blueprint_path.exists():
        errors.append("BLUEPRINT.md missing from repository root")

    # DOC_AUTHORITY classification checks.
    doc_authority_path = REPO_ROOT / "DOC_AUTHORITY.md"
    doc_authority = doc_authority_path.read_text(encoding="utf-8") if doc_authority_path.exists() else ""
    if not doc_authority:
        errors.append("DOC_AUTHORITY.md missing")
    else:
        if "MEMORY_PLATFORM_EXECUTION_PLAN.md" not in doc_authority:
            errors.append("DOC_AUTHORITY.md does not reference the memory-platform execution plan")
        if "ChaosCentral-Current-Build" not in doc_authority:
            errors.append("DOC_AUTHORITY.md does not reference the machine-fact authority")
        # database-plan.md must not be classified as authoritative-stable.
        stable_section = doc_authority.split("## Authoritative — stable", 1)[-1].split("## Current-state", 1)[0]
        if "database-plan.md" in stable_section:
            errors.append("DOC_AUTHORITY.md still classifies database-plan.md as authoritative-stable")
        # CONTEXT_BLOCK.md must appear as current-state, not only historical.
        current_section = doc_authority.split("## Current-state", 1)[-1].split("## Bifrost", 1)[0]
        if "CONTEXT_BLOCK.md" not in current_section:
            errors.append("DOC_AUTHORITY.md does not classify CONTEXT_BLOCK.md as current-state")
        # BLUEPRINT.md must be classified as authoritative-stable.
        stable_section_full = doc_authority.split("## Authoritative", 1)[-1].split("## Current-state", 1)[0] if "## Authoritative" in doc_authority else ""
        if "BLUEPRINT.md" not in stable_section_full:
            errors.append("DOC_AUTHORITY.md does not classify BLUEPRINT.md as authoritative")

    # Historical banners on stale executable documents.
    banner_required = {
        "AGENT_DATABASE_BOOTSTRAP.md": "HISTORICAL",
        "database-plan.md": "HISTORICAL SCHEMA EVIDENCE",
        "CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md": "HISTORICAL",
        "Global-memory-and-context-system-revised-2.md": "DO NOT EXECUTE",
        "docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md": "DO NOT EXECUTE",
    }
    for rel, marker in banner_required.items():
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        head = path.read_text(encoding="utf-8", errors="replace")[:1500]
        if marker.lower() not in head.lower():
            errors.append(f"{rel}: missing required banner marker '{marker}' near top of file")

    # CONTEXT_BLOCK.md must be current: no stray opening code fence, no H:-provisioning language.
    context_block_path = REPO_ROOT / "CONTEXT_BLOCK.md"
    if context_block_path.exists():
        text = context_block_path.read_text(encoding="utf-8", errors="replace")
        if text.lstrip().startswith("```"):
            errors.append("CONTEXT_BLOCK.md starts with a stray code fence")
        if "provision H: as" in text:
            errors.append("CONTEXT_BLOCK.md still contains H:-provisioning language (H: is live)")

    # Wildcard grants must be covered by a documented transitional note.
    wildcard_servers = [
        key for key, server in (registry.get("servers") or {}).items()
        if server.get("permitted_tools") == ["*"]
    ]
    if wildcard_servers and "tool_lifecycle_note" not in registry:
        errors.append(
            "registry has permitted_tools:['*'] grants without a tool_lifecycle_note transitional exception: "
            + ", ".join(sorted(wildcard_servers))
        )

    # Current rule files must not teach retired routes.
    current_rule_files = [
        "AGENTS.md",
        "CLAUDE.md",
        "rules/canonical/GLOBAL_AGENT_RULES.md",
        "rules/global-mcp-routing.md",
        "rules/environment-and-secrets.md",
        ".cursor/rules/agentcore-env-policy.mdc",
    ]
    retired_patterns = [
        (re.compile(r"DEPWIRE_NO_TELEMETRY\s*=\s*1"), "sets DEPWIRE_NO_TELEMETRY=1"),
        (re.compile(r"use\s+`?global-memory-gateway`?\s+only", re.IGNORECASE), "mandates retired global-memory-gateway"),
        (re.compile(r"must\s+use\s+`?global-memory-gateway`?", re.IGNORECASE), "mandates retired global-memory-gateway"),
    ]
    for rel in current_rule_files:
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern, description in retired_patterns:
            if pattern.search(text):
                errors.append(f"{rel}: current rule file {description}")

    return errors


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
    errors.extend(authority_policy_checks(registry))
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
    print("OK: authority + policy contracts valid (hierarchy, banners, wildcard transitional note, rule files)")
    print("OK: master-config drift check stub (no hard failures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
