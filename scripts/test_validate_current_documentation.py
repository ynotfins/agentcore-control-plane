from __future__ import annotations

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


class CurrentDocumentationValidatorTests(unittest.TestCase):
    def _root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        baseline = (
            "AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION\n"
            "v0.2.1 release recertification pending\n"
            "AgentCore-PostgreSQL18 pool identity\n"
            "point-in-time Context Engine v0.2.0\n"
            "docs/operations/LANGFUSE_TRACING_AND_PROMPTS.md Inherited untracked WIP\n"
            "Milestone acceptance is point-in-time evidence\n"
            "Global `BLUEPRINT.md` and current `CONTEXT_BLOCK.md`\n"
            f"{REPO_PYTHON}\n"
            f"Set-Location '{SCRIPTS_CWD}'\n"
            "agentcore-gateway http://127.0.0.1:8080/mcp\n"
            "127.0.0.1:55433 neutral SwarmRecall Portable Context Engine\n"
        )
        for relative in CURRENT_DOCS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(baseline, encoding="utf-8")
        for relative, marker in CLASSIFIED_EVIDENCE.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {marker}\n", encoding="utf-8")
        return root

    def test_accepts_aligned_surface(self) -> None:
        self.assertEqual(validate(self._root()), [])

    def test_rejects_stale_context_engine_acceptance(self) -> None:
        root = self._root()
        path = root / "CONTEXT_BLOCK.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n110/110 tests\n", encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
