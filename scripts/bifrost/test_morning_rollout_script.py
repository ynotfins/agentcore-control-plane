from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops" / "bifrost" / "Invoke-AgentCoreMorningRollout.ps1"


def test_morning_rollout_script_exists() -> None:
    assert SCRIPT.is_file()


def test_morning_rollout_script_parses() -> None:
    command = (
        "$errors=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{SCRIPT}', [ref]$null, [ref]$errors) | Out-Null; "
        "if ($errors.Count) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_morning_rollout_has_explicit_approval_switches() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "[switch]$ApproveCursorCleanup" in text
    assert "[switch]$ApproveBifrostRollout" in text
    assert "No live mutation was requested or performed." in text


def test_morning_rollout_mutating_phases_are_approval_guarded() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    cursor_block = re.search(
        r"if \(\$ApproveCursorCleanup\) \{(?P<body>.*?)\n\}",
        text,
        re.DOTALL,
    )
    bifrost_block = re.search(
        r"if \(\$ApproveBifrostRollout\) \{(?P<body>.*?)\n\}",
        text,
        re.DOTALL,
    )
    assert cursor_block, "Cursor cleanup block must be guarded"
    assert bifrost_block, "Bifrost rollout block must be guarded"
    assert "Invoke-AgentCoreIdeGatewayCutover.ps1" in cursor_block.group("body")
    assert "Install-AgentCoreBifrostGateway.ps1" in bifrost_block.group("body")
    assert "Start-AgentCoreBifrostGateway.ps1" in bifrost_block.group("body")


def test_morning_rollout_default_invocation_has_no_approval_flags() -> None:
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(SCRIPT), "-RepoRoot", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    # The current machine is expected to be NOT_READY before operator approvals.
    # This smoke proves the default path reaches the no-approval branch rather
    # than running cleanup/install actions.
    combined = result.stdout + result.stderr
    assert "No live mutation was requested or performed." in combined
    assert "To approve Cursor cleanup" in combined
    assert "To approve Bifrost live rollout" in combined


def test_morning_rollout_approved_paths_pass_arguments_as_single_parameter(tmp_path: Path) -> None:
    fake_repo = tmp_path / "repo"
    fake_ops = fake_repo / "ops" / "bifrost"
    fake_ops.mkdir(parents=True)

    scripts = {
        "Test-AgentCoreMorningReadiness.ps1": "Write-Host 'READY'; exit 0\n",
        "Invoke-AgentCoreIdeGatewayCutover.ps1": (
            "param([string]$RepoRoot,[string]$EvidenceRoot,[string[]]$Clients,[string]$CursorConfigPath)\n"
            "if ($Clients -ne 'cursor') { throw \"bad clients: $Clients\" }\n"
            "Write-Host \"CUTOVER:$($Clients):$CursorConfigPath\"; exit 0\n"
        ),
        "Test-AgentCoreBifrostGateway.ps1": "Write-Host 'GATEWAY_TEST'; exit 0\n",
        "Install-AgentCoreBifrostGateway.ps1": "param([string]$RuntimeRoot,[string]$RepoRoot) Write-Host \"INSTALL:$RuntimeRoot\"; exit 0\n",
        "Start-AgentCoreBifrostGateway.ps1": "param([string]$RuntimeRoot) Write-Host \"START:$RuntimeRoot\"; exit 0\n",
        "Get-BifrostStatus.ps1": "Write-Host 'STATUS'; exit 0\n",
    }
    for name, body in scripts.items():
        (fake_ops / name).write_text(body, encoding="utf-8")

    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(SCRIPT),
            "-RepoRoot",
            str(fake_repo),
            "-RuntimeRoot",
            str(tmp_path / "runtime"),
            "-CursorMcpPath",
            str(tmp_path / "mcp.json"),
            "-SkipInitialReadiness",
            "-ApproveCursorCleanup",
            "-ApproveBifrostRollout",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "CUTOVER:cursor:" in combined
    assert "INSTALL:" in combined
    assert "START:" in combined
    assert "AGENTCORE_MORNING_ROLLOUT_READY" in combined
