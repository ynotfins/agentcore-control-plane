from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validate_current_documentation import (
    CLASSIFIED_EVIDENCE,
    CURRENT_DOCS,
    REPO_PYTHON,
    SCRIPTS_CWD,
    validate,
)


# ---------------------------------------------------------------------------
# Task-scoped read-order contract helpers (TDD RED step)
# ---------------------------------------------------------------------------

CONTRACT_RELATIVE = "contracts/project-execution-policy.json"

TRIGGER_IDS = [
    "architecture_governance",
    "bifrost_gateway",
    "memory_database",
    "new_project_bootstrap",
    "documentation_mutation",
    "dependency_external_api",
    "ui_scaffolding",
    "implementation",
    "historical_evidence",
]

SC_IDS = ["SC-01", "SC-02", "SC-03", "SC-04", "SC-05", "SC-06"]

SC_INSTRUCTIONS = {
    "SC-01": "Discover and read every applicable AGENTS.md and CLAUDE.md before task work.",
    "SC-02": "Verify the exact repository, worktree, branch, HEAD, approved base, and dirty state.",
    "SC-03": "Determine task mode, project ownership and enrollment, and the AgentCore or Swarm boundary.",
    "SC-04": "Classify every target's authority and protection class and confirm matching authorization before writes.",
    "SC-05": "Run the Ask-mode Foundation Report when this is the first task in the repository.",
    "SC-06": "Compare requested scope, authority, current state, and evidence and stop on unresolved drift or conflict.",
}

SAFEGUARD_IDS = ["SG-01", "SG-02", "SG-03", "SG-04", "SG-05"]

SAFEGUARD_RULES = {
    "SG-01": "Load only the matching task-triggered documents beyond the mandatory authority baseline; never load the full corpus automatically.",
    "SG-02": "Historical or superseded evidence is never automatic and never overrides current authority.",
    "SG-03": "Documentation mutation requires documentation governance, matching approval, rollback evidence, guard acceptance, and the documentation maintainer.",
    "SG-04": "Generated state and decision projections remain projection-worker-only.",
    "SG-05": "Do not expand task scope or claim merge, deployment, or adoption without the required new approval and evidence.",
}

BASELINE = ["PROJECT_ANCHOR.md", "DOC_AUTHORITY.md"]

TRIGGER_DOCUMENTS: dict[str, list[str]] = {
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

HUMAN_POLICY_FILES: list[str] = [
    "AGENTS.md",
    "docs/agent-policy/DOCUMENTATION_READ_ORDER.md",
    "docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md",
]

FORBIDDEN_HANDOFF = "MEMORY_PLATFORM_IMPLEMENTATION_HANDOFF_2026-07-14.md"
FORBIDDEN_PHRASE = "Hardcoded read sequence for a managed project"


def _make_valid_contract() -> dict:
    """Return a minimal valid task-scoped read_order contract dict."""
    return {
        "read_order": {
            "mode": "task_scoped",
            "mandatory_self_checks": [
                {"id": sc, "instruction": SC_INSTRUCTIONS[sc]} for sc in SC_IDS
            ],
            "mandatory_authority_baseline": list(BASELINE),
            "task_triggers": [
                {"id": tid, "when": f"Task scope requires {tid.replace('_', ' ')}.", "documents": list(TRIGGER_DOCUMENTS[tid])}
                for tid in TRIGGER_IDS
            ],
            "safeguards": [
                {"id": sg, "rule": SAFEGUARD_RULES[sg]} for sg in SAFEGUARD_IDS
            ],
        }
    }


def _write_contract(root: Path, contract: dict) -> Path:
    """Write *contract* into *root* / CONTRACT_RELATIVE and return the path."""
    path = root / CONTRACT_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return path


def _write_human_policies(
    root: Path,
    sc_ids: list[str] | None = None,
    trigger_ids: list[str] | None = None,
    safeguard_ids: list[str] | None = None,
) -> None:
    """Write AGENTS.md, DOCUMENTATION_READ_ORDER.md, and
    NEW_PROJECT_BOOTSTRAP.md with backticked ids and baseline wording."""
    sc_ids = sc_ids if sc_ids is not None else SC_IDS
    trigger_ids = trigger_ids if trigger_ids is not None else TRIGGER_IDS
    safeguard_ids = safeguard_ids if safeguard_ids is not None else SAFEGUARD_IDS

    sc_lines = "\n".join(f"- `{sid}`" for sid in sc_ids)
    trigger_lines = "\n".join(f"- `{tid}`" for tid in trigger_ids)
    safeguard_lines = "\n".join(f"- `{sg}`" for sg in safeguard_ids)

    agents = (
        "# AGENTS.md\n\n"
        "## Task-Scoped Read Order\n\n"
        "Every task MUST first read the mandatory authority baseline:\n"
        "- `PROJECT_ANCHOR.md`\n"
        "- `DOC_AUTHORITY.md`\n\n"
        "Then the task MUST read only the documents listed under the matching trigger.\n\n"
        "## Self-Checks\n"
        f"{sc_lines}\n\n"
        "## Safeguards\n"
        f"{safeguard_lines}\n\n"
        "## Triggers\n"
        f"{trigger_lines}\n"
    )
    read_order = (
        "# Documentation Read Order\n\n"
        "## Task-Scoped Read Order\n\n"
        "Every task MUST first read the mandatory authority baseline:\n"
        "- `PROJECT_ANCHOR.md`\n"
        "- `DOC_AUTHORITY.md`\n\n"
        "Then read only the trigger-specific documents for the active task.\n\n"
        "Under `architecture_governance`, read `BLUEPRINT.md` then `CONTEXT_BLOCK.md`.\n\n"
        "## Self-Checks\n"
        f"{sc_lines}\n\n"
        "## Safeguards\n"
        f"{safeguard_lines}\n\n"
        "## Triggers\n"
        f"{trigger_lines}\n"
    )
    bootstrap = (
        "# New Project Bootstrap\n\n"
        "## Task-Scoped Read Order\n\n"
        "Always start with `PROJECT_ANCHOR.md` then `DOC_AUTHORITY.md`.\n"
        "Follow the trigger-specific read order for the current task.\n"
    )

    (root / "AGENTS.md").write_text(agents, encoding="utf-8")
    (root / "docs/agent-policy/DOCUMENTATION_READ_ORDER.md").parent.mkdir(
        parents=True, exist_ok=True
    )
    (root / "docs/agent-policy/DOCUMENTATION_READ_ORDER.md").write_text(
        read_order, encoding="utf-8"
    )
    (root / "docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md").parent.mkdir(
        parents=True, exist_ok=True
    )
    (root / "docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md").write_text(
        bootstrap, encoding="utf-8"
    )


class CurrentDocumentationValidatorTests(unittest.TestCase):
    def _root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        baseline = (
            "AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION\n"
            "Context Engine 0.2.5 exact-installed\n"
            "AgentCore-PostgreSQL18\n"
            "agentcore-context validate --live passed\n"
            "Bifrost v2.0.0 memory 0.9.1 ten tools\n"
            "RELEASE_CANDIDATE exact-SHA independent re-review required\n"
            "neutral Recall project_count=11 one shared global pool 11 private pools\n"
            "neutral Recall current health degraded URLError cached_project_topologies=0\n"
            "September isolation canaries are point-in-time evidence\n"
            "point-in-time Context Engine v0.2.0\n"
            "docs/operations/LANGFUSE_TRACING_AND_PROMPTS.md Inherited untracked WIP\n"
            "Milestone acceptance is point-in-time evidence\n"
            "Global `BLUEPRINT.md` and current `CONTEXT_BLOCK.md`\n"
            f"{REPO_PYTHON}\n"
            f"Set-Location '{SCRIPTS_CWD}'\n"
            "agentcore-gateway http://127.0.0.1:8080/mcp\n"
            "127.0.0.1:55433 neutral SwarmRecall Portable Context Engine\n"
            "installed_unverified SwarmClaw receives no AgentCore skill install\n"
            "Exact release identity\n## Independent review\n"
        )
        for relative in CURRENT_DOCS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(baseline, encoding="utf-8")
        for relative, marker in CLASSIFIED_EVIDENCE.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {marker}\n", encoding="utf-8")
        _write_contract(root, _make_valid_contract())
        _write_human_policies(root)
        return root

    def _root_with_contract(self, contract: dict | None = None) -> Path:
        """Return a root with all surface docs plus a task-scoped contract."""
        root = self._root()
        _write_contract(root, contract if contract is not None else _make_valid_contract())
        _write_human_policies(root)
        return root

    # ------------------------------------------------------------------
    # Focused validate(root) rejection tests on current-truth markers
    # ------------------------------------------------------------------

    def test_rejects_unsupported_context_engine_phrase_v024(self) -> None:
        root = self._root()
        path = root / "CONTEXT_BLOCK.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "Context Engine 0.2.5 exact-installed",
                "v0.2.4 exact-installed and live-certified",
            ),
            encoding="utf-8",
        )
        errors = validate(root)
        self.assertTrue(
            any("v0.2.4" in error and "live-certified" in error for error in errors),
            f"expected rejection of unsupported 'v0.2.4 exact-installed and live-certified', got: {errors}",
        )

    def test_rejects_missing_release_candidate_gate(self) -> None:
        root = self._root()
        path = root / "CONTEXT_BLOCK.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "RELEASE_CANDIDATE exact-SHA independent re-review required",
                "",
            ),
            encoding="utf-8",
        )
        errors = validate(root)
        self.assertTrue(
            any("RELEASE_CANDIDATE" in error or "exact-SHA" in error for error in errors),
            f"expected rejection for missing RELEASE_CANDIDATE gate, got: {errors}",
        )

    def test_rejects_missing_validate_live_or_bifrost_evidence(self) -> None:
        root = self._root()
        path = root / "CONTEXT_BLOCK.md"
        content = path.read_text(encoding="utf-8")
        content = content.replace("agentcore-context validate --live passed", "")
        content = content.replace("Bifrost v2.0.0 memory 0.9.1 ten tools", "")
        path.write_text(content, encoding="utf-8")
        errors = validate(root)
        self.assertTrue(
            any(
                phrase in error
                for phrase in ("validate --live", "Bifrost v2.0.0")
                for error in errors
            ),
            f"expected rejection for missing validate --live or Bifrost evidence, got: {errors}",
        )

    def test_rejects_missing_project_count_and_pool_topology_markers(self) -> None:
        root = self._root()
        path = root / "CONTEXT_BLOCK.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "neutral Recall project_count=11 one shared global pool 11 private pools",
                "",
            ),
            encoding="utf-8",
        )
        errors = validate(root)
        self.assertTrue(
            any("project_count" in error or "pool" in error for error in errors),
            f"expected rejection for missing project_count/pool markers, got: {errors}",
        )

    def test_rejects_healthy_neutral_recall_claim_when_fixture_has_degraded_urlerror(
        self,
    ) -> None:
        root = self._root()
        path = root / "CONTEXT_BLOCK.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "neutral Recall current health degraded URLError cached_project_topologies=0",
                "neutral Recall current health healthy",
            ),
            encoding="utf-8",
        )
        errors = validate(root)
        self.assertTrue(
            any("degraded" in error or "URLError" in error for error in errors),
            f"expected rejection of healthy claim when fixture records degraded, got: {errors}",
        )

    def test_rejects_missing_degraded_urlerror_cached_topologies_markers(self) -> None:
        root = self._root()
        path = root / "CONTEXT_BLOCK.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "neutral Recall current health degraded URLError cached_project_topologies=0",
                "",
            ),
            encoding="utf-8",
        )
        errors = validate(root)
        self.assertTrue(
            any(
                marker in error
                for marker in ("degraded", "URLError", "cached_project_topologies")
                for error in errors
            ),
            f"expected rejection for missing degraded/URLError/cached_project_topologies=0 markers, got: {errors}",
        )

    # ------------------------------------------------------------------
    # existing tests
    # ------------------------------------------------------------------

    def test_accepts_aligned_surface(self) -> None:
        self.assertEqual(validate(self._root()), [])

    def test_rejects_stale_context_engine_acceptance(self) -> None:
        root = self._root()
        path = root / "CONTEXT_BLOCK.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n110/110 tests\n", encoding="utf-8")
        self.assertTrue(any("stale Context Engine" in error for error in validate(root)))

    def test_rejects_superseded_v021_pending_gate(self) -> None:
        root = self._root()
        path = root / "CONTEXT_BLOCK.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\nv0.2.1 release recertification pending\n",
            encoding="utf-8",
        )
        self.assertTrue(any("stale Context Engine" in error for error in validate(root)))

    def test_rejects_unqualified_operator_command(self) -> None:
        root = self._root()
        path = root / "docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md"
        path.write_text(path.read_text(encoding="utf-8") + "\npython -m agentcore workflow topology\n", encoding="utf-8")
        self.assertTrue(any("unqualified agentcore command" in error for error in validate(root)))

    def test_rejects_historical_handoff_in_read_order(self) -> None:
        root = self._root()
        path = root / "docs/agent-policy/DOCUMENTATION_READ_ORDER.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\nMEMORY_PLATFORM_IMPLEMENTATION_HANDOFF_2026-07-14.md\n",
            encoding="utf-8",
        )
        self.assertTrue(any("historical memory handoff" in error for error in validate(root)))

    def test_rejects_bare_pip_in_operator_runbook(self) -> None:
        root = self._root()
        path = root / "docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\n| Missing dependency | pip install package |\n",
            encoding="utf-8",
        )
        self.assertTrue(any("bare pip install" in error for error in validate(root)))

    def test_rejects_repo_root_launch(self) -> None:
        root = self._root()
        path = root / "docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\nSet-Location 'D:\\github\\agentcore-control-plane'\n"
            + f"& '{REPO_PYTHON}' -m agentcore workflow topology\n",
            encoding="utf-8",
        )
        self.assertTrue(any("repository root instead of scripts" in error for error in validate(root)))

    def test_rejects_missing_scripts_working_directory(self) -> None:
        root = self._root()
        path = root / "scripts/agentcore_workflow/studio/README.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(f"Set-Location '{SCRIPTS_CWD}'\n", ""),
            encoding="utf-8",
        )
        self.assertTrue(any("missing explicit scripts working directory" in error for error in validate(root)))

    def test_rejects_newest_handoff_as_live_authority(self) -> None:
        root = self._root()
        path = root / "DOC_AUTHORITY.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\nuse the newest dated handoff for live status\n",
            encoding="utf-8",
        )
        self.assertTrue(any("handoff recency" in error for error in validate(root)))

    def test_rejects_alignment_runbook_without_honest_host_status(self) -> None:
        root = self._root()
        path = root / "docs/operations/AGENTCORE_ALIGNMENT_SKILL.md"
        path.write_text("SwarmClaw receives no AgentCore skill install\n", encoding="utf-8")
        self.assertTrue(any("alignment skill" in error for error in validate(root)))

    def test_rejects_acceptance_without_independent_review_section(self) -> None:
        root = self._root()
        path = root / "audits/CONTEXT_ENGINE_0_2_4_AND_ALIGNMENT_ACCEPTANCE_2026-08-04.md"
        path.write_text("Exact release identity\n", encoding="utf-8")
        self.assertTrue(any("acceptance audit" in error for error in validate(root)))

    # ------------------------------------------------------------------
    # task-scoped read-order TDD tests (RED — expected to fail)
    # ------------------------------------------------------------------

    # -- old array format rejection ------------------------------------

    def test_rejects_old_array_read_order(self) -> None:
        root = self._root_with_contract()
        contract_path = root / CONTRACT_RELATIVE
        contract_path.write_text(
            json.dumps({"read_order": ["PROJECT_ANCHOR.md", "DOC_AUTHORITY.md"]}),
            encoding="utf-8",
        )
        errors = validate(root)
        self.assertTrue(
            any("array" in error.lower() or "read_order" in error.lower() for error in errors),
            f"expected rejection of array read_order, got: {errors}",
        )

    # -- mode must be task_scoped --------------------------------------

    def test_rejects_read_order_mode_not_task_scoped(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["mode"] = "legacy"
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("task_scoped" in error for error in errors),
            f"expected rejection of non-task_scoped mode, got: {errors}",
        )

    # -- self-check ids ------------------------------------------------

    def test_rejects_missing_self_check_id(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["mandatory_self_checks"] = [
            {"id": sc, "instruction": SC_INSTRUCTIONS[sc]} for sc in SC_IDS[:5]
        ]  # missing SC-06
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("SC-06" in error for error in errors),
            f"expected rejection for missing SC-06, got: {errors}",
        )

    def test_rejects_unknown_self_check_id(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["mandatory_self_checks"].append(
            {"id": "SC-07", "instruction": "Unknown self-check."}
        )
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("SC-07" in error for error in errors),
            f"expected rejection for unknown SC-07, got: {errors}",
        )

    def test_rejects_duplicate_self_check_id(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["mandatory_self_checks"].append(
            {"id": "SC-01", "instruction": SC_INSTRUCTIONS["SC-01"]}
        )
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("duplicate" in error.lower() for error in errors),
            f"expected rejection for duplicate SC-01, got: {errors}",
        )

    def test_rejects_mis_cased_self_check_id(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["mandatory_self_checks"] = [
            {"id": s.lower(), "instruction": SC_INSTRUCTIONS[s]} for s in SC_IDS
        ]
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any(error for error in errors if "sc-" in error.lower()),
            f"expected case-sensitive rejection for lower-cased SC ids, got: {errors}",
        )

    def test_rejects_changed_self_check_instruction(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["mandatory_self_checks"][0]["instruction"] = "Weakened."
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("SC-01" in error and "instruction" in error.lower() for error in errors),
            f"expected rejection for changed SC-01 instruction, got: {errors}",
        )

    # -- trigger ids ---------------------------------------------------

    def test_rejects_missing_trigger_id(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["task_triggers"] = [
            t for t in contract["read_order"]["task_triggers"] if t["id"] != "implementation"
        ]
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("implementation" in error for error in errors),
            f"expected rejection for missing implementation trigger, got: {errors}",
        )

    def test_rejects_unknown_trigger_id(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["task_triggers"].append(
            {"id": "extra_trigger", "when": "unknown", "documents": []}
        )
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("extra_trigger" in error for error in errors),
            f"expected rejection for unknown extra_trigger, got: {errors}",
        )

    def test_rejects_duplicate_trigger_id(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["task_triggers"].append(
            {"id": "architecture_governance", "when": "duplicate", "documents": []}
        )
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("duplicate" in error.lower() for error in errors),
            f"expected rejection for duplicate architecture_governance, got: {errors}",
        )

    def test_rejects_mis_cased_trigger_id(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["task_triggers"][0]["id"] = "Architecture_Governance"
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("Architecture_Governance" in error for error in errors),
            f"expected case-sensitive rejection for mis-cased trigger, got: {errors}",
        )

    # -- baseline ------------------------------------------------------

    def test_rejects_baseline_not_project_anchor_then_doc_authority(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["mandatory_authority_baseline"] = ["DOC_AUTHORITY.md", "PROJECT_ANCHOR.md"]
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("baseline" in error.lower() for error in errors),
            f"expected rejection of swapped baseline order, got: {errors}",
        )

    def test_rejects_baseline_missing_doc_authority(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["mandatory_authority_baseline"] = ["PROJECT_ANCHOR.md"]
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("DOC_AUTHORITY.md" in error for error in errors),
            f"expected rejection for missing DOC_AUTHORITY.md in baseline, got: {errors}",
        )

    # -- Blueprint/Context are rejected in baseline, required in arch ---

    def test_rejects_blueprint_and_context_in_baseline(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["mandatory_authority_baseline"] = [
            "PROJECT_ANCHOR.md",
            "DOC_AUTHORITY.md",
            "BLUEPRINT.md",
        ]
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("BLUEPRINT.md" in error and "baseline" in error.lower() for error in errors),
            f"expected rejection of BLUEPRINT.md in baseline, got: {errors}",
        )

    def test_rejects_context_block_in_baseline(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["mandatory_authority_baseline"] = [
            "PROJECT_ANCHOR.md",
            "DOC_AUTHORITY.md",
            "CONTEXT_BLOCK.md",
        ]
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("CONTEXT_BLOCK.md" in error and "baseline" in error.lower() for error in errors),
            f"expected rejection of CONTEXT_BLOCK.md in baseline, got: {errors}",
        )

    # -- trigger document sequences ------------------------------------

    def test_rejects_architecture_trigger_missing_blueprint(self) -> None:
        contract = _make_valid_contract()
        for t in contract["read_order"]["task_triggers"]:
            if t["id"] == "architecture_governance":
                docs = list(TRIGGER_DOCUMENTS["architecture_governance"])
                docs.remove("BLUEPRINT.md")
                t["documents"] = docs
                break
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("BLUEPRINT.md" in error for error in errors),
            f"expected rejection for missing BLUEPRINT.md in architecture_governance, got: {errors}",
        )

    def test_rejects_architecture_trigger_missing_context_block(self) -> None:
        contract = _make_valid_contract()
        for t in contract["read_order"]["task_triggers"]:
            if t["id"] == "architecture_governance":
                docs = list(TRIGGER_DOCUMENTS["architecture_governance"])
                docs.remove("CONTEXT_BLOCK.md")
                t["documents"] = docs
                break
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("CONTEXT_BLOCK.md" in error for error in errors),
            f"expected rejection for missing CONTEXT_BLOCK.md in architecture_governance, got: {errors}",
        )

    def test_rejects_architecture_trigger_reordered_documents(self) -> None:
        contract = _make_valid_contract()
        for t in contract["read_order"]["task_triggers"]:
            if t["id"] == "architecture_governance":
                docs = list(TRIGGER_DOCUMENTS["architecture_governance"])
                docs[0], docs[1] = docs[1], docs[0]  # swap BLUEPRINT and CONTEXT_BLOCK
                t["documents"] = docs
                break
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("order" in error.lower() or "sequence" in error.lower() for error in errors),
            f"expected rejection for reordered architecture_governance docs, got: {errors}",
        )

    def test_rejects_architecture_trigger_partial_documents(self) -> None:
        contract = _make_valid_contract()
        for t in contract["read_order"]["task_triggers"]:
            if t["id"] == "architecture_governance":
                t["documents"] = ["BLUEPRINT.md"]
                break
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any(error for error in errors if "architecture" in error.lower()),
            f"expected rejection for partial architecture_governance docs, got: {errors}",
        )

    def test_missing_required_documents_per_trigger_table(self) -> None:
        """Subtest table: each trigger must have its required documents present."""
        for trigger_id, required_docs in TRIGGER_DOCUMENTS.items():
            with self.subTest(trigger=trigger_id):
                contract = _make_valid_contract()
                for t in contract["read_order"]["task_triggers"]:
                    if t["id"] == trigger_id:
                        t["documents"] = []
                        break
                root = self._root_with_contract(contract)
                errors = validate(root)
                self.assertTrue(
                    any(trigger_id in error for error in errors)
                    or any(
                        doc in error for doc in required_docs for error in errors
                    ),
                    f"expected rejection for empty docs in {trigger_id}, got: {errors}",
                )

    # -- historical_evidence special -----------------------------------

    def test_rejects_historical_evidence_not_exact_literal(self) -> None:
        contract = _make_valid_contract()
        for t in contract["read_order"]["task_triggers"]:
            if t["id"] == "historical_evidence":
                t["documents"] = ["some_other_doc.md"]
                break
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any(
                "specifically cited historical" in error
                or "historical_evidence" in error
                for error in errors
            ),
            f"expected rejection for non-literal historical_evidence docs, got: {errors}",
        )

    def test_rejects_missing_historical_evidence_trigger(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["task_triggers"] = [
            t for t in contract["read_order"]["task_triggers"] if t["id"] != "historical_evidence"
        ]
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("historical_evidence" in error for error in errors),
            f"expected rejection for missing historical_evidence trigger, got: {errors}",
        )

    # -- safeguard ids -------------------------------------------------

    def test_rejects_missing_safeguard_ids(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["safeguards"] = [
            {"id": sg, "rule": SAFEGUARD_RULES[sg]} for sg in SAFEGUARD_IDS[:3]
        ]
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("SG-04" in error or "SG-05" in error for error in errors),
            f"expected rejection for missing safeguard ids, got: {errors}",
        )

    def test_rejects_changed_safeguard_rule(self) -> None:
        contract = _make_valid_contract()
        contract["read_order"]["safeguards"][0]["rule"] = "Load everything automatically."
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any("SG-01" in error and "rule" in error.lower() for error in errors),
            f"expected rejection for changed SG-01 rule, got: {errors}",
        )

    # -- MEMORY_PLATFORM_IMPLEMENTATION_HANDOFF forbidden --------------

    def test_rejects_handoff_in_contract_string_location(self) -> None:
        contract = _make_valid_contract()
        for t in contract["read_order"]["task_triggers"]:
            if t["id"] == "architecture_governance":
                t["documents"].append(FORBIDDEN_HANDOFF)
                break
        root = self._root_with_contract(contract)
        errors = validate(root)
        self.assertTrue(
            any(FORBIDDEN_HANDOFF in error for error in errors),
            f"expected rejection of {FORBIDDEN_HANDOFF} in contract, got: {errors}",
        )

    def test_rejects_handoff_in_agents_md(self) -> None:
        root = self._root_with_contract()
        agents = root / "AGENTS.md"
        agents.write_text(
            agents.read_text(encoding="utf-8") + f"\n{FORBIDDEN_HANDOFF}\n",
            encoding="utf-8",
        )
        errors = validate(root)
        self.assertTrue(
            any(FORBIDDEN_HANDOFF in error for error in errors),
            f"expected rejection of {FORBIDDEN_HANDOFF} in AGENTS.md, got: {errors}",
        )

    def test_rejects_handoff_in_read_order_md(self) -> None:
        root = self._root_with_contract()
        path = root / "docs/agent-policy/DOCUMENTATION_READ_ORDER.md"
        path.write_text(
            path.read_text(encoding="utf-8") + f"\n{FORBIDDEN_HANDOFF}\n",
            encoding="utf-8",
        )
        errors = validate(root)
        self.assertTrue(
            any(FORBIDDEN_HANDOFF in error for error in errors),
            f"expected rejection of {FORBIDDEN_HANDOFF} in DOCUMENTATION_READ_ORDER.md, got: {errors}",
        )

    def test_rejects_handoff_in_new_project_bootstrap_md(self) -> None:
        root = self._root_with_contract()
        path = root / "docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md"
        path.write_text(
            path.read_text(encoding="utf-8") + f"\n{FORBIDDEN_HANDOFF}\n",
            encoding="utf-8",
        )
        errors = validate(root)
        self.assertTrue(
            any(FORBIDDEN_HANDOFF in error for error in errors),
            f"expected rejection of {FORBIDDEN_HANDOFF} in NEW_PROJECT_BOOTSTRAP.md, got: {errors}",
        )

    # -- Markdown backticked id parity ---------------------------------

    def test_rejects_agents_md_missing_backticked_sc_id(self) -> None:
        root = self._root_with_contract()
        _write_human_policies(root, sc_ids=SC_IDS[:5])  # missing SC-06
        errors = validate(root)
        self.assertTrue(
            any("SC-06" in error for error in errors),
            f"expected rejection for missing backticked SC-06 in AGENTS.md, got: {errors}",
        )

    def test_rejects_read_order_md_extra_backticked_trigger(self) -> None:
        root = self._root_with_contract()
        _write_human_policies(root, trigger_ids=TRIGGER_IDS + ["extra_trigger"])
        errors = validate(root)
        self.assertTrue(
            any("extra_trigger" in error for error in errors),
            f"expected rejection for extra backticked trigger in DOCUMENTATION_READ_ORDER.md, got: {errors}",
        )

    # -- forbidden phrase ----------------------------------------------

    def test_rejects_hardcoded_read_sequence_phrase(self) -> None:
        root = self._root_with_contract()
        path = root / "AGENTS.md"
        path.write_text(
            path.read_text(encoding="utf-8") + f"\n{FORBIDDEN_PHRASE}\n",
            encoding="utf-8",
        )
        errors = validate(root)
        self.assertTrue(
            any(FORBIDDEN_PHRASE in error for error in errors),
            f"expected rejection of forbidden phrase, got: {errors}",
        )

    # -- Blueprint/Context are required under architecture_governance,
    #    not as unconditional startup ---------------------------

    def test_blueprint_and_context_are_triggered_not_baseline(self) -> None:
        contract = _make_valid_contract()
        read_order = contract["read_order"]
        self.assertEqual(read_order["mandatory_authority_baseline"], BASELINE)
        architecture = next(
            trigger
            for trigger in read_order["task_triggers"]
            if trigger["id"] == "architecture_governance"
        )
        self.assertEqual(
            architecture["documents"][:2], ["BLUEPRINT.md", "CONTEXT_BLOCK.md"]
        )
        self.assertEqual(validate(self._root_with_contract(contract)), [])


if __name__ == "__main__":
    unittest.main()
