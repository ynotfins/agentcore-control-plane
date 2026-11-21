from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from validate_current_documentation import GATEWAY_GUIDE, validate_gateway_guide

VALID_GUIDE = """# AgentCore Gateway and Bifrost Developer Guide
> Subordinate developer guide. This file is not architecture authority.
Read PROJECT_ANCHOR.md, DOC_AUTHORITY.md, BLUEPRINT.md, and CONTEXT_BLOCK.md.
The contracts are [registry](contracts/bifrost-upstream-mcp-registry.json) and
[client](contracts/agentcore-gateway-client.json).
Structured output uses contracts/mcp-tool-output-schemas.json.
The MCP plane and inference plane are separate; MCP health does not prove inference routing.
Resolve http://127.0.0.1:8080/mcp and http://127.0.0.1:18082/mcp from gateway_url
and gateway_auth_mode. The latter is process-attested.
Use Code Mode in order: listToolFiles, readToolFile or getToolDocs, then executeToolCode.
Project identity follows contracts/agentcore-project-enrollment.json.
agentcore-memory keeps PostgreSQL canonical and Recall a neutral semantic projection.
SwarmClaw remains separate. ZCode is distinct from Zoo-Code.
"""


class GatewayDeveloperGuideValidatorTests(unittest.TestCase):
    def _root(self, guide: str = VALID_GUIDE) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        for relative in (
            "contracts/bifrost-upstream-mcp-registry.json",
            "contracts/agentcore-gateway-client.json",
        ):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")
        (root / "contracts" / "bifrost-upstream-mcp-registry.json").write_text(
            json.dumps(
                {
                    "servers": {
                        "mcp-debugger": {
                            "enabled": False,
                            "status": "disabled",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        authority_lock = root / "contracts" / "authority-lock.yaml"
        authority_lock.write_text(
            "classes:\n"
            "  normal_workstream:\n"
            "    paths:\n"
            f"      - {GATEWAY_GUIDE}\n"
            "enforcement:\n"
            "  deny_direct_edit_without_capability: true\n",
            encoding="utf-8",
        )
        (root / "DOC_AUTHORITY.md").write_text(
            "## Authoritative — stable (safe to follow; change rarely, with approval)\n\n"
            "| File | Purpose |\n| --- | --- |\n"
            "| `PROJECT_ANCHOR.md` | Authority |\n\n"
            "## Subordinate developer navigation (procedural; not authority)\n\n"
            "| File | Purpose |\n| --- | --- |\n"
            f"| `{GATEWAY_GUIDE}` | Navigation |\n",
            encoding="utf-8",
        )
        migration = root / "docs" / "bifrost" / "MIGRATION_RUNBOOK.md"
        migration.parent.mkdir(parents=True, exist_ok=True)
        migration.write_text(
            "Backup-AgentCoreBifrostConfig.ps1 is a rendered-configuration backup helper only; "
            "not a complete runtime checkpoint.\n"
            "Ordinary rollback restores the last accepted Bifrost and client state. "
            "If gateway restoration fails, stop and report `agentcore-gateway` unavailable. "
            "A legacy direct baseline requires an explicit authority change and is never an ordinary rollback.\n",
            encoding="utf-8",
        )
        rollback = root / "docs" / "bifrost" / "ROLLBACK_RUNBOOK.md"
        rollback.write_text(
            "Restore and validate the last accepted Bifrost gateway and client state. "
            "If gateway restoration fails, stop and report `agentcore-gateway` unavailable. "
            "A legacy direct baseline requires an explicit authority change and is never an ordinary rollback.\n",
            encoding="utf-8",
        )
        (root / "docs" / "bifrost" / "UNIFIED_GATEWAY_SETUP.md").write_text(
            "Used today for disabled servers such as `mcp-debugger`.\n",
            encoding="utf-8",
        )
        (root / "docs" / "bifrost" / "CAPABILITY_PROFILES.md").write_text(
            "Disabled servers such as `mcp-debugger` require runtime health gates.\n",
            encoding="utf-8",
        )
        (root / GATEWAY_GUIDE).write_text(guide, encoding="utf-8")
        return root

    def test_accepts_complete_guide(self) -> None:
        self.assertEqual(validate_gateway_guide(self._root()), [])

    def test_rejects_broken_link_wrong_sequence_and_placeholder(self) -> None:
        guide = VALID_GUIDE.replace(
            "contracts/agentcore-gateway-client.json",
            "contracts/missing-client-contract.json",
        ).replace(
            "listToolFiles, readToolFile or getToolDocs, then executeToolCode",
            "executeToolCode, listToolFiles, readToolFile, getToolDocs",
        ) + "\nTODO\n"
        errors = validate_gateway_guide(self._root(guide))
        self.assertTrue(any("agentcore-gateway-client.json" in error for error in errors))
        self.assertTrue(any("missing repository-relative link" in error for error in errors))
        self.assertTrue(any("ordered Code Mode sequence" in error for error in errors))
        self.assertTrue(any("placeholder/corruption" in error for error in errors))

    def test_rejects_authority_and_migration_drift(self) -> None:
        root = self._root()
        (root / "contracts" / "authority-lock.yaml").write_text(
            "classes:\n  normal_workstream:\n    paths: []\n",
            encoding="utf-8",
        )
        authority = root / "DOC_AUTHORITY.md"
        authority.write_text(
            "## Authoritative — stable (safe to follow; change rarely, with approval)\n\n"
            f"| `{GATEWAY_GUIDE}` | Wrong class |\n",
            encoding="utf-8",
        )
        (root / "docs" / "bifrost" / "MIGRATION_RUNBOOK.md").write_text(
            "v2.0.0-prerelease1 E:\\AgentCore-Backups\\ unless rolling back intentionally\n",
            encoding="utf-8",
        )
        (root / "docs" / "bifrost" / "ROLLBACK_RUNBOOK.md").write_text(
            "Optionally leave Bifrost stopped if returning to pre-gateway direct baselines.\n"
            "Do not paste unresolved upstream registries without calling it a rollback.\n",
            encoding="utf-8",
        )
        errors = validate_gateway_guide(root)
        self.assertTrue(any("normal_workstream" in error for error in errors))
        self.assertTrue(any("subordinate navigation" in error for error in errors))
        self.assertTrue(any("authoritative stable" in error for error in errors))
        self.assertTrue(any("stale prerelease" in error for error in errors))
        self.assertTrue(any("stale AgentCore backup root" in error for error in errors))
        self.assertTrue(any("config-only backup-helper limitation" in error for error in errors))
        self.assertTrue(any("legacy direct baseline as ordinary rollback" in error for error in errors))
        self.assertTrue(any("permissive legacy-direct wording" in error for error in errors))
        self.assertTrue(any("missing fail-closed rule" in error for error in errors))

    def test_rejects_server_example_missing_from_registry(self) -> None:
        root = self._root()
        (root / "contracts" / "bifrost-upstream-mcp-registry.json").write_text(
            '{"servers": {}}\n',
            encoding="utf-8",
        )
        capability_profiles = root / "docs" / "bifrost" / "CAPABILITY_PROFILES.md"
        capability_profiles.write_text(
            capability_profiles.read_text(encoding="utf-8")
            + "Disabled servers include `artiforge`.\n",
            encoding="utf-8",
        )
        errors = validate_gateway_guide(root)
        self.assertTrue(any("nonexistent registry server: artiforge" in error for error in errors))
        self.assertTrue(any("example missing from registry: mcp-debugger" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
