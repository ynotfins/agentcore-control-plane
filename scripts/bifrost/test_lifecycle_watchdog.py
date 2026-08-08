from __future__ import annotations

import json
import os
import subprocess
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
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
            content_type = (
                "text/event-stream" if mcp_body.startswith("event:") else "application/json"
            )
            self.send_header("Content-Type", content_type)
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


def encode_initialize_response(result: dict[str, object], transport: str) -> str:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "result": result}, separators=(",", ":")
    )
    if transport == "json":
        return payload
    split_at = payload.index('"capabilities"')
    return (
        "event: message\n"
        f"data: {payload[:split_at]}\n"
        f"data: {payload[split_at:]}\n\n"
    )


def installer_task_specs(runtime_root: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            "pwsh", "-NoProfile", "-File",
            str(REPO_ROOT / "ops" / "bifrost" / "Install-AgentCoreBifrostGateway.ps1"),
            "-EmitTaskSpecs", "-RuntimeRoot", str(runtime_root),
            "-HostAddress", "127.0.0.1", "-Port", "18080",
            "-TaskSpecPowerShellPath", "test-pwsh.exe",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def installer_task_calls(runtime_root: Path) -> list[dict[str, object]]:
    result = subprocess.run(
        [
            "pwsh", "-NoProfile", "-File",
            str(REPO_ROOT / "ops" / "bifrost" / "Install-AgentCoreBifrostGateway.ps1"),
            "-TestMode", "-RuntimeRoot", str(runtime_root),
            "-HostAddress", "127.0.0.1", "-Port", "18080",
            "-TaskSpecPowerShellPath", "test-pwsh.exe",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    marker = "INSTALL_TASK_CALLS "
    matching_lines = [line for line in result.stdout.splitlines() if line.startswith(marker)]
    assert len(matching_lines) == 1, result.stdout
    return json.loads(matching_lines[0][len(marker):])


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

    healthy = run_watchdog(runtime_root, "Healthy", started_at)
    assert healthy.returncode == 0
    for _ in range(2):
        assert run_watchdog(runtime_root, "Unhealthy", started_at).returncode == 0
    stop_failed = run_watchdog(
        runtime_root, "Unhealthy", started_at, "-TestRecycleOutcome", "StopFailure"
    )
    assert stop_failed.returncode == 1
    suppressed_stop_failure = run_watchdog(runtime_root, "Unhealthy", started_at)
    assert suppressed_stop_failure.returncode == 1
    assert "outcome=stop_failed" in suppressed_stop_failure.stdout


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


def test_start_accepts_only_client_supported_initialize_versions_for_json_and_sse(
    tmp_path: Path,
) -> None:
    for protocol_version in ("2024-11-05", "2025-03-26", "2025-06-18"):
        initialize_result = {
            "protocolVersion": protocol_version,
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1"},
        }
        for transport in ("json", "sse"):
            runtime_root = tmp_path / f"supported-{protocol_version}-{transport}"
            payload = encode_initialize_response(initialize_result, transport)
            with gateway_stub(payload) as port:
                result = run_start_against_stub(runtime_root, port)
            assert result.returncode == 0, result.stderr
            assert not (runtime_root / "state" / "bifrost-maintenance.marker").exists()


def test_start_rejects_invalid_initialize_result_shapes_for_json_and_sse(
    tmp_path: Path,
) -> None:
    invalid_results = {
        "empty-server-info": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "serverInfo": {},
        },
        "string-capabilities": {
            "protocolVersion": "2025-06-18",
            "capabilities": "tools",
            "serverInfo": {"name": "test", "version": "1"},
        },
        "unsupported-version": {
            "protocolVersion": "2099-01-01",
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1"},
        },
        "numeric-version": {
            "protocolVersion": 20250618,
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1"},
        },
        "array-capabilities": {
            "protocolVersion": "2025-06-18",
            "capabilities": [],
            "serverInfo": {"name": "test", "version": "1"},
        },
        "array-server-info": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "serverInfo": [],
        },
        "non-string-server-info-fields": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "serverInfo": {"name": 123, "version": False},
        },
    }
    for name, initialize_result in invalid_results.items():
        for transport in ("json", "sse"):
            runtime_root = tmp_path / f"{name}-{transport}"
            payload = encode_initialize_response(initialize_result, transport)
            with gateway_stub(payload) as port:
                result = run_start_against_stub(runtime_root, port)
            assert result.returncode == 1, (name, transport, result.stdout, result.stderr)
            assert not (runtime_root / "state" / "bifrost-maintenance.marker").exists()


def test_start_rejects_mcp_rpc_errors_malformed_bodies_and_missing_result_fields(
    tmp_path: Path,
) -> None:
    invalid_payloads = {
        "rpc-error": '{"jsonrpc":"2.0","id":1,"error":{"code":-32000,"message":"denied"}}',
        "malformed": "not-json",
        "missing-result-fields": '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18"}}',
    }
    for name, payload in invalid_payloads.items():
        runtime_root = tmp_path / name
        with gateway_stub(payload) as port:
            result = run_start_against_stub(runtime_root, port)
        assert result.returncode == 1, result.stderr
        assert not (runtime_root / "state" / "bifrost-maintenance.marker").exists()


def test_probe_only_never_mutates_maintenance_marker(tmp_path: Path) -> None:
    valid_result = '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{},"serverInfo":{"name":"test","version":"1"}}}'
    rpc_error = '{"jsonrpc":"2.0","id":1,"error":{"code":-32000,"message":"denied"}}'
    for name, payload, expected_code in (("success", valid_result, 0), ("failure", rpc_error, 1)):
        runtime_root = tmp_path / name
        marker = runtime_root / "state" / "bifrost-maintenance.marker"
        marker.parent.mkdir(parents=True)
        marker.write_text("operator-maintenance", encoding="utf-8")
        original = marker.read_bytes()
        with gateway_stub(payload) as port:
            result = run_start_against_stub(runtime_root, port)
        assert result.returncode == expected_code, result.stderr
        assert marker.exists()
        assert marker.read_bytes() == original

    absent_root = tmp_path / "absent"
    with gateway_stub(valid_result) as port:
        result = run_start_against_stub(absent_root, port)
    assert result.returncode == 0, result.stderr
    assert not (absent_root / "state" / "bifrost-maintenance.marker").exists()


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


def test_installer_task_specs_are_deterministic_and_non_mutating(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    specs = installer_task_specs(runtime_root)

    assert not runtime_root.exists()
    assert specs["gateway"]["action"]["executable"] == "test-pwsh.exe"
    assert "Launch-AgentCoreBifrostGateway.ps1" in specs["gateway"]["action"]["arguments"]
    assert specs["gateway"]["trigger"] == {"type": "logon", "user": os.environ["USERNAME"]}
    assert specs["gateway"]["settings"] == {
        "allow_start_if_on_batteries": True,
        "dont_stop_if_going_on_batteries": True,
        "execution_time_limit_seconds": 0,
        "restart_count": 1,
        "restart_interval_seconds": 60,
        "start_when_available": True,
        "multiple_instances": "IgnoreNew",
    }
    assert specs["gateway"]["settings"]["restart_count"] == 1
    assert specs["gateway"]["settings"]["multiple_instances"] == "IgnoreNew"
    assert specs["watchdog"]["trigger"]["start_delay_seconds"] == 60
    assert specs["watchdog"]["trigger"]["repetition_interval_seconds"] == 60
    assert specs["watchdog"]["settings"] == {
        "allow_start_if_on_batteries": True,
        "dont_stop_if_going_on_batteries": True,
        "execution_time_limit_seconds": 60,
        "restart_count": 0,
        "start_when_available": True,
        "multiple_instances": "IgnoreNew",
    }
    assert specs["watchdog"]["settings"]["multiple_instances"] == "IgnoreNew"
    assert "Invoke-AgentCoreBifrostWatchdog.ps1" in specs["watchdog"]["action"]["arguments"]
    assert specs["operational_logging"] == {
        "channel": "Microsoft-Windows-TaskScheduler/Operational", "enable": True
    }


def test_installer_behaviorally_constructs_tasks_and_logging_from_specs(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    started_at = datetime.now(timezone.utc)
    calls = installer_task_calls(runtime_root)
    finished_at = datetime.now(timezone.utc)

    assert not runtime_root.exists()
    by_scope_and_command = {
        (call["scope"], call["command"]): call["parameters"] for call in calls
    }
    launch_script = REPO_ROOT / "ops" / "bifrost" / "Launch-AgentCoreBifrostGateway.ps1"
    watchdog_script = REPO_ROOT / "ops" / "bifrost" / "Invoke-AgentCoreBifrostWatchdog.ps1"
    assert by_scope_and_command[("gateway", "New-ScheduledTaskAction")] == {
        "Execute": "test-pwsh.exe",
        "Argument": (
            f'-NoProfile -ExecutionPolicy Bypass -File "{launch_script}" '
            f'-RuntimeRoot "{runtime_root}" -HostAddress 127.0.0.1 -Port 18080'
        ),
        "WorkingDirectory": str(runtime_root),
    }
    assert by_scope_and_command[("gateway", "New-ScheduledTaskTrigger")] == {
        "AtLogOn": True,
        "User": os.environ["USERNAME"],
    }
    assert by_scope_and_command[("gateway", "New-ScheduledTaskSettingsSet")] == {
        "AllowStartIfOnBatteries": True,
        "DontStopIfGoingOnBatteries": True,
        "ExecutionTimeLimitSeconds": 0,
        "RestartCount": 1,
        "RestartIntervalSeconds": 60,
        "StartWhenAvailable": True,
        "MultipleInstances": "IgnoreNew",
    }
    assert by_scope_and_command[("watchdog", "New-ScheduledTaskAction")] == {
        "Execute": "test-pwsh.exe",
        "Argument": (
            f'-NoProfile -ExecutionPolicy Bypass -File "{watchdog_script}" '
            f'-RuntimeRoot "{runtime_root}" -GatewayUrl http://127.0.0.1:18080 '
            '-TaskPath "\\AgentCore\\" -TaskName "AgentCore-Bifrost-Gateway"'
        ),
        "WorkingDirectory": str(runtime_root),
    }
    assert by_scope_and_command[("watchdog", "New-ScheduledTaskSettingsSet")] == {
        "AllowStartIfOnBatteries": True,
        "DontStopIfGoingOnBatteries": True,
        "ExecutionTimeLimitSeconds": 60,
        "RestartCount": 0,
        "StartWhenAvailable": True,
        "MultipleInstances": "IgnoreNew",
    }
    assert by_scope_and_command[("operational_logging", "wevtutil.exe")] == {
        "ArgumentList": [
            "sl",
            "Microsoft-Windows-TaskScheduler/Operational",
            "/e:true",
        ]
    }

    watchdog_trigger_calls = [
        call
        for call in calls
        if call["scope"] == "watchdog"
        and call["command"] == "New-ScheduledTaskTrigger"
    ]
    assert len(watchdog_trigger_calls) == 2
    daily, repetition = watchdog_trigger_calls
    assert daily["parameters"]["Daily"] is True
    assert repetition["parameters"] == {
        "Once": True,
        "At": daily["parameters"]["At"],
        "RepetitionIntervalSeconds": 60,
        "RepetitionDurationSeconds": 86400,
    }
    trigger_at = datetime.fromisoformat(daily["parameters"]["At"].replace("Z", "+00:00"))
    assert started_at + timedelta(seconds=55) <= trigger_at
    assert trigger_at <= finished_at + timedelta(seconds=65)

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
    assert "New-BifrostTaskSpecs" in installer
    assert "while ($true)" not in launcher
    assert "bifrost-maintenance.marker" in starter
    assert "bifrost-maintenance.marker" in stopper
    assert "bifrost-maintenance.marker" in status
    assert HARNESS.is_file()
