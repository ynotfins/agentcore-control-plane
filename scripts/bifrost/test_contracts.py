#!/usr/bin/env python3
"""Deterministic test harness for the authority-reconciliation contracts and renderers.

Standalone (no pytest). Exit 0 = all checks pass, exit 1 = failures listed.

Run: python scripts/bifrost/test_contracts.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
FAILURES: list[str] = []
PASSES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        PASSES.append(name)
    else:
        FAILURES.append(f"{name}{': ' + detail if detail else ''}")


def read(rel: str) -> str:
    path = REPO / rel
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def main() -> int:
    # --- contracts parse and schema-validate ---
    import jsonschema

    for contract_rel, schema_rel in [
        ("contracts/project-execution-policy.json", "contracts/schemas/project-execution-policy.schema.json"),
        ("contracts/project-tool-lifecycle.json", "contracts/schemas/project-tool-lifecycle.schema.json"),
        ("contracts/model-context-profiles.json", "contracts/schemas/model-context-profiles.schema.json"),
    ]:
        try:
            instance = json.loads(read(contract_rel))
            schema = json.loads(read(schema_rel))
            jsonschema.Draft202012Validator(schema).validate(instance)
            check(f"schema:{contract_rel}", True)
        except Exception as exc:  # noqa: BLE001 - report any validation failure
            check(f"schema:{contract_rel}", False, str(exc)[:200])

    try:
        policy = yaml.safe_load(read("contracts/global-agent-policy.yaml"))
        schema = json.loads(read("contracts/schemas/global-agent-policy.schema.json"))
        jsonschema.Draft202012Validator(schema).validate(policy)
        check("schema:contracts/global-agent-policy.yaml", True)
    except Exception as exc:  # noqa: BLE001
        policy = None
        check("schema:contracts/global-agent-policy.yaml", False, str(exc)[:200])

    try:
        enrollment = json.loads(read("contracts/agentcore-project-enrollment.json"))
        enrolled_paths = [
            path
            for project in enrollment.get("projects", [])
            for path in project.get("paths", [])
        ]
        check(
            "project-enrollment:default deny with explicit paths",
            enrollment.get("schema_version") == 1
            and enrollment.get("default_policy") == "deny"
            and bool(enrolled_paths)
            and len(enrolled_paths) == len(set(path.lower() for path in enrolled_paths)),
        )
    except Exception as exc:  # noqa: BLE001
        check("project-enrollment:default deny with explicit paths", False, str(exc)[:200])

    try:
        model_profiles = json.loads(read("contracts/model-context-profiles.json"))
        by_name = {row["profile_name"]: row for row in model_profiles["profiles"]}
        check(
            "context-profile:one-million preserved",
            by_name["one-million-context"]["hard_context_limit"] == 1_000_000,
        )
        check(
            "context-profile:future above million",
            by_name["future-above-million"]["hard_context_limit"] > 1_000_000,
        )
        check(
            "context-profile:small is not default",
            model_profiles["default_profile"] not in {"acceptance-small", "legacy-4096"},
        )
    except Exception as exc:  # noqa: BLE001
        check("context-profile:semantic checks", False, str(exc)[:200])

    # --- agent-policy docs exist ---
    for rel in [
        "docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md",
        "docs/agent-policy/MILESTONE_EXECUTION_STANDARD.md",
        "docs/agent-policy/CHECKLIST_STANDARD.md",
        "docs/agent-policy/TOOL_LIFECYCLE_POLICY.md",
        "docs/agent-policy/DOCUMENTATION_READ_ORDER.md",
    ]:
        check(f"policy-doc:{rel}", (REPO / rel).exists())

    # --- governance templates exist ---
    for rel in [
        "templates/project-governance/.agentcore/PROJECT_CHARTER.md",
        "templates/project-governance/.agentcore/MILESTONES.md",
        "templates/project-governance/.agentcore/TOOL_MANIFEST.yaml",
        "templates/project-governance/.agentcore/PROJECT_STATE.json",
        "templates/project-governance/.agentcore/RISK_REGISTER.md",
        "templates/project-governance/.agentcore/ACCEPTANCE_TESTS.md",
        "templates/project-governance/.agentcore/milestones/M0-bootstrap.md",
        "templates/project-governance/.agentcore/checklists/state.json",
    ]:
        check(f"template:{rel}", (REPO / rel).exists())

    # Template manifest parses as YAML and template state parses as JSON.
    try:
        manifest = yaml.safe_load(read("templates/project-governance/.agentcore/TOOL_MANIFEST.yaml"))
        required = {"project_id", "base_profile", "core_active", "forbidden", "last_audit", "policy_revision"}
        check("template:TOOL_MANIFEST fields", required.issubset(manifest.keys()),
              f"missing {required - set(manifest.keys())}")
    except Exception as exc:  # noqa: BLE001
        check("template:TOOL_MANIFEST fields", False, str(exc)[:200])
    try:
        state = json.loads(read("templates/project-governance/.agentcore/checklists/state.json"))
        check("template:checklist state items", isinstance(state.get("items"), list) and len(state["items"]) >= 1)
    except Exception as exc:  # noqa: BLE001
        check("template:checklist state items", False, str(exc)[:200])

    # --- BLUEPRINT.md present and referenced ---
    blueprint = read("BLUEPRINT.md")
    check("blueprint:exists", bool(blueprint))
    check("blueprint:locked-milestones", "## M0" in blueprint and "## M8" in blueprint)
    check("blueprint:lossless", "Lossless" in blueprint or "lossless" in blueprint)
    check("blueprint:no-mem0", "Mem0 is not installed" in blueprint or "Do not install Mem0" in blueprint)
    doc_auth = read("DOC_AUTHORITY.md")
    stable_chunk = doc_auth.split("## Authoritative")[1].split("## Current-state")[0] if "## Authoritative" in doc_auth and "## Current-state" in doc_auth else ""
    check("blueprint:classified-current", "BLUEPRINT.md" in stable_chunk)

    # --- memory-platform authority ---
    plan = read("docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md")
    check("plan:exists", bool(plan))
    for milestone in [f"M{i}" for i in range(9)]:
        check(f"plan:milestone {milestone}", f"## {milestone} — " in plan, "locked milestone heading missing")
    check("plan:lossless definition", "Lossless requirement" in plan)
    check("plan:mem0 rejected", "Mem0 is rejected" in plan)
    check("plan:tool lifecycle in M6", "M6" in plan and "Progressive Tool Disclosure" in plan)

    # --- ide-profiles ---
    profiles_root = REPO / "ide-profiles"
    check("ide:matrix", (profiles_root / "IDE_CAPABILITY_MATRIX.yaml").exists())
    profile_dirs = [
        p for p in profiles_root.iterdir()
        if p.is_dir() and (p / "IDE_PROFILE.yaml").is_file()
    ]
    check(
        "ide:priority clients + cursor+codex present",
        {"zed", "eigent", "cursor", "codex"}.issubset({p.name for p in profile_dirs}),
    )
    matrix = yaml.safe_load(read("ide-profiles/IDE_CAPABILITY_MATRIX.yaml"))
    check(
        "ide:priority ordering truthful",
        list((matrix.get("managed_ides") or {}).keys())[:2] == ["zed", "eigent"]
        and matrix["managed_ides"]["zed"]["m8_enrollment"] == "awaiting_operator_import"
        and matrix["managed_ides"]["eigent"]["m8_enrollment"] == "awaiting_operator_import",
    )
    zed_renderer = json.loads(read("renderers/gateway-clients/zed.json"))
    eigent_renderer = json.loads(read("renderers/gateway-clients/eigent.json"))
    antigravity_renderer = json.loads(read("renderers/gateway-clients/antigravity.json"))
    check(
        "ide:zed renderer schema",
        list(zed_renderer.get("context_servers", {})) == ["agentcore-gateway"]
        and zed_renderer["context_servers"]["agentcore-gateway"].get("url")
        == "http://127.0.0.1:8080/mcp",
    )
    check(
        "ide:eigent renderer schema",
        list(eigent_renderer.get("mcpServers", {})) == ["agentcore-gateway"]
        and eigent_renderer["mcpServers"]["agentcore-gateway"].get("url")
        == "http://127.0.0.1:8080/mcp",
    )
    antigravity_gateway = antigravity_renderer["mcpServers"]["agentcore-gateway"]
    check(
        "ide:antigravity renderer schema",
        list(antigravity_renderer.get("mcpServers", {})) == ["agentcore-gateway"]
        and antigravity_gateway.get("serverUrl") == "http://127.0.0.1:8080/mcp"
        and not any(key in antigravity_gateway for key in ("type", "url", "httpUrl", "timeout")),
    )
    check(
        "ide:antigravity renderer path",
        "C:\\Users\\ynotf\\AppData\\Roaming\\Antigravity IDE\\User\\mcp.json"
        in antigravity_renderer.get("_agentcore", {}).get("paths", []),
    )
    for client, renderer in (("zed", zed_renderer), ("eigent", eigent_renderer)):
        renderer_text = json.dumps(renderer)
        check(
            f"ide:{client} renderer symbolic secret only",
            "${env:BIFROST_MCP_VIRTUAL_KEY}" in renderer_text
            and re.search(r"Bearer\s+(?!\$\{env:)[A-Za-z0-9._~+/=-]{20,}", renderer_text) is None,
        )
    antigravity_renderer_text = json.dumps(antigravity_renderer)
    check(
        "ide:antigravity renderer symbolic secret only",
        "${BIFROST_MCP_VIRTUAL_KEY}" in antigravity_renderer_text
        and re.search(r"Bearer\s+(?!\$\{BIFROST_MCP_VIRTUAL_KEY\})[A-Za-z0-9._~+/=-]{20,}", antigravity_renderer_text) is None,
    )
    valid_modes = {"direct_write", "generated_prompt", "manual_import", "unsupported", "unverified"}
    for profile_dir in sorted(profile_dirs):
        profile_rel = f"ide-profiles/{profile_dir.name}"
        try:
            profile = yaml.safe_load((profile_dir / "IDE_PROFILE.yaml").read_text(encoding="utf-8"))
        except FileNotFoundError:
            check(f"ide:{profile_rel}/IDE_PROFILE.yaml", False, "missing")
            continue
        editability = profile.get("editability") or {}
        check(
            f"ide:{profile_rel} editability declared",
            bool(editability) and all(v in valid_modes for v in editability.values()),
            f"modes={editability}",
        )
        for derived in ("GLOBAL_RULES.md", "INSTALL_OR_UPDATE.md", "VALIDATION.md"):
            check(f"ide:{profile_rel}/{derived}", (profile_dir / derived).exists())
        mcp_templates = list(profile_dir.glob("MCP_CONFIG_TEMPLATE.*"))
        check(f"ide:{profile_rel}/MCP_CONFIG_TEMPLATE", len(mcp_templates) == 1)
        # No resolved secrets in generated artifacts.
        for artifact in [*mcp_templates, *(profile_dir / name for name in ("GLOBAL_RULES.md",))]:
            body = artifact.read_text(encoding="utf-8", errors="replace")
            secret_hit = re.search(r"sk-(proj|ant|or-v1)-[A-Za-z0-9]|ghp_[A-Za-z0-9]{20}|AIza[A-Za-z0-9_\-]{30}", body)
            check(f"ide:no-secrets:{profile_rel}/{artifact.name}", secret_hit is None)

    # Rendered rule files are current (deterministic renderer check).
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "render_ide_rules.py"), "--check"],
        capture_output=True, text=True, cwd=REPO,
    )
    check("ide:renderings current", result.returncode == 0, result.stdout.strip()[:200])

    # IDE-local enrollment prompts must stay client-scoped (no multi-IDE live edits).
    scope_result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "bifrost" / "validate_ide_enrollment_scope.py")],
        capture_output=True, text=True, cwd=REPO,
    )
    check(
        "ide:client-local enrollment scope",
        scope_result.returncode == 0,
        (scope_result.stdout or scope_result.stderr).strip()[:300],
    )

    # Per-dimension client-status schema and semantic/temporal invariants.
    status_result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "bifrost" / "validate_client_status.py")],
        capture_output=True, text=True, cwd=REPO,
    )
    check(
        "ide:client-status semantic/temporal invariants",
        status_result.returncode == 0,
        (status_result.stdout or status_result.stderr).strip()[:300],
    )

    # Every mandatory rule id appears in every rendered GLOBAL_RULES.md (no silent omission).
    if policy:
        rule_titles = [rule["title"] for rule in policy["mandatory_rules"]]
        for profile_dir in sorted(profile_dirs):
            rendered = read(f"ide-profiles/{profile_dir.name}/GLOBAL_RULES.md")
            missing = [t for t in rule_titles if f"**{t}.**" not in rendered]
            check(f"ide:parity:{profile_dir.name}", not missing, f"missing rules: {missing}")

    # --- registry wildcard transitional note ---
    registry = json.loads(read("contracts/bifrost-upstream-mcp-registry.json"))
    wildcards = [k for k, s in registry["servers"].items() if s.get("permitted_tools") == ["*"]]
    check("registry:wildcards documented", not wildcards or "tool_lifecycle_note" in registry,
          f"undocumented wildcards: {wildcards}")

    nia = registry["servers"].get("nia") or {}
    nia_allowed = {
        "search",
        "nia_read",
        "nia_grep",
        "nia_explore",
        "nia_package_search_hybrid",
        "nia_vault_list",
        "nia_vault_search",
    }
    nia_denied_required = {
        "index",
        "context",
        "nia_research",
        "nia_advisor",
        "tracer",
        "manage_resource",
        "auto_subscribe_dependencies",
        "nia_write",
        "nia_rm",
        "nia_mv",
        "nia_mkdir",
        "nia_vault_create",
        "nia_vault_run",
    }
    profile_servers = registry.get("capability_profiles") or {}
    nia_profiles = sorted(
        profile_id
        for profile_id, profile in profile_servers.items()
        if "nia" in (profile.get("allowed_server_ids") or [])
    )
    check(
        "registry:nia endpoint and env auth",
        nia.get("connection_type") == "http"
        and nia.get("executable_or_url") == "https://apigcp.trynia.ai/mcp"
        and nia.get("auth_type") == "headers"
        and nia.get("headers", {}).get("Authorization") == "Bearer env.NIA_API_KEY"
        and nia.get("env_var_names") == ["NIA_API_KEY"],
        f"nia={nia}",
    )
    check(
        "registry:nia retrieval-only tool surface",
        set(nia.get("permitted_tools") or []) == nia_allowed
        and nia_denied_required.issubset(set(nia.get("denied_tools") or []))
        and nia.get("write_classification") == "read_only",
        f"permitted={nia.get('permitted_tools')} denied={nia.get('denied_tools')}",
    )
    check(
        "registry:nia all-IDE profiles only",
        nia_profiles == ["builder", "docs-knowledge", "operator"]
        and sorted(nia.get("capability_profiles") or []) == nia_profiles,
        f"nia_profiles={nia_profiles}",
    )
    check(
        "registry:zoo-code remains non-upstream",
        not any(server_id in registry["servers"] for server_id in ("zoo-code", "zoo_code", "zoocode")),
    )

    # Shared STDIO clients receive no trustworthy caller/project identity. Project-bound
    # upstreams therefore stay dormant until an explicit per-session router exists.
    implicit_project_servers = {"serena", "depwire", "tentra", "filesystem", "context-fabric"}
    unsafe_enabled = sorted(
        server_id for server_id in implicit_project_servers
        if registry["servers"][server_id].get("enabled")
        or registry["servers"][server_id].get("capability_profiles")
    )
    check(
        "registry:implicit project upstreams dormant",
        not unsafe_enabled,
        f"unsafe enabled/profiled servers: {unsafe_enabled}",
    )
    router_profiles = sorted(
        profile_id for profile_id, profile in registry["capability_profiles"].items()
        if "agentcore-project-router" in (profile.get("allowed_server_ids") or [])
    )
    check(
        "registry:global project mutation operator-only",
        router_profiles == ["operator"],
        f"router profiles: {router_profiles}",
    )

    source_renderer_paths = [
        REPO / "renderers" / "bifrost" / "config.json",
        REPO / "renderers" / "bifrost" / "config.sanitized.json",
    ]
    oauth_id_pattern = re.compile(r'"oauth_config_id"\s*:\s*"[A-Za-z0-9_-]{8,}"')
    oauth_leaks = [
        str(path.relative_to(REPO)) for path in source_renderer_paths
        if oauth_id_pattern.search(path.read_text(encoding="utf-8", errors="replace"))
    ]
    check(
        "renderer:no runtime OAuth metadata in Git",
        not oauth_leaks,
        f"oauth_config_id values: {oauth_leaks}",
    )

    recovery_runbook = read("docs/operations/AUTOMATIC_NEW_CHAT_RECOVERY.md")
    check(
        "runbook:Cursor Stage B current",
        "HARD GATE PENDING" not in recovery_runbook
        and "Not registered in Stage A" not in recovery_runbook,
    )
    memory_plan = read("docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md")
    check("memory-plan:no AgentCore H spool", "on H: spool" not in memory_plan)

    cursor_runtime_sources = [
        "scripts/agentcore_cursor/bootstrap.py",
        "scripts/agentcore_cursor/hook_dispatcher.py",
        "scripts/agentcore_cursor/spool.py",
        "scripts/agentcore_cursor/hooks.py",
    ]
    stale_cursor_runtime_paths = [
        path for path in cursor_runtime_sources if r"H:\AgentRuntime" in read(path)
    ]
    check(
        "cursor-runtime:no stale H AgentRuntime defaults",
        not stale_cursor_runtime_paths,
        f"stale runtime paths: {stale_cursor_runtime_paths}",
    )
    cursor_bootstrap = read("scripts/agentcore_cursor/bootstrap.py")
    check(
        "cursor-runtime:bootstrap has no machine-global router dependency",
        "agentcore_project_router-" not in cursor_bootstrap,
    )
    global_agent_policy = read("contracts/global-agent-policy.yaml")
    stale_shared_project_policy = [
        phrase for phrase in (
            "activate the project through agentcore-project-router",
            "Use Serena through agentcore-gateway",
        )
        if phrase in global_agent_policy
    ]
    check(
        "policy:no shared implicit-project tool mandate",
        not stale_shared_project_policy,
        f"stale policy phrases: {stale_shared_project_policy}",
    )
    bootstrap_policy = read("docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md")
    check(
        "policy:new-project bootstrap uses explicit local project identity",
        "Activate/register" not in bootstrap_policy
        and "Project-scoped filesystem operations" not in bootstrap_policy,
    )

    for name, command in (
        (
            "project-boundary:cursor bootstrap",
            [sys.executable, "-m", "unittest", "scripts.agentcore_cursor.tests.test_bootstrap_project_boundary"],
        ),
        (
            "project-boundary:memory facade",
            [sys.executable, "-m", "pytest", "scripts/agentcore_memory/tests/test_project_boundary.py", "-q"],
        ),
    ):
        boundary_result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=REPO,
        )
        check(
            name,
            boundary_result.returncode == 0,
            (boundary_result.stdout or boundary_result.stderr).strip()[:400],
        )

    # --- MCP outputSchema coverage (MissingOutputSchema must be zero) ---
    # Full gate including the generated-artifact drift check: a contract or registry
    # change that has not been re-rendered leaves live tools/list without outputSchema.
    output_schema_result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "bifrost" / "validate_output_schemas.py")],
        capture_output=True, text=True, cwd=REPO,
    )
    check(
        "mcp:outputSchema coverage (MissingOutputSchema=0)",
        output_schema_result.returncode == 0,
        (output_schema_result.stdout or output_schema_result.stderr).strip()[:400],
    )

    # Normalizer self-proof: emitted envelopes validate against emitted schemas.
    adapter_selftest = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "bifrost" / "mcp_output_schema_adapter.py"),
            "--self-test",
        ],
        capture_output=True, text=True, cwd=REPO,
    )
    check(
        "mcp:output normalizer self-test",
        adapter_selftest.returncode == 0,
        (adapter_selftest.stdout or adapter_selftest.stderr).strip()[:400],
    )

    # Registry wiring must reference the normalizer that the renderer injects.
    adapter_block = registry.get("output_schema_adapter") or {}
    check(
        "mcp:output adapter wired in registry",
        bool(adapter_block.get("enabled"))
        and (REPO / str(adapter_block.get("script", "")).replace("\\", "/")).exists()
        and (REPO / str(adapter_block.get("contract", "")).replace("\\", "/")).exists(),
        f"output_schema_adapter={adapter_block}",
    )

    # --- CONTEXT_BLOCK repaired ---
    context_block = read("CONTEXT_BLOCK.md")
    check("context-block:no stray fence", not context_block.lstrip().startswith("```"))
    check("context-block:bifrost composition", "agentcore-gateway" in context_block)
    check("context-block:never format H:", "never be formatted" in context_block or "never format" in context_block.lower())

    # --- report ---
    print(f"PASS {len(PASSES)} checks")
    if FAILURES:
        print(f"FAIL {len(FAILURES)} checks:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("OK: all contract/renderer tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
