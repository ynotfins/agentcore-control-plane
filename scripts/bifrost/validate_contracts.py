#!/usr/bin/env python3
"""Validate Bifrost upstream registry and gateway client contracts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
REGISTRY_SCHEMA = REPO_ROOT / "contracts" / "schemas" / "bifrost-upstream-mcp-registry.schema.json"
GATEWAY = REPO_ROOT / "contracts" / "agentcore-gateway-client.json"
GATEWAY_SCHEMA = REPO_ROOT / "contracts" / "schemas" / "agentcore-gateway-client.schema.json"
ALIGNMENT_HOSTS = REPO_ROOT / "contracts" / "agentcore-alignment-skill-hosts.json"
IDE_MATRIX = REPO_ROOT / "ide-profiles" / "IDE_CAPABILITY_MATRIX.yaml"

HYPHEN_OK = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
UNDERSCORE_ONLY = re.compile(r"^[a-z][a-z0-9_]*$")
SWARM_MARKERS = ("swarmrecall", "swarmvault", "swarmclaw", "agentswarm")
TRACKED_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openrouter-api-key", re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}")),
    ("openai-project-api-key", re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}")),
    ("anthropic-api-key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("deepseek-api-key", re.compile(r"DEEPSEEK_API_KEY[^\\n\\r]{0,200}sk-[A-Za-z0-9_-]{20,}")),
    ("hindsight-api-key", re.compile(r"HINDSIGHT_API_KEY[^\\n\\r]{0,200}hsk_[A-Za-z0-9_-]{20,}")),
    ("github-token", re.compile(r"ghp_[A-Za-z0-9_]{20,}")),
    ("bearer-sk-token", re.compile(r"Bearer\s+sk-[A-Za-z0-9_-]{20,}")),
)
TRACKED_SECRET_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "scripts/bifrost/mcp_output_schema.py": (
        "sk-[A-Za-z0-9_\\-]{12,}",
        "sk-abcdefghijklmnop",
        "sk-abcdefghijklmnopqrst",
    ),
    "tools/cheap-workers/secret-safety.test.mjs": (
        "sk-test-active-secret-1234567890",
        "sk-or-v1-" + "abcdefghijklmnopqrstuvwxyz123456",
    ),
}
REQUIRED_TASK2_HOSTS = {
    "cursor",
    "codex",
    "devin",
    "eigent",
    "zed",
    "minimax",
    "mavis",
    "reasonix",
    "opencode",
    "open-design",
    "autogpt",
    "agent-orchestrator",
    "cherry-studio",
    "lobehub",
    "openhands",
    "antigravity",
    "zcode",
    "open-interpreter",
    "openclaw",
    "clawx",
}


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
    profiles = registry.get("capability_profiles") or {}
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

        if key == "clasp-mcp":
            upstream_tools = {
                "list_projects",
                "pull_files",
                "clone_project",
                "create_project",
                "push_files",
            }
            for tool in sorted(upstream_tools.intersection(permitted)):
                errors.append(
                    f"servers.{key}: clasp tool {tool!r} requires an isolation adapter "
                    "that prevents implicit parent discovery and validates provider-returned "
                    "Windows filenames before filesystem access"
                )

        # Tool group consistency: every tool in a group must appear in permitted_tools or denied_tools.
        tool_groups = server.get("tool_groups") or {}
        all_declared = set(permitted) | set(denied)
        if all_declared and tool_groups:
            for gname, gdef in tool_groups.items():
                requires_approval = bool(
                    (gdef.get("lease_defaults") or {}).get("requires_approval")
                )
                permanent_profiles = [
                    pid
                    for pid, profile in profiles.items()
                    if key in (profile.get("allowed_server_ids") or [])
                ]
                for t in gdef.get("tools") or []:
                    if t not in all_declared:
                        errors.append(
                            f"servers.{key}.tool_groups.{gname}: "
                            f"tool {t!r} not in permitted_tools or denied_tools"
                        )
                    if requires_approval and t in permitted and permanent_profiles:
                        errors.append(
                            f"servers.{key}.tool_groups.{gname}: approval-required tool "
                            f"{t!r} cannot be granted permanently through profiles "
                            f"{permanent_profiles!r}; deny it or remove the permanent server grant"
                        )

    # Profile references
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
    for blocked in ("hostinger",):  # context7 unblocked AUTH-2026-08-30-GLOBAL-LOCAL-DOCS-INGEST
        for sid in (registry.get("servers") or {}):
            if blocked in sid.lower():
                errors.append(
                    f"servers.{sid}: blocked_authority ({blocked}) — remove or keep catalog-only; "
                    f"see docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md"
                )

    return errors


def output_schema_checks() -> list[str]:
    """Delegate MCP outputSchema coverage to scripts/bifrost/validate_output_schemas.py.

    Contract-level gate only (--skip-rendered): a stale generated Bifrost artifact is
    reported by test_contracts.py, which runs the full validator including the
    rendered-artifact drift gate.
    """
    validator = REPO_ROOT / "scripts" / "bifrost" / "validate_output_schemas.py"
    if not validator.exists():
        return ["output-schema: scripts/bifrost/validate_output_schemas.py missing"]
    result = subprocess.run(
        [sys.executable, str(validator), "--skip-rendered"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    if result.returncode == 0:
        return []
    detail = [
        line.strip()[2:].strip()
        for line in (result.stdout or result.stderr).splitlines()
        if line.strip().startswith("- ")
    ]
    if not detail:
        detail = [f"validator exited {result.returncode}"]
    return [f"output-schema: {line}" for line in detail]


def authority_lock_checks() -> list[str]:
    validator = REPO_ROOT / "scripts" / "validate_authority_lock.py"
    if not validator.exists():
        return ["authority-lock: scripts/validate_authority_lock.py missing"]
    result = subprocess.run(
        [sys.executable, str(validator)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    if result.returncode == 0:
        return []
    detail = [
        line.strip()[2:].strip()
        for line in (result.stdout or result.stderr).splitlines()
        if line.strip().startswith("- ")
    ]
    if not detail:
        detail = [f"validator exited {result.returncode}"]
    return [f"authority-lock: {line}" for line in detail]


def tracked_secret_checks() -> list[str]:
    """Scan every tracked text file for high-confidence secret material."""
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    if result.returncode != 0:
        return [f"tracked-secrets: git ls-files exited {result.returncode}"]

    errors: list[str] = []
    rel_paths = [
        rel.decode("utf-8", errors="replace")
        for rel in result.stdout.split(b"\0")
        if rel
    ]
    for rel in rel_paths:
        path = REPO_ROOT / rel
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeError):
            continue

        allowlisted = TRACKED_SECRET_ALLOWLIST.get(rel.replace("\\", "/"), ())
        for label, pattern in TRACKED_SECRET_PATTERNS:
            if not pattern.search(text):
                continue
            if allowlisted and all(hit in allowlisted for hit in set(pattern.findall(text))):
                continue
            errors.append(f"tracked-secrets: {rel}: possible {label} literal")
            break

    return errors


def task2_contract_profile_checks(gateway: dict[str, Any]) -> list[str]:
    """Enforce the universal host, Code Mode, and evidence alignment contract."""
    import yaml  # noqa: PLC0415

    errors: list[str] = []
    policy = yaml.safe_load(
        (REPO_ROOT / "contracts" / "global-agent-policy.yaml").read_text(encoding="utf-8")
    )
    matrix = yaml.safe_load(IDE_MATRIX.read_text(encoding="utf-8"))
    host_manifest = load(ALIGNMENT_HOSTS)

    rules = {rule["id"]: str(rule["rule"]) for rule in policy.get("mandatory_rules", [])}
    discovery = rules.get("session-tool-discovery", "")
    code_mode_sequence = ("listToolFiles", "readToolFile", "getToolDocs", "executeToolCode")
    positions = [discovery.find(name) for name in code_mode_sequence]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        errors.append(
            "GLOBAL_POLICY: session-tool-discovery must contain ordered Code Mode sequence "
            "listToolFiles -> readToolFile -> getToolDocs -> executeToolCode"
        )
    for phrase in ("Code Mode", "operational issue", "duplicate"):
        if phrase not in discovery:
            errors.append(f"GLOBAL_POLICY: session-tool-discovery missing {phrase!r}")

    required_task_gates = {
        "agentcore-memory",
        "sequential-thinking",
        "serena",
        "depwire",
        "tentra",
        "filesystem",
        "github",
        "playwright",
        "shadcn",
        "posthog",
        "fetch",
        "wcgw",
        "docker",
        "postgresql",
        "sqlite",
        "ref",
        "agentmail",
        "morph",
    }
    task_gates = {gate.get("tool_name") for gate in policy.get("task_class_gates", [])}
    missing_task_gates = sorted(required_task_gates - task_gates)
    if missing_task_gates:
        errors.append(f"GLOBAL_POLICY: missing primary tool-routing gates {missing_task_gates}")

    managed = matrix.get("managed_ides") or {}
    candidates = matrix.get("managed_candidates") or {}
    represented_hosts = set(managed) | set(candidates)
    if matrix.get("mavis_alias_note"):
        represented_hosts.add("mavis")
    missing_matrix_hosts = sorted(REQUIRED_TASK2_HOSTS - represented_hosts)
    if missing_matrix_hosts:
        errors.append(f"MATRIX: missing managed/candidate hosts {missing_matrix_hosts}")

    manifest_hosts = {entry.get("host") for entry in host_manifest.get("hosts", [])}
    missing_manifest_hosts = sorted(REQUIRED_TASK2_HOSTS - manifest_hosts)
    if missing_manifest_hosts:
        errors.append(f"ALIGNMENT_HOSTS: missing hosts {missing_manifest_hosts}")

    swarm_clients = matrix.get("swarm_managed_clients") or {}
    expected_host_certification = {
        "openclaw": "configured_restart_required",
        "clawx": "unverified",
    }
    for host in ("openclaw", "clawx"):
        if host in swarm_clients:
            errors.append(f"MATRIX: {host} must not remain in swarm_managed_clients")
        candidate = candidates.get(host) or {}
        if candidate.get("ownership") != "agentcore":
            errors.append(f"MATRIX: {host} ownership must be agentcore")
        expected_certification = expected_host_certification[host]
        if candidate.get("certification") != expected_certification:
            errors.append(
                f"MATRIX: {host} certification must be {expected_certification}"
            )
        for dimension, details in (candidate.get("dimensions") or {}).items():
            if details.get("status") == "live_validated" and not (
                details.get("evidence_path") and details.get("evidence_ts")
            ):
                errors.append(
                    f"MATRIX: {host} {dimension}=live_validated requires evidence_path and evidence_ts"
                )
        manifest_entry = next(
            (entry for entry in host_manifest.get("hosts", []) if entry.get("host") == host),
            {},
        )
        if manifest_entry.get("ownership") != "agentcore":
            errors.append(f"ALIGNMENT_HOSTS: {host} ownership must be agentcore")
    openclaw = candidates.get("openclaw") or {}
    expected_roots = {
        "governed_product_root": r"D:\github\open--claw",
        "windows_operations_root": r"D:\openclaw",
        "excluded_live_state_root": r"C:\Users\ynotf\.openclaw",
        "gateway_url": "http://127.0.0.1:8080/mcp",
        "gateway_auth_mode": "dedicated_bearer_env",
        "capability_profile": "openclaw",
    }
    for field, expected in expected_roots.items():
        if openclaw.get(field) != expected:
            errors.append(f"MATRIX: openclaw {field} must be {expected}")
    if (candidates.get("clawx") or {}).get("installer_root") != r"C:\Program Files\ClawX":
        errors.append(r"MATRIX: clawx installer_root must be C:\Program Files\ClawX")

    client_hints = gateway.get("client_render_hints") or {}
    openclaw_hint = client_hints.get("openclaw") or {}
    expected_openclaw_hint = {
        "enabled": True,
        "config_path": r"C:\Users\ynotf\.openclaw\openclaw.json",
        "syntax": "openclaw_json",
        "supports_env_headers": True,
    }
    for field, expected in expected_openclaw_hint.items():
        if openclaw_hint.get(field) != expected:
            errors.append(f"gateway-client: openclaw {field} must be {expected!r}")

    clawx_hint = client_hints.get("clawx") or {}
    if clawx_hint.get("enabled") is not False or clawx_hint.get("syntax") != "skip_openclaw":
        errors.append("gateway-client: clawx must remain a disabled unverified skip_openclaw hint")

    stale_openclaw = "OpenClaw/ClawX are Swarm-managed"
    if stale_openclaw.lower() in json.dumps(policy).lower():
        errors.append("GLOBAL_POLICY: stale OpenClaw/ClawX Swarm classification")

    devin_paths = [
        REPO_ROOT / "ide-profiles" / "devin" / "MCP_CONFIG_TEMPLATE.json",
        REPO_ROOT / "renderers" / "gateway-clients" / "devin.json",
    ]
    for path in devin_paths:
        artifact = load(path)
        servers = [k for k in (artifact.get("mcpServers") or {}).keys() if k != "claude-context"]
        if servers != ["agentcore-gateway"]:
            errors.append(f"{path.relative_to(REPO_ROOT)}: Devin AgentCore template must be gateway-only")
    devin_text_paths = [
        *devin_paths,
        REPO_ROOT / "ide-profiles" / "devin" / "IDE_PROFILE.yaml",
    ]
    for path in devin_text_paths:
        body = path.read_text(encoding="utf-8", errors="replace").lower()
        for forbidden in ("public tunnel", "tunnel http", "install directly", "paste_project_root_here"):
            if forbidden in body:
                errors.append(f"{path.relative_to(REPO_ROOT)}: stale Devin route {forbidden!r}")

    reasonix_profile = REPO_ROOT / "ide-profiles" / "reasonix" / "IDE_PROFILE.yaml"
    reasonix_rules = REPO_ROOT / "ide-profiles" / "reasonix" / "GLOBAL_RULES.md"
    reasonix = yaml.safe_load(reasonix_profile.read_text(encoding="utf-8"))
    if "hindsight" in (
        reasonix_profile.read_text(encoding="utf-8", errors="replace")
        + reasonix_rules.read_text(encoding="utf-8", errors="replace")
    ).lower():
        errors.append("Reasonix: unsupported Hindsight claim remains")
    if reasonix.get("m8_enrollment") == "live_validated" or any(
        dimension.get("status") == "live_validated"
        for dimension in (reasonix.get("dimensions") or {}).values()
    ):
        errors.append("Reasonix: live_validated claim remains without accepted evidence")

    for profile_path in sorted((REPO_ROOT / "ide-profiles").glob("*/IDE_PROFILE.yaml")):
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        for dimension, details in (profile.get("dimensions") or {}).items():
            evidence_path = details.get("evidence_path") if isinstance(details, dict) else None
            if evidence_path and not (REPO_ROOT / evidence_path).is_file():
                errors.append(
                    f"{profile_path.relative_to(REPO_ROOT)}: {dimension} evidence_path does not exist: "
                    f"{evidence_path}"
                )
    for host, host_data in managed.items():
        for dimension, details in (host_data.get("dimensions") or {}).items():
            evidence_path = details.get("evidence_path") if isinstance(details, dict) else None
            if evidence_path and not (REPO_ROOT / evidence_path).is_file():
                errors.append(
                    f"MATRIX: {host}.{dimension} evidence_path does not exist: {evidence_path}"
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


def strict_master_config_audit(registry: dict[str, Any]) -> list[str]:
    """Hard-failure audit of MASTER_CONFIG_AND_PROMPT.md and related enrollment surfaces."""
    import yaml  # noqa: PLC0415

    errors: list[str] = []
    master = REPO_ROOT / "MASTER_CONFIG_AND_PROMPT.md"
    install_prompt = REPO_ROOT / "docs" / "prompts" / "install-agentcore-gateway-in-ide.md"
    matrix_path = REPO_ROOT / "ide-profiles" / "IDE_CAPABILITY_MATRIX.yaml"

    if not master.exists():
        return ["MASTER_CONFIG_AND_PROMPT.md missing"]
    content = master.read_text(encoding="utf-8")

    # 1. BLUEPRINT.md in authority chain with absolute path
    if "@D:\\github\\agentcore-control-plane\\BLUEPRINT.md" not in content:
        errors.append("MASTER_CONFIG: BLUEPRINT.md missing from authority chain as @-prefixed absolute path")

    # 2. Canonical single gateway entry
    if "agentcore-gateway" not in content or "http://127.0.0.1:8080/mcp" not in content:
        errors.append("MASTER_CONFIG: missing canonical single gateway entry")
    if "${env:BIFROST_MCP_VIRTUAL_KEY}" not in content:
        errors.append("MASTER_CONFIG: missing env-var bearer auth form")

    # 3. Exact ten memory tools
    expected_tools = [
        "memory_status", "startup_context", "retrieve_context", "append_event",
        "propose_fact", "expand_source", "session_open", "session_close",
        "build_handoff", "docs_search",
    ]
    for tool in expected_tools:
        if tool not in content:
            errors.append(f"MASTER_CONFIG: missing memory tool {tool}")

    # 4. Obsidian not presented as default enabled
    if re.search(r"(?i)obsidian[^.\n]{0,80}default[^.\n]{0,80}enabled", content):
        errors.append("MASTER_CONFIG: Obsidian presented as default enabled")
    if re.search(r"(?i)obsidian[^.\n]{0,80}enabled[^.\n]{0,80}by default", content):
        errors.append("MASTER_CONFIG: Obsidian presented as enabled by default")

    # 5. MiniMax Code and Classic not conflated
    if re.search(r"(?i)minimax[^a-z0-9_.]mavis|minimax\s*code/classic|minimax/classic", content):
        errors.append("MASTER_CONFIG: MiniMax Code and Classic may be conflated")
    if "MiniMax Code" not in content or "MiniMax Agent Classic" not in content:
        errors.append("MASTER_CONFIG: MiniMax Code and MiniMax Agent Classic must be listed separately")

    # 6. Mavis not falsely presented as separate executable client
    mavis_row = re.search(r"(?im)^\|\s*mavis\s*\|", content)
    if mavis_row:
        errors.append("MASTER_CONFIG: Mavis listed as a separate managed client in matrix/table")
    if re.search(r"(?i)\bmavis\b[^.\n]{0,120}separate[^.\n]{0,120}client", content):
        if "not a separate" not in content.lower():
            errors.append("MASTER_CONFIG: Mavis presented as a separate executable client")

    # 7. manual/UI-only clients not given direct-write mcp config (matrix + profiles)
    if matrix_path.exists():
        matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
        for ide_id, ide in (matrix.get("managed_ides") or {}).items():
            mode = ide.get("configuration_mode")
            edit = ide.get("editability") or {}
            if mode in ("UI_only", "manual_import") and edit.get("mcp_config") == "direct_write":
                errors.append(f"MATRIX: {ide_id} is {mode} but mcp_config is direct_write")
    for profile_path in sorted((REPO_ROOT / "ide-profiles").glob("*/IDE_PROFILE.yaml")):
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        if profile.get("swarm_managed"):
            continue
        ide_id = profile.get("ide_id") or profile_path.parent.name
        mode = profile.get("installation_mode") or profile.get("configuration_mode")
        edit = profile.get("editability") or {}
        if mode in ("UI_only", "manual_import") and edit.get("mcp_config") == "direct_write":
            errors.append(f"PROFILE: {ide_id} is {mode} but mcp_config is direct_write")

    # 8. Setup prompt must not edit another IDE
    # Covered by scripts/bifrost/validate_ide_enrollment_scope.py; run it as a companion.

    # 9. Required file references use @ + absolute path
    for path in (master, install_prompt):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # Remove command lines (python/pwsh) before checking bare absolute paths;
        # those lines instruct execution, not required reads.
        filtered_lines = [
            line for line in text.splitlines()
            if not re.match(r"^\s*(?:python|py|pwsh|powershell)\s+", line, re.IGNORECASE)
        ]
        filtered_text = "\n".join(filtered_lines)
        # Flag bare D:\github\... or C:\Users\... without @ when instructing reads
        for m in re.finditer(r"(?m)(?<!@)(?<![\w./\\-])(D:\\(?:github|ChaosCentral)[^\s`\"')\]]+\\[^\s`\"')\]]+)(?:\.(?:md|yaml|yml|json|py))", filtered_text):
            errors.append(f"{path.name}: absolute path missing @ prefix: {m.group(1)[:80]}")
        for m in re.finditer(r"(?m)(?<!@)(?<![\w./\\-])(C:\\Users\\ynotf\\[^\s`\"')\]]+)(?:\.(?:md|yaml|yml|json|py))", filtered_text):
            errors.append(f"{path.name}: user-profile path missing @ prefix: {m.group(1)[:80]}")

    # 10. C-drive user path omits C:\Users\ynotf
    if re.search(r"C:\\Users\\\.\.\.", content):
        errors.append("MASTER_CONFIG: contains shortened C:\\Users\\... form")

    # 11. Global rules omit the memory lifecycle
    policy_path = REPO_ROOT / "contracts" / "global-agent-policy.yaml"
    if policy_path.exists():
        policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        rule_ids = {r.get("id") for r in policy.get("mandatory_rules", [])}
        required = {"memory-lifecycle-continuous-capture", "durable-memory-context", "recovery-first"}
        missing = required - rule_ids
        if missing:
            errors.append(f"GLOBAL_POLICY: missing memory lifecycle rule(s): {missing}")

    # 12. Configuration presence is not reported as native validation
    if "Do not claim completion from config files alone" not in content:
        errors.append("MASTER_CONFIG: missing 'configuration presence is not native validation' statement")
    if "Do not mark live_validated from config inspection alone" not in content:
        errors.append("MASTER_CONFIG: missing 'do not mark live_validated from config inspection' statement")

    # 13. Mutable runtime facts not presented as permanent architecture
    if re.search(r"HEAD\s+[a-f0-9]{7,}", content):
        errors.append("MASTER_CONFIG: mutable HEAD hash presented as permanent authority")
    if re.search(r"(?i)\b(?:1[0-9]|2[0-9]|3[0-9])\s+tools\b", content):
        errors.append("MASTER_CONFIG: mutable runtime tool count presented as permanent architecture")
    if re.search(r"(?i)\b(?:1[0-9]|2[0-9])\s+enabled\s+upstream\b", content):
        errors.append("MASTER_CONFIG: mutable upstream enabled count presented as permanent architecture")

    # 14. Secrets or resolved bearer values in Git
    for path in (master, install_prompt):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for needle in ("sk-bf-ag", "sk-proj-", "sk-ant-", "sk-or-v1-", "ghp_", "Bearer sk-"):
            if needle in text:
                errors.append(f"{path.name}: possible resolved secret literal ({needle})")

    # 15. Follow-on Cursor task needs continuation prompt
    if "CURSOR CONTINUATION PROMPT" not in content:
        errors.append("MASTER_CONFIG: missing CURSOR CONTINUATION PROMPT section")

    # 16. Supported clients list must be current and not generic
    required_client_inventory = (
        "Cursor, Codex, Devin, Eigent, Zed, Zcode, MiniMax Code/Mavis, Reasonix, OpenCode, "
        "Open Design, AutoGPT, Agent Orchestrator, Cherry Studio, LobeHub, OpenHands, "
        "Antigravity, Open Interpreter, OpenClaw/ClawX, Claude Code, Claude Desktop, "
        "MiniMax Agent Classic, Zoo-Code/Roo-Code"
    )
    if required_client_inventory not in content:
        errors.append("MASTER_CONFIG: supported client list missing or stale")

    # 17. Cherry Studio and MiniMax Classic must be present in the matrix
    if matrix_path.exists():
        managed = matrix.get("managed_ides", {})
        if "cherry-studio" not in managed:
            errors.append("MATRIX: cherry-studio missing from managed_ides")
        if "minimax-classic" not in managed:
            errors.append("MATRIX: minimax-classic missing from managed_ides")
        if list(managed)[:2] != ["zed", "eigent"]:
            errors.append("MATRIX: Zed and Eigent must be the first managed_ides")
        if "mavis" in managed:
            errors.append("MATRIX: mavis still listed as a managed IDE")

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
    errors.extend(task2_contract_profile_checks(gateway))
    errors.extend(strict_master_config_audit(registry))
    errors.extend(authority_lock_checks())
    errors.extend(output_schema_checks())
    errors.extend(tracked_secret_checks())
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
    print("OK: master-config strict audit passed")
    print("OK: authority-lock and foreign-boundary manifests valid")
    print("OK: MCP outputSchema coverage — MissingOutputSchema=0 (contract gate)")
    print("OK: tracked source secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
