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


class CurrentDocumentationValidatorTests(unittest.TestCase):
    def _root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        baseline = (
            "AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION\n"
            "v0.2.4 exact-installed; Bifrost v2.0.0 recertification pending\n"
            "AgentCore-PostgreSQL18 pool identity\n"
            "live direct-API and signed-gateway isolation canaries passed\n"
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
            "| Eigent | profile | unsupported | disabled unverified no approved secure credential route |\n"
            "| Zed | profile | unsupported | disabled unverified no approved secure credential route |\n"
            "| ZCode | contract | direct | enabled 18082 process-attested distinct from Zoo-Code |\n"
            "| OpenCode | pending | unsupported | disabled unverified legacy drift |\n"
            "| Cherry Studio | profile | unsupported | disabled unsupported_with_reason historical evidence |\n"
            "| Antigravity | profile | generated | enabled 18082 process-attested validated 2026-09-08 |\n"
            "| Open Interpreter **CLI** | profile | generated | enabled 8080 bearer_token_env_var no credential is stored |\n"
            "| Open Interpreter **GUI** (`Interpreter.exe`) | profile | generated | enabled 18082 process-attested fresh in-app acceptance pending |\n"
            "| OpenClaw | profile | manual | enabled dedicated direct BIFROST_MCP_VK_OPENCLAW live activation and lifecycle remain unverified |\n"
            "| ClawX | host | unverified | no ClawX-native MCP configuration |\n"
            "| Claude Desktop | profile | unsupported | disabled unverified historical drift |\n"
            "| MiniMax Agent Classic | profile | unsupported | disabled unverified Do not create a cloud custom-MCP entry |\n"
            "If you are Open Interpreter, identify whether you are the CLI or the desktop GUI\n"
            "gateway_auth_mode` is `unverified`\n"
            "Open Interpreter GUI uses process-attested `:18082`\n"
            "- Cherry Studio's July 2026 proof is historical credential-bearing evidence; current status is disabled / `unverified`; do not enroll, re-enroll, or materialize.\n"
        )
        for relative in CURRENT_DOCS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(baseline, encoding="utf-8")
        for relative, marker in CLASSIFIED_EVIDENCE.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {marker}\n", encoding="utf-8")

        hints = {
            "zed": {"enabled": False, "gateway_auth_mode": "unverified"},
            "eigent": {"enabled": False, "gateway_auth_mode": "unverified"},
            "zcode": {"enabled": True, "gateway_auth_mode": "process_attested_proxy", "gateway_url": "http://127.0.0.1:18082/mcp"},
            "opencode": {"enabled": False, "gateway_auth_mode": "unverified"},
            "cherry-studio": {"enabled": False, "gateway_auth_mode": "unverified"},
            "antigravity": {"enabled": True, "gateway_auth_mode": "process_attested_proxy", "gateway_url": "http://127.0.0.1:18082/mcp"},
            "open-interpreter": {"enabled": True, "gateway_auth_mode": "process_attested_proxy", "gateway_url": "http://127.0.0.1:18082/mcp"},
            "openclaw": {"enabled": True},
            "clawx": {"enabled": False},
            "claude-desktop": {"enabled": False, "gateway_auth_mode": "unverified"},
            "minimax-classic": {"enabled": False, "gateway_auth_mode": "unverified"},
        }
        contract = root / "contracts/agentcore-gateway-client.json"
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text(json.dumps({"client_render_hints": hints}), encoding="utf-8")

        matrix = root / "ide-profiles/IDE_CAPABILITY_MATRIX.yaml"
        matrix.parent.mkdir(parents=True, exist_ok=True)
        matrix.write_text(
            "managed_ides:\n"
            "  zed:\n    m8_enrollment: unsupported_with_reason\n"
            "  eigent:\n    m8_enrollment: unsupported_with_reason\n"
            "  zcode:\n    certification: configured_restart_required\n    gateway_url: http://127.0.0.1:18082/mcp\n    gateway_auth_mode: process_attested_proxy\n"
            "  opencode:\n    certification: unsupported_with_reason\n"
            "  cherry-studio:\n    m8_enrollment: unsupported_with_reason\n"
            "  antigravity:\n    last_validated: '2026-09-08'\n    gateway_url: http://127.0.0.1:18082/mcp\n    gateway_auth_mode: process_attested_proxy\n"
            "  open-interpreter:\n    last_validated: '2026-09-08'\n    gateway_url: http://127.0.0.1:8080/mcp\n    gateway_auth_mode: bearer_env\n    gui_gateway_url: http://127.0.0.1:18082/mcp\n    gui_gateway_auth_mode: process_attested_proxy\n"
            "  openclaw:\n    certification: configured_restart_required\n    gateway_url: http://127.0.0.1:8080/mcp\n    gateway_auth_mode: dedicated_bearer_env\n    capability_profile: openclaw\n"
            "  clawx:\n    certification: unverified\n"
            "  claude-desktop:\n    m8_enrollment: unsupported_with_reason\n"
            "  minimax-classic:\n    m8_enrollment: unsupported_with_reason\n",
            encoding="utf-8",
        )

        profile = root / "ide-profiles/open-interpreter/IDE_PROFILE.yaml"
        profile.parent.mkdir(parents=True, exist_ok=True)
        profile.write_text(
            "display_name: Open Interpreter (CLI)\n"
            "gui_display_name: Open Interpreter desktop GUI\n"
            "live_mcp_config_target: C:\\Users\\ynotf\\.openinterpreter\\config.toml\n"
            "live_gui_mcp_config_target: C:\\Users\\ynotf\\AppData\\Roaming\\interpreter\\config.json\n"
            "gateway_url: http://127.0.0.1:8080/mcp\n"
            "gateway_auth_mode: bearer_env\n"
            "classification: superseded_historical_evidence\n"
            "current_resolution: GUI uses process-attested :18082 with no stored bearer\n",
            encoding="utf-8",
        )

        setup = root / "docs/bifrost/UNIFIED_GATEWAY_SETUP.md"
        setup.parent.mkdir(parents=True, exist_ok=True)
        setup.write_text(
            "scripts\\.venv\\Scripts\\python.exe scripts/bifrost/render_bifrost_config.py\n"
            "### D. Require a named inventory before activation\n"
            "Existing wildcard placeholders are allowed only on disabled or dormant entries\n"
            '- Mutable live posture: `CONTEXT_BLOCK.md` §0 ("Current posture")\n',
            encoding="utf-8",
        )
        return root

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

    def test_rejects_superseded_open_interpreter_gui_hard_stop(self) -> None:
        root = self._root()
        path = root / "MASTER_CONFIG_AND_PROMPT.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\nIf you are Open Interpreter GUI, stop with unsupported_with_reason.\n",
            encoding="utf-8",
        )
        self.assertTrue(any("Open Interpreter GUI hard-stop" in error for error in validate(root)))

    def test_rejects_enabled_zcode_matrix_route_drift(self) -> None:
        root = self._root()
        path = root / "ide-profiles/IDE_CAPABILITY_MATRIX.yaml"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "certification: configured_restart_required",
                "certification: unverified",
                1,
            ),
            encoding="utf-8",
        )
        self.assertTrue(any("matrix drift for zcode" in error for error in validate(root)))


if __name__ == "__main__":
    unittest.main()
