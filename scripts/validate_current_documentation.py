"""Validate the small documentation surface allowed to claim current readiness."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote


CURRENT_DOCS = (
    "DOC_AUTHORITY.md",
    "CONTEXT_BLOCK.md",
    "MASTER_CONFIG_AND_PROMPT.md",
    "MILESTONES.md",
    "AGENTS.md",
    "docs/agent-policy/DOCUMENTATION_READ_ORDER.md",
    "docs/current/CURRENT_PROJECT_RECONSTRUCTION.md",
    "docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md",
    "docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md",
    "docs/operations/AUTOMATIC_NEW_CHAT_RECOVERY.md",
    "docs/operations/AGENTCORE_ALIGNMENT_SKILL.md",
    "audits/CONTEXT_ENGINE_0_2_4_AND_ALIGNMENT_ACCEPTANCE_2026-08-04.md",
    "scripts/agentcore_workflow/studio/README.md",
)

CLASSIFIED_EVIDENCE = {
    "docs/operations/OPENROUTER_PROVIDER_INTEGRATIONS.md": "HISTORICAL PHASE 1 EVIDENCE",
    "docs/handoffs/AGENTCORE_SWARM_DUAL_ECOSYSTEM_HANDOFF_2026-07-25.md": "POINT-IN-TIME HANDOFF",
    "docs/handoffs/AGENTCORE_AUTONOMOUS_WORKFLOW_STUDIO_HANDOFF_2026-07-17.md": "POINT-IN-TIME HANDOFF",
    "docs/SYSTEM_HANDOVER_BLUEPRINT.md": "SUPERSEDED HANDOVER",
    "docs/current/CHATGPT_PROJECT_SOURCE_MANIFEST.md": "RETIRED SOURCE EXPORT",
}

OPERATOR_RUNBOOKS = (
    "docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md",
    "docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md",
    "docs/operations/AUTOMATIC_NEW_CHAT_RECOVERY.md",
    "scripts/agentcore_workflow/studio/README.md",
)

REPO_PYTHON = r"D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe"
SCRIPTS_CWD = r"D:\github\agentcore-control-plane\scripts"
REPO_ROOT_CWD = r"D:\github\agentcore-control-plane"
SYSTEM_PYTHON = r"C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe"
GATEWAY_GUIDE = "GATEWAY_AND_BIFROST_DEVELOPER_GUIDE.md"
CLIENT_CONTRACT = "contracts/agentcore-gateway-client.json"
CLIENT_MATRIX = "ide-profiles/IDE_CAPABILITY_MATRIX.yaml"
OPEN_INTERPRETER_PROFILE = "ide-profiles/open-interpreter/IDE_PROFILE.yaml"
UNIFIED_GATEWAY_SETUP = "docs/bifrost/UNIFIED_GATEWAY_SETUP.md"
CAPABILITY_PROFILES_DOC = "docs/bifrost/CAPABILITY_PROFILES.md"


def _repository_relative_markdown_targets(text: str) -> list[str]:
    """Return local targets from inline and reference-style Markdown links."""
    targets = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text)
    targets.extend(
        match.group(1)
        for match in re.finditer(r"(?m)^\s*\[[^\]]+\]:\s*(\S+)", text)
    )
    local: list[str] = []
    for raw_target in targets:
        target = raw_target.strip()
        if target.startswith("<") and ">" in target:
            target = target[1 : target.index(">")]
        else:
            target = target.split(maxsplit=1)[0]
        target = unquote(target).split("#", 1)[0]
        if not target or target.startswith(("#", "/", "\\")):
            continue
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
            continue
        local.append(target.replace("/", "\\"))
    return local


def _yaml_mapping_block(text: str, key: str, indent: int) -> str:
    """Return one indentation-delimited YAML mapping body without a YAML dependency."""
    prefix = " " * indent
    match = re.search(
        rf"(?ms)^{re.escape(prefix + key)}:\s*$\n"
        rf"(?P<body>.*?)(?=^{re.escape(prefix)}\S[^\n]*:\s*(?:#.*)?$|\Z)",
        text,
    )
    return match.group("body") if match else ""


def _markdown_table_row(text: str, label: str) -> str:
    match = re.search(rf"(?m)^\| {re.escape(label)} \|.*$", text)
    return match.group(0) if match else ""


def validate_client_authority_alignment(root: Path) -> list[str]:
    """Keep the reusable client-status authority aligned with contracts and profiles."""
    errors: list[str] = []
    paths = {
        "contract": root / CLIENT_CONTRACT,
        "matrix": root / CLIENT_MATRIX,
        "master": root / "MASTER_CONFIG_AND_PROMPT.md",
        "profile": root / OPEN_INTERPRETER_PROFILE,
        "setup": root / UNIFIED_GATEWAY_SETUP,
        "authority": root / "DOC_AUTHORITY.md",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return [f"client authority alignment missing {name}: {paths[name].relative_to(root)}" for name in missing]

    try:
        contract = json.loads(paths["contract"].read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"invalid gateway client contract: {exc}"]
    hints = contract.get("client_render_hints") or {}
    master = paths["master"].read_text(encoding="utf-8")
    matrix = paths["matrix"].read_text(encoding="utf-8")
    profile = paths["profile"].read_text(encoding="utf-8")
    setup = paths["setup"].read_text(encoding="utf-8")
    authority = paths["authority"].read_text(encoding="utf-8")

    contract_expectations = {
        "zed": (False, "unverified", None),
        "eigent": (False, "unverified", None),
        "zcode": (True, "process_attested_proxy", "http://127.0.0.1:18082/mcp"),
        "opencode": (False, "unverified", None),
        "cherry-studio": (False, "unverified", None),
        "antigravity": (True, "process_attested_proxy", "http://127.0.0.1:18082/mcp"),
        "open-interpreter": (True, "process_attested_proxy", "http://127.0.0.1:18082/mcp"),
        "openclaw": (True, None, None),
        "clawx": (False, None, None),
        "claude-desktop": (False, "unverified", None),
        "minimax-classic": (False, "unverified", None),
    }
    for client, (enabled, auth_mode, gateway_url) in contract_expectations.items():
        hint = hints.get(client)
        if not isinstance(hint, dict):
            errors.append(f"gateway client contract missing hint: {client}")
            continue
        if hint.get("enabled") is not enabled:
            errors.append(f"gateway client contract enabled drift for {client}: expected {enabled}")
        if auth_mode is not None and hint.get("gateway_auth_mode") != auth_mode:
            errors.append(f"gateway client contract auth-mode drift for {client}: expected {auth_mode}")
        if gateway_url is not None and hint.get("gateway_url") != gateway_url:
            errors.append(f"gateway client contract route drift for {client}: expected {gateway_url}")

    master_rows = {
        "Eigent": ("unsupported", "disabled", "unverified", "no approved secure credential route"),
        "Zed": ("unsupported", "disabled", "unverified", "no approved secure credential route"),
        "ZCode": ("enabled", "18082", "process-attested", "distinct from Zoo-Code"),
        "OpenCode": ("unsupported", "disabled", "unverified", "legacy drift"),
        "Cherry Studio": ("unsupported", "disabled", "unsupported_with_reason", "historical evidence"),
        "Antigravity": ("enabled", "18082", "process-attested", "validated 2026-09-08"),
        "Open Interpreter **CLI**": ("enabled", "8080", "bearer_token_env_var", "no credential is stored"),
        "Open Interpreter **GUI** (`Interpreter.exe`)": ("enabled", "18082", "process-attested", "fresh in-app acceptance pending"),
        "OpenClaw": ("enabled", "dedicated direct", "BIFROST_MCP_VK_OPENCLAW", "live activation and lifecycle remain unverified"),
        "ClawX": ("unverified", "no ClawX-native MCP configuration"),
        "Claude Desktop": ("unsupported", "disabled", "unverified", "historical drift"),
        "MiniMax Agent Classic": ("unsupported", "disabled", "unverified", "Do not create a cloud custom-MCP entry"),
    }
    for label, required_terms in master_rows.items():
        row = _markdown_table_row(master, label)
        if not row:
            errors.append(f"MASTER client status row missing: {label}")
            continue
        for term in required_terms:
            if term.casefold() not in row.casefold():
                errors.append(f"MASTER client status row drift for {label}: missing {term}")

    matrix_expectations = {
        "zed": ("m8_enrollment: unsupported_with_reason",),
        "eigent": ("m8_enrollment: unsupported_with_reason",),
        "zcode": ("certification: configured_restart_required", "gateway_url: http://127.0.0.1:18082/mcp", "gateway_auth_mode: process_attested_proxy"),
        "opencode": ("certification: unsupported_with_reason",),
        "cherry-studio": ("m8_enrollment: unsupported_with_reason",),
        "antigravity": ("last_validated: '2026-09-08'", "gateway_url: http://127.0.0.1:18082/mcp", "gateway_auth_mode: process_attested_proxy"),
        "open-interpreter": ("last_validated: '2026-09-08'", "gateway_url: http://127.0.0.1:8080/mcp", "gateway_auth_mode: bearer_env", "gui_gateway_url: http://127.0.0.1:18082/mcp", "gui_gateway_auth_mode: process_attested_proxy"),
        "openclaw": ("certification: configured_restart_required", "gateway_url: http://127.0.0.1:8080/mcp", "gateway_auth_mode: dedicated_bearer_env", "capability_profile: openclaw"),
        "clawx": ("certification: unverified",),
        "claude-desktop": ("m8_enrollment: unsupported_with_reason",),
        "minimax-classic": ("m8_enrollment: unsupported_with_reason",),
    }
    for client, required_terms in matrix_expectations.items():
        block = _yaml_mapping_block(matrix, client, 2)
        if not block:
            errors.append(f"client capability matrix row missing: {client}")
            continue
        for term in required_terms:
            if term not in block:
                errors.append(f"client capability matrix drift for {client}: missing {term}")

    for required in (
        "display_name: Open Interpreter (CLI)",
        "gui_display_name: Open Interpreter desktop GUI",
        r"live_mcp_config_target: C:\Users\ynotf\.openinterpreter\config.toml",
        r"live_gui_mcp_config_target: C:\Users\ynotf\AppData\Roaming\interpreter\config.json",
        "gateway_url: http://127.0.0.1:8080/mcp",
        "gateway_auth_mode: bearer_env",
        "classification: superseded_historical_evidence",
        "GUI uses process-attested :18082 with no stored bearer",
    ):
        if required not in profile:
            errors.append(f"Open Interpreter profile drift: missing {required}")

    if "If you are Open Interpreter GUI" in master or "GUI has no MCP schema" in master:
        errors.append("MASTER retains the superseded Open Interpreter GUI hard-stop")
    for required in (
        "If you are Open Interpreter, identify whether you are the CLI or the desktop GUI",
        "gateway_auth_mode` is `unverified`",
        "Open Interpreter GUI uses process-attested `:18082`",
    ):
        if required not in master:
            errors.append(f"MASTER reusable prompt missing contract-selected route guidance: {required}")

    if "CONTEXT_BLOCK.md` §0a" in setup:
        errors.append("unified gateway setup points to nonexistent CONTEXT_BLOCK section 0a")
    if 'CONTEXT_BLOCK.md` §0 ("Current posture")' not in setup:
        errors.append("unified gateway setup omits current CONTEXT_BLOCK section 0 pointer")
    if re.search(r"(?m)^\s*python\s+scripts/bifrost/render_bifrost_config\.py", setup):
        errors.append("unified gateway setup teaches bare Python for Bifrost rendering")
    if "### D. Allow all tools on one client" in setup:
        errors.append("unified gateway setup teaches active wildcard tool exposure")
    for required in (
        r"scripts\.venv\Scripts\python.exe scripts/bifrost/render_bifrost_config.py",
        "Require a named inventory before activation",
    ):
        if required not in setup:
            errors.append(f"unified gateway setup missing safe admission guidance: {required}")
    if not re.search(
        r"Existing wildcard placeholders are allowed\s+only\s+on disabled or dormant entries",
        setup,
    ):
        errors.append(
            "unified gateway setup missing safe admission guidance: disabled/dormant wildcard boundary"
        )

    cherry_line = next((line for line in authority.splitlines() if line.startswith("- Cherry Studio's July 2026")), "")
    for required in ("historical credential-bearing evidence", "disabled / `unverified`", "do not enroll, re-enroll, or materialize"):
        if required not in cherry_line:
            errors.append(f"DOC_AUTHORITY Cherry classification drift: missing {required}")
    return errors


def validate_gateway_guide(root: Path) -> list[str]:
    """Validate the root gateway guide without treating it as architecture authority."""
    errors: list[str] = []
    path = root / GATEWAY_GUIDE
    if not path.is_file():
        return [f"missing gateway developer guide: {GATEWAY_GUIDE}"]

    text = path.read_text(encoding="utf-8")
    folded = text.casefold()
    if "subordinate" not in folded or "architecture authority" not in folded:
        errors.append("gateway guide does not declare its subordinate/non-authority role")

    for required in (
        "PROJECT_ANCHOR.md",
        "DOC_AUTHORITY.md",
        "BLUEPRINT.md",
        "CONTEXT_BLOCK.md",
        "contracts/bifrost-upstream-mcp-registry.json",
        "contracts/agentcore-gateway-client.json",
        "contracts/mcp-tool-output-schemas.json",
    ):
        if required.casefold() not in folded:
            errors.append(f"gateway guide missing authority or contract reference: {required}")

    if not ("mcp plane" in folded and "inference" in folded and re.search(r"does not prove|separate", folded)):
        errors.append("gateway guide does not distinguish MCP routing from inference routing")

    for required in (
        "http://127.0.0.1:8080/mcp",
        "http://127.0.0.1:18082/mcp",
        "gateway_url",
        "gateway_auth_mode",
        "process-attested",
    ):
        if required.casefold() not in folded:
            errors.append(f"gateway guide missing client-route contract term: {required}")

    sequence = ("listToolFiles", "readToolFile", "getToolDocs", "executeToolCode")
    offsets = [text.find(term) for term in sequence]
    if any(offset < 0 for offset in offsets) or offsets != sorted(offsets):
        errors.append("gateway guide missing ordered Code Mode sequence: " + " -> ".join(sequence))

    for label, required in {
        "project enrollment": "contracts/agentcore-project-enrollment.json",
        "memory facade": "agentcore-memory",
        "canonical memory": "PostgreSQL",
        "neutral semantic projection": "Recall",
        "Swarm separation": "SwarmClaw",
        "ZCode distinction": "ZCode",
        "Zoo-Code distinction": "Zoo-Code",
    }.items():
        if required.casefold() not in folded:
            errors.append(f"gateway guide missing {label}: {required}")
    if not re.search(r"ZCode.{0,100}(?:different|distinct|separate).{0,100}Zoo-Code", text, re.I | re.S):
        errors.append("gateway guide does not explicitly distinguish ZCode from Zoo-Code")

    for marker in ("\x00", "\ufffd", "â€", "TODO", "TBD", "FIXME", "PLACEHOLDER", "{{", "}}"):
        if marker in text:
            errors.append(f"gateway guide contains placeholder/corruption marker: {marker!r}")

    root_resolved = root.resolve()
    for target in _repository_relative_markdown_targets(text):
        candidate = (path.parent / target).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError:
            errors.append(f"gateway guide link escapes repository: {target}")
            continue
        if not candidate.exists():
            errors.append(f"gateway guide has missing repository-relative link target: {target}")

    authority_lock_path = root / "contracts" / "authority-lock.yaml"
    if not authority_lock_path.is_file():
        errors.append("missing authority-lock contract for gateway guide classification")
    else:
        authority_lock = authority_lock_path.read_text(encoding="utf-8")
        normal_workstream = re.search(
            r"(?ms)^  normal_workstream:\s*\n(?P<body>.*?)(?=^  [a-z_]+:\s*$|^enforcement:)",
            authority_lock,
        )
        if normal_workstream is None or GATEWAY_GUIDE not in normal_workstream.group("body"):
            errors.append("authority-lock does not classify gateway guide under normal_workstream")

    doc_authority_path = root / "DOC_AUTHORITY.md"
    if not doc_authority_path.is_file():
        errors.append("missing DOC_AUTHORITY for gateway guide classification")
    else:
        doc_authority = doc_authority_path.read_text(encoding="utf-8")

        def section(heading: str) -> str:
            match = re.search(
                rf"(?ms)^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
                doc_authority,
            )
            return match.group("body") if match else ""

        subordinate = section("Subordinate developer navigation (procedural; not authority)")
        authoritative = section("Authoritative — stable (safe to follow; change rarely, with approval)")
        if GATEWAY_GUIDE not in subordinate:
            errors.append("DOC_AUTHORITY does not classify gateway guide as subordinate navigation")
        if GATEWAY_GUIDE in authoritative:
            errors.append("DOC_AUTHORITY incorrectly classifies gateway guide as authoritative stable")

    migration_path = root / "docs" / "bifrost" / "MIGRATION_RUNBOOK.md"
    if not migration_path.is_file():
        errors.append("missing Bifrost migration runbook")
    else:
        migration = migration_path.read_text(encoding="utf-8")
        if "v2.0.0-prerelease1" in migration:
            errors.append("Bifrost migration runbook contains stale prerelease pin")
        if "E:\\AgentCore-Backups\\" in migration:
            errors.append("Bifrost migration runbook contains stale AgentCore backup root")
        backup_helper = re.search(
            r"(?is)Backup-AgentCoreBifrostConfig\.ps1.{0,240}"
            r"(?:configuration|config).{0,100}not a complete runtime checkpoint",
            migration,
        )
        if backup_helper is None:
            errors.append("Bifrost migration runbook omits config-only backup-helper limitation")
        if "unless rolling back intentionally" in migration:
            errors.append("Bifrost migration runbook permits a legacy direct baseline as ordinary rollback")
        for required in (
            "Ordinary rollback restores the last accepted Bifrost and client state",
            "If gateway restoration fails, stop and report `agentcore-gateway` unavailable",
            "A legacy direct baseline requires an explicit authority change and is never an ordinary rollback",
        ):
            if required not in migration:
                errors.append(f"Bifrost migration runbook missing fail-closed rollback rule: {required}")

    rollback_path = root / "docs" / "bifrost" / "ROLLBACK_RUNBOOK.md"
    if not rollback_path.is_file():
        errors.append("missing Bifrost rollback runbook")
    else:
        rollback = rollback_path.read_text(encoding="utf-8")
        for stale in (
            "returning to pre-gateway direct baselines",
            "without calling it a rollback",
        ):
            if stale in rollback:
                errors.append(f"Bifrost rollback runbook retains permissive legacy-direct wording: {stale}")
        for required in (
            "Restore and validate the last accepted Bifrost gateway and client state",
            "If gateway restoration fails, stop and report `agentcore-gateway` unavailable",
            "A legacy direct baseline requires an explicit authority change and is never an ordinary rollback",
        ):
            if required not in rollback:
                errors.append(f"Bifrost rollback runbook missing fail-closed rule: {required}")

    registry_path = root / "contracts" / "bifrost-upstream-mcp-registry.json"
    capability_profiles_path = root / CAPABILITY_PROFILES_DOC
    if not capability_profiles_path.is_file():
        errors.append(f"missing Bifrost capability profiles document: {CAPABILITY_PROFILES_DOC}")
    else:
        capability_profiles = capability_profiles_path.read_text(encoding="utf-8")
        setup_path = root / UNIFIED_GATEWAY_SETUP
        setup = setup_path.read_text(encoding="utf-8") if setup_path.is_file() else ""
        if "artiforge" in setup.casefold() or "artiforge" in capability_profiles.casefold():
            errors.append("Bifrost documentation references nonexistent registry server: artiforge")
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"cannot validate Bifrost registry-document parity: {exc}")
        else:
            debugger = (registry.get("servers") or {}).get("mcp-debugger")
            if not isinstance(debugger, dict):
                errors.append("Bifrost documentation example missing from registry: mcp-debugger")
            elif debugger.get("enabled") is not False or debugger.get("status") != "disabled":
                errors.append("Bifrost documentation example mcp-debugger is not disabled in registry")
            if "`mcp-debugger`" not in setup or "`mcp-debugger`" not in capability_profiles:
                errors.append("Bifrost disabled-server documentation does not use registry id mcp-debugger")
    return errors


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    texts: dict[str, str] = {}

    for relative in CURRENT_DOCS:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing current document: {relative}")
            continue
        texts[relative] = path.read_text(encoding="utf-8")

    for relative, marker in CLASSIFIED_EVIDENCE.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing classified evidence: {relative}")
            continue
        if marker not in path.read_text(encoding="utf-8"):
            errors.append(f"historical document missing classification marker {marker!r}: {relative}")

    joined = "\n".join(texts.values())
    for stale in (
        "82450b8c3b3884d12e2e1eece22b5771484e8686",
        "110/110 tests",
        "v0.2.1 release recertification pending",
    ):
        if stale in joined:
            errors.append(f"stale Context Engine acceptance claim remains: {stale}")

    context = texts.get("CONTEXT_BLOCK.md", "")
    for required in (
        "AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION",
        "v0.2.4 exact-installed; Bifrost v2.0.0 recertification pending",
        "AgentCore-PostgreSQL18",
        "live direct-API and signed-gateway isolation canaries passed",
    ):
        if required not in context:
            errors.append(f"CONTEXT_BLOCK missing current launch gate: {required}")

    authority = texts.get("DOC_AUTHORITY.md", "")
    if "point-in-time Context Engine v0.2.0" not in authority:
        errors.append("DOC_AUTHORITY does not classify the 2026-08-02 acceptance as v0.2.0 point-in-time evidence")
    if "Authoritative current Context Engine acceptance" in authority:
        errors.append("DOC_AUTHORITY still promotes the old Context Engine audit as current")
    if "use the newest dated handoff for live status" in authority:
        errors.append("DOC_AUTHORITY still allows handoff recency to override current-state authority")
    if (
        "docs/operations/LANGFUSE_TRACING_AND_PROMPTS.md" not in authority
        or "Inherited untracked WIP" not in authority
    ):
        errors.append("DOC_AUTHORITY does not explicitly classify inherited Langfuse WIP")

    milestones = texts.get("MILESTONES.md", "")
    if "Milestone acceptance is point-in-time evidence" not in milestones:
        errors.append("MILESTONES does not separate historical acceptance from current readiness")

    alignment = texts.get("docs/operations/AGENTCORE_ALIGNMENT_SKILL.md", "")
    if "installed_unverified" not in alignment or "SwarmClaw receives no AgentCore skill install" not in alignment:
        errors.append("alignment skill runbook omits honest host or Swarm boundary status")

    acceptance = texts.get(
        "audits/CONTEXT_ENGINE_0_2_4_AND_ALIGNMENT_ACCEPTANCE_2026-08-04.md", ""
    )
    if "Exact release identity" not in acceptance or "## Independent review" not in acceptance:
        errors.append("Context Engine acceptance audit omits release identity or independent review")

    read_order = texts.get("docs/agent-policy/DOCUMENTATION_READ_ORDER.md", "")
    if "Global `BLUEPRINT.md` and current `CONTEXT_BLOCK.md`" not in read_order:
        errors.append("DOCUMENTATION_READ_ORDER omits the stable/current authority pair")
    if "MEMORY_PLATFORM_IMPLEMENTATION_HANDOFF_2026-07-14.md" in read_order:
        errors.append("DOCUMENTATION_READ_ORDER still mandates a historical memory handoff")

    for relative in OPERATOR_RUNBOOKS:
        text = texts.get(relative, "")
        if REPO_PYTHON not in text:
            errors.append(f"operator runbook missing repository Python: {relative}")
        if not re.search(
            rf"(?im)^\s*Set-Location\s+['\"]{re.escape(SCRIPTS_CWD)}['\"]\s*$",
            text,
        ):
            errors.append(f"operator runbook missing explicit scripts working directory: {relative}")
        if re.search(
            rf"(?im)^\s*Set-Location\s+['\"]{re.escape(REPO_ROOT_CWD)}['\"]\s*$",
            text,
        ):
            errors.append(f"operator runbook launches from repository root instead of scripts: {relative}")
        if SYSTEM_PYTHON in text:
            errors.append(f"operator runbook still teaches system Python: {relative}")
        if re.search(r"(?m)^\s*python\s+-m\s+agentcore\b", text):
            errors.append(f"operator runbook contains unqualified agentcore command: {relative}")
        if re.search(r"(?im)(?:^|\|)\s*`?pip\s+install\b", text):
            errors.append(f"operator runbook contains bare pip install command: {relative}")

    workflow_runbook = texts.get("docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md", "")
    if "**Status:** READY" in workflow_runbook:
        errors.append("workflow runbook still claims unconditional READY")

    stable_requirements = {
        "agentcore-gateway": "MASTER_CONFIG_AND_PROMPT.md",
        "http://127.0.0.1:8080/mcp": "MASTER_CONFIG_AND_PROMPT.md",
        "127.0.0.1:55433": "CONTEXT_BLOCK.md",
        "neutral SwarmRecall": "CONTEXT_BLOCK.md",
        "Portable Context Engine": "MASTER_CONFIG_AND_PROMPT.md",
    }
    for required, relative in stable_requirements.items():
        if required.casefold() not in texts.get(relative, "").casefold():
            errors.append(f"stable architecture term missing from {relative}: {required}")

    errors.extend(validate_client_authority_alignment(root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    resolved_root = args.root.resolve()
    errors = validate(resolved_root)
    errors.extend(validate_gateway_guide(resolved_root))
    result = {
        "ok": not errors,
        "checked": [*CURRENT_DOCS, GATEWAY_GUIDE],
        "classified_evidence": list(CLASSIFIED_EVIDENCE),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    elif errors:
        for error in errors:
            print(f"FAIL: {error}")
    else:
        print(f"OK: current documentation surface aligned ({len(CURRENT_DOCS)} files)")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
