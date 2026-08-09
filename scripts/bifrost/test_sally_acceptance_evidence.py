from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops" / "bifrost" / "Test-SallyAcceptanceEvidence.ps1"
TEMPLATE = (
    REPO_ROOT
    / "docs"
    / "templates"
    / "SALLY_FULL_SWARM_ACCEPTANCE_REPORT_TEMPLATE_2026-08-09.md"
)


def run_validator(report: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(SCRIPT), "-Path", str(report)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_sally_acceptance_script_exists() -> None:
    assert SCRIPT.is_file()


def test_sally_acceptance_template_exists() -> None:
    assert TEMPLATE.is_file()


def test_sally_acceptance_script_parses() -> None:
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


def test_sally_acceptance_full_report_passes(tmp_path: Path) -> None:
    report = tmp_path / "sally-acceptance.md"
    report.write_text(
        """
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
""",
        encoding="utf-8",
    )
    result = run_validator(report)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SALLY_ACCEPTANCE_EVIDENCE" not in result.stdout
    assert "SUMMARY status=READY" in result.stdout


def test_sally_acceptance_template_satisfies_structural_gate() -> None:
    result = run_validator(TEMPLATE)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SUMMARY status=READY" in result.stdout


def test_sally_acceptance_orchestrator_ok_only_fails(tmp_path: Path) -> None:
    report = tmp_path / "health-only.md"
    report.write_text("ORCHESTRATOR_OK", encoding="utf-8")
    result = run_validator(report)
    assert result.returncode != 0
    assert "ORCHESTRATOR_OK alone is health evidence" in result.stdout
    assert "SUMMARY status=NOT_READY" in result.stdout


def test_sally_acceptance_missing_swarmvault_fails(tmp_path: Path) -> None:
    report = tmp_path / "missing-vault.md"
    report.write_text(
        """
Timestamp: 2026-08-09
Final status: PASS
SwarmClaw version v1.9.39
SwarmRecall version v0.3.0
SwarmVault version v3.20.0
H:\\SwarmData H:\\SwarmRuntime E:\\SwarmBackups
Services: SwarmClaw SwarmRecall SwarmVault Meilisearch PostgreSQL listener
SwarmRecall canary write read search exact match
Autonomous team canary Builder task result review completed
No writes to AgentCore Bifrost LangGraph IDE configs
Exact files changed: none
Files intentionally not touched: AgentCore Bifrost LangGraph IDE
Backup path E:\\SwarmBackups\\acceptance files readable
""",
        encoding="utf-8",
    )
    result = run_validator(report)
    assert result.returncode != 0
    assert "swarmvault_canary" in result.stdout
    assert "SUMMARY status=NOT_READY" in result.stdout


def test_sally_acceptance_secret_literal_fails(tmp_path: Path) -> None:
    report = tmp_path / "secret.md"
    report.write_text(
        """
Timestamp: 2026-08-09
Final status: PASS
SwarmClaw version v1.9.39
SwarmRecall version v0.3.0
SwarmVault version v3.20.0
H:\\SwarmData H:\\SwarmRuntime E:\\SwarmBackups
Services: SwarmClaw SwarmRecall SwarmVault Meilisearch PostgreSQL listener
SwarmRecall canary write read search exact match
SwarmVault search context-pack corpus source count
Autonomous team canary Builder task result review completed
No writes to AgentCore Bifrost LangGraph IDE configs
Exact files changed: none
Files intentionally not touched: AgentCore Bifrost LangGraph IDE
Backup path E:\\SwarmBackups\\acceptance files readable
SWARMRECALL_API_KEY=do-not-put-secrets-here
""",
        encoding="utf-8",
    )
    result = run_validator(report)
    assert result.returncode != 0
    assert "secret_scan" in result.stdout
    assert "SUMMARY status=NOT_READY" in result.stdout


def test_sally_acceptance_script_is_read_only_by_static_policy() -> None:
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
        assert token not in text
