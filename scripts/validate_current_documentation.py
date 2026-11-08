"""Validate the small documentation surface allowed to claim current readiness."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CURRENT_DOCS = (
    "DOC_AUTHORITY.md",
    "CONTEXT_BLOCK.md",
    "MASTER_CONFIG_AND_PROMPT.md",
    "MILESTONES.md",
    "AGENTS.md",
    "docs/agent-policy/DOCUMENTATION_READ_ORDER.md",
    "docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md",
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

READ_ORDER_CONTRACT = "contracts/project-execution-policy.json"
HUMAN_READ_ORDER_POLICIES = (
    "AGENTS.md",
    "docs/agent-policy/DOCUMENTATION_READ_ORDER.md",
    "docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md",
)
FORBIDDEN_HISTORICAL_HANDOFF = "MEMORY_PLATFORM_IMPLEMENTATION_HANDOFF_2026-07-14.md"
LEGACY_READ_ORDER_PHRASE = "Hardcoded read sequence for a managed project"

EXPECTED_SELF_CHECKS = {
    "SC-01": "Discover and read every applicable AGENTS.md and CLAUDE.md before task work.",
    "SC-02": "Verify the exact repository, worktree, branch, HEAD, approved base, and dirty state.",
    "SC-03": "Determine task mode, project ownership and enrollment, and the AgentCore or Swarm boundary.",
    "SC-04": "Classify every target's authority and protection class and confirm matching authorization before writes.",
    "SC-05": "Run the Ask-mode Foundation Report when this is the first task in the repository.",
    "SC-06": "Compare requested scope, authority, current state, and evidence and stop on unresolved drift or conflict.",
}

EXPECTED_TRIGGER_DOCUMENTS = {
    "architecture_governance": [
        "BLUEPRINT.md",
        "CONTEXT_BLOCK.md",
        "docs/agent-policy/",
    ],
    "bifrost_gateway": [
        "contracts/bifrost-upstream-mcp-registry.json",
        "contracts/agentcore-gateway-client.json",
        "GATEWAY_AND_BIFROST_DEVELOPER_GUIDE.md",
    ],
    "memory_database": [
        "CONTEXT_BLOCK.md",
        "docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md",
    ],
    "new_project_bootstrap": [
        "docs/agent-policy/",
        "docs/current/MASTER_TODO.md",
        "project AGENTS.md and CLAUDE.md",
        ".agentcore project governance files",
    ],
    "documentation_mutation": [
        "docs/agent-policy/DOCUMENTATION_GOVERNANCE.md",
        "AUTHORITY_LOCK.md",
        "contracts/authority-lock.yaml",
    ],
    "dependency_external_api": [
        "project manifests and lockfiles",
        "Arabold exact-version documentation index",
    ],
    "ui_scaffolding": [
        "docs/knowledge-library/",
        "knowledge library query for framework and asset_type",
    ],
    "implementation": [
        "project state and decisions",
        "relevant manifests and lockfiles",
        "relevant implementation files",
    ],
    "historical_evidence": [
        "specifically cited historical or superseded evidence required for the current fact question"
    ],
}

EXPECTED_SAFEGUARDS = {
    "SG-01": "Load only the matching task-triggered documents beyond the mandatory authority baseline; never load the full corpus automatically.",
    "SG-02": "Historical or superseded evidence is never automatic and never overrides current authority.",
    "SG-03": "Documentation mutation requires documentation governance, matching approval, rollback evidence, guard acceptance, and the documentation maintainer.",
    "SG-04": "Generated state and decision projections remain projection-worker-only.",
    "SG-05": "Do not expand task scope or claim merge, deployment, or adoption without the required new approval and evidence.",
}


def _duplicates(values: list[str]) -> set[str]:
    return {value for value in values if values.count(value) > 1}


def _all_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _all_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _all_strings(nested)


def _validate_id_entries(
    entries: object,
    expected: dict[str, str],
    value_key: str,
    label: str,
    errors: list[str],
) -> dict[str, dict]:
    if not isinstance(entries, list):
        errors.append(f"read_order.{label} must be an array")
        return {}

    ids = [entry.get("id") for entry in entries if isinstance(entry, dict)]
    string_ids = [entry_id for entry_id in ids if isinstance(entry_id, str)]
    for duplicate in sorted(_duplicates(string_ids)):
        errors.append(f"read_order.{label} contains duplicate id {duplicate}")
    for missing in sorted(set(expected) - set(string_ids)):
        errors.append(f"read_order.{label} is missing {missing}")
    for unknown in sorted(set(string_ids) - set(expected)):
        errors.append(f"read_order.{label} contains unknown or mis-cased id {unknown}")

    by_id: dict[str, dict] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"read_order.{label}[{index}] must be an object")
            continue
        entry_id = entry.get("id")
        if isinstance(entry_id, str) and entry_id not in by_id:
            by_id[entry_id] = entry
        if set(entry) != {"id", value_key}:
            errors.append(
                f"read_order.{label}[{index}] must contain only id and {value_key}"
            )

    for entry_id, expected_value in expected.items():
        entry = by_id.get(entry_id)
        if entry is not None and entry.get(value_key) != expected_value:
            errors.append(
                f"read_order {entry_id} {value_key} does not match the approved value"
            )
    return by_id


def _validate_task_scoped_read_order(
    root: Path, texts: dict[str, str], errors: list[str]
) -> None:
    contract_path = root / READ_ORDER_CONTRACT
    if not contract_path.is_file():
        errors.append(f"missing read-order contract: {READ_ORDER_CONTRACT}")
        return
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid read-order contract JSON: {exc}")
        return

    read_order = contract.get("read_order")
    if not isinstance(read_order, dict):
        errors.append("read_order must be a task_scoped object; legacy array is forbidden")
        return

    expected_keys = {
        "mode",
        "mandatory_self_checks",
        "mandatory_authority_baseline",
        "task_triggers",
        "safeguards",
    }
    if set(read_order) != expected_keys:
        errors.append(
            "read_order keys must be exactly " + ", ".join(sorted(expected_keys))
        )
    if read_order.get("mode") != "task_scoped":
        errors.append("read_order.mode must be task_scoped")

    _validate_id_entries(
        read_order.get("mandatory_self_checks"),
        EXPECTED_SELF_CHECKS,
        "instruction",
        "mandatory_self_checks",
        errors,
    )

    baseline = read_order.get("mandatory_authority_baseline")
    expected_baseline = ["PROJECT_ANCHOR.md", "DOC_AUTHORITY.md"]
    if baseline != expected_baseline:
        errors.append(
            "read_order mandatory baseline must be exactly "
            f"{expected_baseline}; got {baseline!r}"
        )

    triggers = read_order.get("task_triggers")
    trigger_by_id: dict[str, dict] = {}
    if not isinstance(triggers, list):
        errors.append("read_order.task_triggers must be an array")
    else:
        trigger_ids = [
            trigger.get("id") for trigger in triggers if isinstance(trigger, dict)
        ]
        string_trigger_ids = [
            trigger_id for trigger_id in trigger_ids if isinstance(trigger_id, str)
        ]
        for duplicate in sorted(_duplicates(string_trigger_ids)):
            errors.append(f"read_order.task_triggers contains duplicate id {duplicate}")
        for missing in sorted(set(EXPECTED_TRIGGER_DOCUMENTS) - set(string_trigger_ids)):
            errors.append(f"read_order.task_triggers is missing {missing}")
        for unknown in sorted(set(string_trigger_ids) - set(EXPECTED_TRIGGER_DOCUMENTS)):
            errors.append(
                f"read_order.task_triggers contains unknown or mis-cased id {unknown}"
            )
        for index, trigger in enumerate(triggers):
            if not isinstance(trigger, dict):
                errors.append(f"read_order.task_triggers[{index}] must be an object")
                continue
            if set(trigger) != {"id", "when", "documents"}:
                errors.append(
                    f"read_order.task_triggers[{index}] must contain only id, when, and documents"
                )
            trigger_id = trigger.get("id")
            if isinstance(trigger_id, str) and trigger_id not in trigger_by_id:
                trigger_by_id[trigger_id] = trigger
            if not isinstance(trigger.get("when"), str) or not trigger["when"].strip():
                errors.append(f"read_order trigger {trigger_id!r} requires a non-empty when")

        for trigger_id, expected_documents in EXPECTED_TRIGGER_DOCUMENTS.items():
            trigger = trigger_by_id.get(trigger_id)
            if trigger is not None and trigger.get("documents") != expected_documents:
                errors.append(
                    f"read_order trigger {trigger_id} document sequence must be "
                    f"{expected_documents}; got {trigger.get('documents')!r}"
                )

    _validate_id_entries(
        read_order.get("safeguards"),
        EXPECTED_SAFEGUARDS,
        "rule",
        "safeguards",
        errors,
    )

    for value in _all_strings(read_order):
        if FORBIDDEN_HISTORICAL_HANDOFF in value:
            errors.append(
                "forbidden historical memory handoff appears in read_order: "
                + FORBIDDEN_HISTORICAL_HANDOFF
            )
            break

    human_text = "\n".join(texts.get(path, "") for path in HUMAN_READ_ORDER_POLICIES)
    if FORBIDDEN_HISTORICAL_HANDOFF in human_text:
        errors.append(
            "forbidden historical memory handoff appears in human policy: "
            + FORBIDDEN_HISTORICAL_HANDOFF
        )
    if LEGACY_READ_ORDER_PHRASE in human_text:
        errors.append(f"legacy phrase remains: {LEGACY_READ_ORDER_PHRASE}")

    expected_ids = (
        set(EXPECTED_SELF_CHECKS)
        | set(EXPECTED_TRIGGER_DOCUMENTS)
        | set(EXPECTED_SAFEGUARDS)
    )
    id_pattern = re.compile(
        r"`(SC-[0-9]{2}|SG-[0-9]{2}|"
        + "|".join(re.escape(value) for value in EXPECTED_TRIGGER_DOCUMENTS)
        + r"|[a-z][a-z0-9_]*_trigger)`"
    )
    human_ids = set(id_pattern.findall(human_text))
    for missing in sorted(expected_ids - human_ids):
        errors.append(f"human read-order policies are missing exact id {missing}")
    for extra in sorted(human_ids - expected_ids):
        errors.append(f"human read-order policies contain unknown id {extra}")

    read_order_text = texts.get("docs/agent-policy/DOCUMENTATION_READ_ORDER.md", "")
    for required in (
        "mandatory authority baseline",
        "architecture_governance",
        "BLUEPRINT.md",
        "CONTEXT_BLOCK.md",
    ):
        if required.casefold() not in read_order_text.casefold():
            errors.append(f"DOCUMENTATION_READ_ORDER missing task-scoped term: {required}")


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
        "AgentCore-PostgreSQL18",
    ):
        if required not in context:
            errors.append(f"CONTEXT_BLOCK missing current launch gate: {required}")

    if "v0.2.4 exact-installed and live-certified" in context:
        errors.append(
            "CONTEXT_BLOCK contains unsupported current certification claim: "
            "v0.2.4 exact-installed and live-certified"
        )

    current_markers = (
        "Context Engine 0.2.5 exact-installed",
        "agentcore-context validate --live passed",
        "Bifrost v2.0.0",
        "memory 0.9.1",
        "ten tools",
        "RELEASE_CANDIDATE",
        "exact-SHA independent re-review required",
        "project_count=11",
        "one shared global pool",
        "11 private pools",
        "neutral Recall current health degraded",
        "URLError",
        "cached_project_topologies=0",
        "September isolation canaries are point-in-time evidence",
    )

    for marker in current_markers:
        if marker not in context:
            errors.append(
                f"CONTEXT_BLOCK missing current readiness marker: {marker}"
            )

    if "neutral Recall current health healthy" in context:
        errors.append(
            "CONTEXT_BLOCK claims neutral Recall current health healthy "
            "but required degraded/URLError evidence is absent"
        )

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

    _validate_task_scoped_read_order(root, texts, errors)

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

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    errors = validate(args.root.resolve())
    result = {
        "ok": not errors,
        "checked": list(CURRENT_DOCS),
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
