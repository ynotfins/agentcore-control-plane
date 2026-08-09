from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops" / "bifrost" / "New-AgentCoreRestorePointReport.ps1"


def test_restore_point_report_script_exists() -> None:
    assert SCRIPT.is_file()


def test_restore_point_report_script_parses() -> None:
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


def test_restore_point_report_has_required_closeout_fields() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    required = [
        "Git HEAD",
        "Morning readiness status",
        "Bifrost config hashes",
        "Scheduled tasks",
        "Sally full Swarm acceptance",
        "LangGraph production canary",
        "SwarmClaw autonomous canary",
        "Do not treat this restore point as production-ready",
    ]
    for marker in required:
        assert marker in text


def test_restore_point_report_does_not_write_without_outfile(tmp_path: Path) -> None:
    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(SCRIPT),
            "-RepoRoot",
            str(REPO_ROOT),
            "-RuntimeRoot",
            str(tmp_path / "missing-runtime"),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "# AgentCore Runtime Restore-Point Report" in result.stdout
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    assert len(list(tmp_path.iterdir())) == 1


def test_restore_point_report_secret_scan_static() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    patterns = [
        r"sk-[A-Za-z0-9_-]{20,}",
        r"MEILI_MASTER_KEY\s*[:=]",
        r"SWARMRECALL_API_KEY\s*[:=]",
        r"AGENTCORE_RECALL_API_KEY\s*[:=]",
    ]
    for pattern in patterns:
        assert re.search(pattern, text) is None
