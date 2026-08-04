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
        "v0.2.4 exact-installed and live-certified",
        "AgentCore-PostgreSQL18",
        "pool identity",
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
