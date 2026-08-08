from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WATCHDOG = REPO_ROOT / "ops" / "bifrost" / "Invoke-AgentCoreBifrostWatchdog.ps1"
HARNESS = REPO_ROOT / "scripts" / "bifrost" / "acceptance_lifecycle_watchdog.py"


def run_watchdog(runtime_root: Path, health: str, started_at: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(WATCHDOG),
            "-RuntimeRoot",
            str(runtime_root),
            "-TestMode",
            "-TestHealthResult",
            health,
            "-GatewayStartedAtUtc",
            started_at,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_watchdog_debounces_failures_and_recycles_once_per_incident(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    started_at = "2000-01-01T00:00:00Z"

    first = run_watchdog(runtime_root, "Unhealthy", started_at)
    second = run_watchdog(runtime_root, "Unhealthy", started_at)
    third = run_watchdog(runtime_root, "Unhealthy", started_at)
    fourth = run_watchdog(runtime_root, "Unhealthy", started_at)

    assert first.returncode == 0, first.stderr
    assert "WATCHDOG_FAILURE count=1" in first.stdout
    assert "WATCHDOG_FAILURE count=2" in second.stdout
    assert "WATCHDOG_TEST_RECYCLE count=3" in third.stdout
    assert "WATCHDOG_RECYCLE_SUPPRESSED" in fourth.stdout

    state = json.loads((runtime_root / "state" / "bifrost-watchdog.json").read_text())
    assert state["consecutive_failures"] == 4
    assert state["recycle_attempted"] is True

    healthy = run_watchdog(runtime_root, "Healthy", started_at)
    assert healthy.returncode == 0, healthy.stderr
    assert "WATCHDOG_HEALTHY" in healthy.stdout
    assert json.loads((runtime_root / "state" / "bifrost-watchdog.json").read_text())["consecutive_failures"] == 0


def test_watchdog_skips_during_maintenance_and_startup_grace(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    marker = runtime_root / "state" / "bifrost-maintenance.marker"
    marker.parent.mkdir(parents=True)
    marker.write_text("planned maintenance", encoding="utf-8")

    maintenance = run_watchdog(runtime_root, "Unhealthy", "2000-01-01T00:00:00Z")
    assert maintenance.returncode == 0, maintenance.stderr
    assert "WATCHDOG_SKIP maintenance_marker" in maintenance.stdout
    assert not (runtime_root / "state" / "bifrost-watchdog.json").exists()

    marker.unlink()
    startup = run_watchdog(runtime_root, "Unhealthy", "2999-01-01T00:00:00Z")
    assert startup.returncode == 0, startup.stderr
    assert "WATCHDOG_SKIP startup_grace" in startup.stdout
    assert not (runtime_root / "state" / "bifrost-watchdog.json").exists()


def test_watchdog_lifecycle_wiring_and_acceptance_harness_are_present() -> None:
    watchdog = WATCHDOG.read_text(encoding="utf-8")
    installer = (REPO_ROOT / "ops" / "bifrost" / "Install-AgentCoreBifrostGateway.ps1").read_text(encoding="utf-8")
    launcher = (REPO_ROOT / "ops" / "bifrost" / "Launch-AgentCoreBifrostGateway.ps1").read_text(encoding="utf-8")
    starter = (REPO_ROOT / "ops" / "bifrost" / "Start-AgentCoreBifrostGateway.ps1").read_text(encoding="utf-8")
    stopper = (REPO_ROOT / "ops" / "bifrost" / "Stop-AgentCoreBifrostGateway.ps1").read_text(encoding="utf-8")
    status = (REPO_ROOT / "ops" / "bifrost" / "Get-BifrostStatus.ps1").read_text(encoding="utf-8")

    assert "Stop-ScheduledTask" in watchdog
    assert "Start-ScheduledTask" in watchdog
    assert "WATCHDOG_RECYCLE" in watchdog
    assert "AgentCore-Bifrost-Watchdog" in installer
    assert "-MultipleInstances IgnoreNew" in installer
    assert "Microsoft-Windows-TaskScheduler/Operational" in installer
    assert "-RestartCount 0" in installer
    assert "while ($true)" not in launcher
    assert "bifrost-maintenance.marker" in starter
    assert "bifrost-maintenance.marker" in stopper
    assert "bifrost-maintenance.marker" in status
    assert HARNESS.is_file()
