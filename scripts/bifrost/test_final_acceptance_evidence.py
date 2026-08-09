from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops" / "bifrost" / "Test-AgentCoreFinalAcceptanceEvidence.ps1"


SALLY_PASSING_REPORT = """
# Swarm Production Acceptance

Timestamp: 2026-08-09T08:00:00-04:00
Final status: PASS

Versions:
- SwarmClaw version v1.9.39
- SwarmRecall version v0.3.0
- SwarmVault version v3.20.0

Storage roots:
- H:\\SwarmData
- H:\\SwarmRuntime
- E:\\SwarmBackups

Service table and endpoints:
- SwarmClaw API healthy
- SwarmRecall API healthy
- SwarmVault API healthy
- Meilisearch healthy
- PostgreSQL listener 65432 healthy

SwarmRecall canary:
- canary id abc-123
- write POST succeeded
- read GET succeeded
- search returned exact match

SwarmVault canary:
- search succeeded
- context-pack returned 3917 tokens
- corpus source count 2466 sources

Autonomous team canary:
- Builder created task
- QA reviewed result
- Reviewer completed acceptance

No-cross-write boundary:
- no writes to AgentCore
- no writes to Bifrost
- no writes to LangGraph
- no writes to IDE configs

Exact files changed:
- D:\\github\\swarm-ecosystem-control\\audits\\SWARM_ACCEPTANCE.md

Files intentionally not touched:
- AgentCore, Bifrost, LangGraph, and IDE configs

Backup / restore point:
- path E:\\SwarmBackups\\acceptance-20260809
- files verified readable
"""


def write_evidence_files(tmp_path: Path, *, sally_text: str = SALLY_PASSING_REPORT):
    sally = tmp_path / "sally.md"
    langgraph = tmp_path / "langgraph.json"
    swarmclaw = tmp_path / "swarmclaw.md"
    sally.write_text(sally_text, encoding="utf-8")
    langgraph.write_text('{"status":"PASS","run_id":"lg-canary"}', encoding="utf-8")
    swarmclaw.write_text("Final status: PASS\nSwarmClaw autonomous canary complete\n", encoding="utf-8")
    return sally, langgraph, swarmclaw


def run_preflight(
    sally: Path, langgraph: Path, swarmclaw: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(SCRIPT),
            "-RepoRoot",
            str(REPO_ROOT),
            "-SallyAcceptancePath",
            str(sally),
            "-LangGraphCanaryPath",
            str(langgraph),
            "-SwarmClawCanaryPath",
            str(swarmclaw),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_final_acceptance_evidence_script_exists() -> None:
    assert SCRIPT.is_file()


def test_final_acceptance_evidence_script_parses() -> None:
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


def test_final_acceptance_evidence_passes_with_three_valid_files(tmp_path: Path) -> None:
    sally, langgraph, swarmclaw = write_evidence_files(tmp_path)
    result = run_preflight(sally, langgraph, swarmclaw)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "sally_structural_gate: READY" in result.stdout
    assert "SUMMARY status=READY" in result.stdout


def test_final_acceptance_evidence_fails_when_langgraph_missing(tmp_path: Path) -> None:
    sally, langgraph, swarmclaw = write_evidence_files(tmp_path)
    langgraph.unlink()
    result = run_preflight(sally, langgraph, swarmclaw)
    assert result.returncode != 0
    assert "langgraph_canary_file" in result.stdout
    assert "SUMMARY status=NOT_READY" in result.stdout


def test_final_acceptance_evidence_fails_when_sally_structural_gate_fails(tmp_path: Path) -> None:
    sally, langgraph, swarmclaw = write_evidence_files(tmp_path, sally_text="ORCHESTRATOR_OK")
    result = run_preflight(sally, langgraph, swarmclaw)
    assert result.returncode != 0
    assert "sally_structural_gate" in result.stdout
    assert "SUMMARY status=NOT_READY" in result.stdout


def test_final_acceptance_evidence_fails_on_secret_literal(tmp_path: Path) -> None:
    sally, langgraph, swarmclaw = write_evidence_files(tmp_path)
    token = "Bearer " + "abcdefghijklmnopqrstuvwxyz" + "1234567890"
    swarmclaw.write_text(token + "\n", encoding="utf-8")
    result = run_preflight(sally, langgraph, swarmclaw)
    assert result.returncode != 0
    assert "swarmclaw_canary_file_secret_scan" in result.stdout
    assert "SUMMARY status=NOT_READY" in result.stdout


def test_final_acceptance_evidence_script_is_read_only_by_static_policy() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = [
        "Set-Content",
        "Add-Content",
        "Out-File",
        "New-Item",
        "Remove-Item",
        "Copy-Item",
        "Move-Item",
        "Set-ItemProperty",
        "New-ScheduledTask",
        "Register-ScheduledTask",
        "Unregister-ScheduledTask",
        "Start-ScheduledTask",
        "Stop-ScheduledTask",
        "Start-Process",
        "Stop-Process",
        "Invoke-Sqlcmd",
        "psql",
    ]
    for token in forbidden:
        assert re.search(rf"(?<![A-Za-z0-9_-]){re.escape(token)}(?![A-Za-z0-9_-])", text) is None
