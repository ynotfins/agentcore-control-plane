from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
INSTALLER = REPO / "ops" / "bifrost" / "Install-AgentCoreResearchMcp.ps1"
PWSH = Path(r"C:\Program Files\PowerShell\7\pwsh.exe")


class ResearchMcpInstallerTests(unittest.TestCase):
    def test_powershell_parses(self) -> None:
        command = (
            "$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile("
            f"'{INSTALLER}',[ref]$null,[ref]$e); if($e.Count){{"
            "$e | ForEach-Object { Write-Error $_.Message }; exit 1 }"
        )
        result = subprocess.run(
            [str(PWSH), "-NoProfile", "-NonInteractive", "-Command", command],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_dry_run_validates_without_writing_runtime(self) -> None:
        result = subprocess.run(
            [
                str(PWSH),
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(INSTALLER),
                "-DryRun",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("dry_run_passed", payload["status"])
        self.assertEqual("v24.16.0", payload["node_version"])
        self.assertEqual(0, payload["provider_calls"])
        self.assertIn("--ignore-scripts", payload["install_command"])
        self.assertNotIn("npx", payload["install_command"])
        self.assertNotIn("@brightdata/mcp", payload["packages"])

    def test_installer_enforces_atomic_staging_and_no_native_addons(self) -> None:
        source = INSTALLER.read_text(encoding="utf-8")
        self.assertIn(".staging-$transactionId", source)
        self.assertIn(".rollback-$transactionId", source)
        self.assertIn("Copy-Item -LiteralPath $RuntimeRoot", source)
        self.assertIn("Move-Item -LiteralPath $stagingRoot -Destination $RuntimeRoot", source)
        self.assertIn("--omit=dev --ignore-scripts --no-audit --no-fund", source)
        self.assertIn("-Filter '*.node'", source)
        self.assertIn("Assert-ToolInventories $stagingRoot", source)
        self.assertIn("RESEARCH_MCP_TOOL_INVENTORY_MISMATCH", source)
        self.assertIn("provider_calls = 0", source)


if __name__ == "__main__":
    unittest.main()
