from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops" / "bifrost" / "Test-AgentCoreMorningReadiness.ps1"


def test_morning_readiness_script_exists() -> None:
    assert SCRIPT.is_file()


def test_morning_readiness_script_parses() -> None:
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


def test_morning_readiness_script_is_read_only_by_static_policy() -> None:
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


def test_morning_readiness_script_covers_current_approval_gates() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    required_markers = [
        "cursor_global_mcp",
        "bifrost_config_drift",
        "AgentCore-Bifrost-Watchdog",
        "swarmrecall_api_health",
        "meilisearch_health",
        "swarmclaw_health",
        "langgraph_topology",
        "a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32",
    ]
    for marker in required_markers:
        assert marker in text
