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
    profile_dirs = [p for p in profiles_root.iterdir() if p.is_dir()]
    check("ide:cursor+codex present", {"cursor", "codex"}.issubset({p.name for p in profile_dirs}))
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
