from __future__ import annotations

import json
import os
import subprocess
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WATCHDOG = REPO_ROOT / "ops" / "bifrost" / "Invoke-AgentCoreBifrostWatchdog.ps1"
HARNESS = REPO_ROOT / "scripts" / "bifrost" / "acceptance_lifecycle_watchdog.py"


@contextmanager
def gateway_stub(mcp_body: str):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(mcp_body.encode("utf-8"))

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        thread.join()


def run_start_against_stub(runtime_root: Path, port: int) -> subprocess.CompletedProcess[str]:
    binary = runtime_root / "bin" / "bifrost-http.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"")
    environment = os.environ | {"BIFROST_MCP_VIRTUAL_KEY": "test-key"}
    return subprocess.run(
        [
            "pwsh", "-NoProfile", "-File",
            str(REPO_ROOT / "ops" / "bifrost" / "Start-AgentCoreBifrostGateway.ps1"),
            "-RuntimeRoot", str(runtime_root), "-HostAddress", "127.0.0.1", "-Port", str(port), "-ProbeOnly",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


def run_watchdog(
    runtime_root: Path, health: str, started_at: str, *extra_args: str
) -> subprocess.CompletedProcess[str]:
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
            *extra_args,
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


def test_watchdog_expires_stale_maintenance_marker_and_honors_exact_120_second_grace(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    marker = runtime_root / "state" / "bifrost-maintenance.marker"
    marker.parent.mkdir(parents=True)
    marker.write_text("planned maintenance", encoding="utf-8")
    created_at = datetime(2026, 8, 8, tzinfo=timezone.utc).timestamp()
    os.utime(marker, (created_at, created_at))
    stale = run_watchdog(
        runtime_root,
        "Unhealthy",
        "2000-01-01T00:00:00Z",
        "-NowUtc",
        "2026-08-08T00:10:00Z",
        "-MaintenanceMarkerTtlSeconds",
        "60",
    )
    assert stale.returncode == 0, stale.stderr
    assert "WATCHDOG_STALE_MARKER_REMOVED age_seconds=600" in stale.stdout
    assert "WATCHDOG_FAILURE count=1" in stale.stdout
    assert not marker.exists()

    at_119 = run_watchdog(
        tmp_path / "grace-119",
        "Unhealthy",
        "2026-08-08T00:00:00Z",
        "-NowUtc",
        "2026-08-08T00:01:59Z",
    )
    at_120 = run_watchdog(
        tmp_path / "grace-120",
        "Unhealthy",
        "2026-08-08T00:00:00Z",
        "-NowUtc",
        "2026-08-08T00:02:00Z",
    )
    assert "WATCHDOG_SKIP startup_grace" in at_119.stdout
    assert "WATCHDOG_FAILURE count=1" in at_120.stdout

    marker.write_text("planned maintenance", encoding="utf-8")
    os.utime(marker, (created_at, created_at))
    status = subprocess.run(
        [
            "pwsh", "-NoProfile", "-File",
            str(REPO_ROOT / "ops" / "bifrost" / "Get-BifrostStatus.ps1"),
            "-RuntimeRoot", str(runtime_root),
            "-GatewayUrl", "http://127.0.0.1:1",
            "-TaskName", "missing-watchdog-test-task",
            "-MaintenanceMarkerTtlSeconds", "60",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert status.returncode == 1
    assert "maintenance_marker: present=True; age_seconds=" in status.stdout
    assert "expired=True" in status.stdout


def test_watchdog_rechecks_maintenance_and_persists_recycle_failure(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    started_at = "2000-01-01T00:00:00Z"
    for _ in range(2):
        assert run_watchdog(runtime_root, "Unhealthy", started_at).returncode == 0

    before_stop = run_watchdog(
        runtime_root, "Unhealthy", started_at, "-TestRecycleOutcome", "BeforeStopMarker"
    )
    assert before_stop.returncode == 0, before_stop.stderr
    assert "WATCHDOG_RECYCLE_SKIPPED maintenance_marker_before_stop" in before_stop.stdout
    state = json.loads((runtime_root / "state" / "bifrost-watchdog.json").read_text())
    assert state["last_recycle_outcome"] == "maintenance_marker_before_stop"
    assert state["recycle_attempted"] is False

    resumed = run_watchdog(runtime_root, "Unhealthy", started_at)
    assert resumed.returncode == 0, resumed.stderr
    assert "WATCHDOG_TEST_RECYCLE count=4" in resumed.stdout

    healthy = run_watchdog(runtime_root, "Healthy", started_at)
    assert healthy.returncode == 0
    for _ in range(2):
        assert run_watchdog(runtime_root, "Unhealthy", started_at).returncode == 0
    before_restart = run_watchdog(
        runtime_root, "Unhealthy", started_at, "-TestRecycleOutcome", "BeforeRestartMarker"
    )
    assert before_restart.returncode == 0, before_restart.stderr
    assert "WATCHDOG_RECYCLE_SKIPPED maintenance_marker_before_restart" in before_restart.stdout

    healthy = run_watchdog(runtime_root, "Healthy", started_at)
    assert healthy.returncode == 0
    for _ in range(2):
        assert run_watchdog(runtime_root, "Unhealthy", started_at).returncode == 0
    start_failed = run_watchdog(
        runtime_root, "Unhealthy", started_at, "-TestRecycleOutcome", "StartFailure"
    )
    assert start_failed.returncode == 1
    assert "WATCHDOG_RECYCLE_START_FAILED" in start_failed.stdout
    state = json.loads((runtime_root / "state" / "bifrost-watchdog.json").read_text())
    assert state["last_recycle_outcome"] == "start_failed"
    suppressed_failure = run_watchdog(runtime_root, "Unhealthy", started_at)
    assert suppressed_failure.returncode == 1
    assert "WATCHDOG_RECYCLE_SUPPRESSED" in suppressed_failure.stdout
    assert "outcome=start_failed" in suppressed_failure.stdout


def test_start_preflight_and_authenticated_health_do_not_clear_marker_early(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    start = REPO_ROOT / "ops" / "bifrost" / "Start-AgentCoreBifrostGateway.ps1"
    preflight = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(start), "-RuntimeRoot", str(runtime_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert preflight.returncode != 0
    assert not (runtime_root / "state" / "bifrost-maintenance.marker").exists()

    unauthenticated = subprocess.run(
        [
            "pwsh", "-NoProfile", "-File", str(start), "-RuntimeRoot", str(runtime_root),
            "-TestMode", "-TestReadiness", "Unauthenticated",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert unauthenticated.returncode != 0
    marker = runtime_root / "state" / "bifrost-maintenance.marker"
    assert marker.exists()

    authenticated = subprocess.run(
        [
            "pwsh", "-NoProfile", "-File", str(start), "-RuntimeRoot", str(runtime_root),
            "-TestMode", "-TestReadiness", "Authenticated",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert authenticated.returncode == 0, authenticated.stderr
    assert not marker.exists()


def test_start_requires_successful_mcp_initialize_response_body(tmp_path: Path) -> None:
    valid_result = '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18"}}'
    rpc_error = '{"jsonrpc":"2.0","id":1,"error":{"code":-32000,"message":"denied"}}'
    for name, payload, expected_code in (
        ("valid", valid_result, 0),
        ("rpc-error", rpc_error, 1),
        ("malformed", "not-json", 1),
    ):
        runtime_root = tmp_path / name
        with gateway_stub(payload) as port:
            result = run_start_against_stub(runtime_root, port)
        marker = runtime_root / "state" / "bifrost-maintenance.marker"
        assert result.returncode == expected_code, result.stderr
        assert marker.exists() is (expected_code == 1)


def test_installer_transaction_rolls_back_and_fails_closed() -> None:
    installer = REPO_ROOT / "ops" / "bifrost" / "Install-AgentCoreBifrostGateway.ps1"
    denied = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(installer), "-TestMode", "-TestPrivilegeDenied"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert denied.returncode != 0
    assert "INSTALL_PRIVILEGE_PREFLIGHT_FAILED" in denied.stderr

    export_failure = subprocess.run(
        [
            "pwsh", "-NoProfile", "-File", str(installer), "-TestMode",
            "-TestGatewayTaskModel", "ExportFailure",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert export_failure.returncode != 0
    assert "INSTALL_TASK_BACKUP_FAILED AgentCore-Bifrost-Gateway" in export_failure.stderr
    assert "gateway-original" in export_failure.stdout

    for phase in ("WatchdogRegistration", "OperationalLogEnablement"):
        partial = subprocess.run(
            [
                "pwsh", "-NoProfile", "-File", str(installer), "-TestMode",
                "-TestFailurePhase", phase,
                "-TestGatewayTaskModel", "Present",
                "-TestWatchdogTaskModel", "Present",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert partial.returncode != 0
        task_model = json.loads(partial.stdout.split("INSTALL_TASK_MODEL ")[-1])
        assert task_model == {"gateway": "gateway-original", "watchdog": "watchdog-original"}

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
    assert "-RestartCount 1" in installer
    assert "while ($true)" not in launcher
    assert "bifrost-maintenance.marker" in starter
    assert "bifrost-maintenance.marker" in stopper
    assert "bifrost-maintenance.marker" in status
    assert HARNESS.is_file()
