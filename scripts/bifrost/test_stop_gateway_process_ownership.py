import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STOPPER = ROOT / "ops" / "bifrost" / "Stop-AgentCoreBifrostGateway.ps1"


def _run(expression: str) -> subprocess.CompletedProcess[str]:
    command = f". '{STOPPER}'; $ErrorActionPreference = 'Stop'; {expression}"
    return subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )


def _process(
    pid: int, executable: str, command_line: str = "", parent_pid: int = 0
) -> str:
    return json.dumps(
        {
            "ProcessId": pid,
            "ParentProcessId": parent_pid,
            "ExecutablePath": executable,
            "CommandLine": command_line,
        },
        separators=(",", ":"),
    ).replace("'", "''")


def _owned_gateway_process(pid: int, parent_pid: int, port: int = 8080) -> str:
    runtime = r"F:\AgentCore\runtime\bifrost"
    executable = runtime + r"\bin\bifrost-http.exe"
    return _process(
        pid,
        executable,
        f'"{executable}" -app-dir "{runtime}" -host 127.0.0.1 -port {port} '
        "-log-level info -log-style json",
        parent_pid,
    )


def _launcher_process(pid: int, port: int = 8080, script: str | None = None) -> str:
    pwsh = r"C:\Program Files\PowerShell\7\pwsh.exe"
    runtime = r"F:\AgentCore\runtime\bifrost"
    launcher = script or str(ROOT / "ops" / "bifrost" / "Launch-AgentCoreBifrostGateway.ps1")
    return _process(
        pid,
        pwsh,
        f'"{pwsh}" -NoProfile -NonInteractive -File "{launcher}" '
        f'-RuntimeRoot "{runtime}" -HostAddress 127.0.0.1 -Port {port}',
        4,
    )


def test_same_name_process_at_unrelated_path_is_not_owned() -> None:
    process = _process(101, r"C:\Temp\bifrost-http.exe")
    result = _run(
        f"$p = '{process}' | ConvertFrom-Json; "
        "Test-AgentCoreBifrostProcess $p 'F:\\AgentCore\\runtime\\bifrost\\bin\\bifrost-http.exe' | ConvertTo-Json"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) is False


def test_exact_bifrost_executable_path_is_required_and_accepted() -> None:
    process = _process(102, r"F:\AgentCore\runtime\bifrost\bin\bifrost-http.exe")
    result = _run(
        f"$p = '{process}' | ConvertFrom-Json; "
        "Test-AgentCoreBifrostProcess $p 'f:\\agentcore\\runtime\\bifrost\\bin\\bifrost-http.exe' | ConvertTo-Json"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) is True


def test_port_owner_mismatch_fails_closed() -> None:
    process = _process(103, r"C:\Other\bifrost-http.exe")
    result = _run(
        f"$p = '{process}' | ConvertFrom-Json; "
        "$listener = [pscustomobject]@{ OwningProcess = 103 }; "
        "Assert-AgentCorePortOwnership @($listener) @($p) "
        "'F:\\AgentCore\\runtime\\bifrost\\bin\\bifrost-http.exe' "
        "'F:\\AgentCore\\runtime\\bifrost' '127.0.0.1' 8080 "
        f"'{ROOT / 'ops' / 'bifrost' / 'Launch-AgentCoreBifrostGateway.ps1'}'"
    )
    assert result.returncode != 0
    assert "Refusing to stop non-AgentCore process PID=103 holding port 8080" in (
        result.stdout + result.stderr
    )


def test_port_owner_with_exact_path_passes() -> None:
    process = _owned_gateway_process(104, 204)
    parent = _launcher_process(204)
    result = _run(
        f"$p = @('{process}','{parent}') | ForEach-Object {{ $_ | ConvertFrom-Json }}; "
        "$listener = [pscustomobject]@{ OwningProcess = 104 }; "
        "Assert-AgentCorePortOwnership @($listener) @($p) "
        "'F:\\AgentCore\\runtime\\bifrost\\bin\\bifrost-http.exe' "
        "'F:\\AgentCore\\runtime\\bifrost' '127.0.0.1' 8080 "
        f"'{ROOT / 'ops' / 'bifrost' / 'Launch-AgentCoreBifrostGateway.ps1'}'"
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_proxy_requires_exact_executable_and_complete_command_line() -> None:
    node = r"C:\Users\ynotf\AppData\Local\pnpm\bin\node.exe"
    script = str(ROOT / "ops" / "bifrost" / "agentcore-builder-compat-proxy.cjs")
    accepted = _process(201, node, f'"{node}" "{script}"')
    extra_argument = _process(202, node, f'"{node}" "{script}" --foreign')
    wrong_node = _process(203, r"C:\Temp\node.exe", f'"{node}" "{script}"')
    substring_only = _process(204, node, f'"{node}" "C:\\Temp\\wrapper-{Path(script).name}"')
    result = _run(
        f"$items = @('{accepted}','{extra_argument}','{wrong_node}','{substring_only}') | "
        "ForEach-Object { $_ | ConvertFrom-Json }; "
        f"@($items | ForEach-Object {{ Test-AgentCoreBuilderProxyProcess $_ '{node}' '{script}' }}) | ConvertTo-Json -Compress"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == [True, False, False, False]


def test_stop_script_validates_listener_ownership_before_stop_process() -> None:
    text = STOPPER.read_text(encoding="utf-8")
    assert "Get-Process -Name 'bifrost-http'" not in text
    assert "$postTask.Listeners" in text
    assert "Test-AgentCoreOwnedBifrostProcess" in text
    assert "Test-AgentCoreBifrostIdentity" in text
    assert "Assert-AgentCorePortOwnership" in text
    assert "Assert-AgentCorePortIdentityOwnership" in text
    preflight = text.index("$preflight = Get-AgentCoreGatewayProcessSnapshot")
    marker = text.index("New-Item -ItemType Directory")
    task_stop = text.index("Stop-ScheduledTask")
    post_task = text.index("$postTask = Get-AgentCoreGatewayProcessSnapshot")
    identity_assert = text.index("Assert-AgentCorePortIdentityOwnership", post_task)
    process_stop = text.index("Stop-Process -Id $process.ProcessId", identity_assert)
    identity_match = text.index("Stopping AgentCore Bifrost identity match", process_stop)
    assert preflight < marker < task_stop < post_task < identity_assert < process_stop < identity_match
    assert "Stop-ScheduledTask" in text
    assert "bifrost-maintenance.marker" in text


def test_foreign_listener_causes_zero_mutation() -> None:
    foreign = _process(301, r"C:\Other\bifrost-http.exe")
    result = _run(
        "$script:mutations = @(); "
        f"$script:foreign = '{foreign}' | ConvertFrom-Json; "
        "function Get-CimInstance { param($ClassName, $ErrorAction) @($script:foreign) }; "
        "function Get-NetTCPConnection { param($LocalPort, $State, $ErrorAction) "
        "[pscustomobject]@{ OwningProcess = 301 } }; "
        "function New-Item { $script:mutations += 'new-item' }; "
        "function Set-Content { $script:mutations += 'set-content' }; "
        "function Stop-ScheduledTask { $script:mutations += 'stop-task' }; "
        "function Stop-Process { $script:mutations += 'stop-process' }; "
        "$caught = ''; try { Stop-AgentCoreBifrostGateway } "
        "catch { $caught = $_.Exception.Message }; "
        "[pscustomobject]@{ Caught = $caught; Mutations = @($script:mutations) } | "
        "ConvertTo-Json -Compress"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert "Refusing to stop non-AgentCore process PID=301" in output["Caught"]
    assert output["Mutations"] == []


def test_same_binary_with_foreign_launcher_parent_causes_zero_mutation() -> None:
    child = _owned_gateway_process(311, 312)
    parent = _launcher_process(312, script=r"C:\Temp\foreign-launcher.ps1")
    result = _run(
        "$script:mutations = @(); "
        f"$script:items = @('{child}','{parent}') | ForEach-Object {{ $_ | ConvertFrom-Json }}; "
        "function Get-CimInstance { param($ClassName, $ErrorAction) @($script:items) }; "
        "function Get-NetTCPConnection { param($LocalPort, $State, $ErrorAction) "
        "[pscustomobject]@{ OwningProcess = 311 } }; "
        "function New-Item { $script:mutations += 'new-item' }; "
        "function Set-Content { $script:mutations += 'set-content' }; "
        "function Stop-ScheduledTask { $script:mutations += 'stop-task' }; "
        "function Stop-Process { $script:mutations += 'stop-process' }; "
        "$caught = ''; try { Stop-AgentCoreBifrostGateway } catch { $caught = $_.Exception.Message }; "
        "[pscustomobject]@{ Caught=$caught; Mutations=@($script:mutations) } | ConvertTo-Json -Compress"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert "Refusing to stop non-AgentCore process PID=311" in output["Caught"]
    assert output["Mutations"] == []


def test_post_task_snapshot_drives_process_termination() -> None:
    first = _owned_gateway_process(401, 501)
    first_parent = _launcher_process(501)
    second = _owned_gateway_process(402, 502)
    second_parent = _launcher_process(502)
    same_binary_other_port = _owned_gateway_process(499, 599, port=9999)
    other_parent = _launcher_process(599, port=9999)
    result = _run(
        "$script:mutations = @(); $script:cimCalls = 0; $script:netCalls = 0; "
        f"$script:first = @('{first}','{first_parent}') | ForEach-Object {{ $_ | ConvertFrom-Json }}; "
        f"$script:second = @('{second}','{second_parent}','{same_binary_other_port}','{other_parent}') | ForEach-Object {{ $_ | ConvertFrom-Json }}; "
        "function Get-CimInstance { param($ClassName, $ErrorAction) "
        "$script:cimCalls += 1; "
        "if ($script:cimCalls -eq 1) { @($script:first) } else { @($script:second) } }; "
        "function Get-NetTCPConnection { param($LocalPort, $State, $ErrorAction) "
        "$script:netCalls += 1; if ($script:netCalls -eq 1) { "
        "[pscustomobject]@{ OwningProcess = 401 } } else { "
        "[pscustomobject]@{ OwningProcess = 402 } } }; "
        "function New-Item { param($ItemType, [switch]$Force, $Path) $script:mutations += 'new-item' }; "
        "function Set-Content { param($LiteralPath, $Value, $Encoding) $script:mutations += 'set-content' }; "
        "function Stop-ScheduledTask { param($TaskPath, $TaskName, $ErrorAction) "
        "$script:mutations += 'stop-task' }; "
        "function Stop-Process { param($Id, [switch]$Force, $ErrorAction) "
        "$script:mutations += ('stop-pid:' + $Id) }; "
        "function Write-Host { param($Object) }; "
        "Stop-AgentCoreBifrostGateway; "
        "[pscustomobject]@{ CimCalls = $script:cimCalls; NetCalls = $script:netCalls; "
        "Mutations = @($script:mutations) } | ConvertTo-Json -Compress"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["CimCalls"] == 2
    assert output["NetCalls"] == 2
    assert "stop-pid:402" in output["Mutations"]
    assert "stop-pid:401" not in output["Mutations"]
    assert "stop-pid:499" not in output["Mutations"]


def test_identity_kill_when_listeners_miss_and_parent_gone() -> None:
    orphan = _owned_gateway_process(701, 801)
    # Parent intentionally omitted from process table to simulate post-task reaping.
    foreign = _owned_gateway_process(702, 802, port=9999)
    result = _run(
        "$script:mutations = @(); $script:cimCalls = 0; $script:netCalls = 0; "
        f"$script:first = @('{orphan}') | ForEach-Object {{ $_ | ConvertFrom-Json }}; "
        f"$script:second = @('{orphan}','{foreign}') | ForEach-Object {{ $_ | ConvertFrom-Json }}; "
        "function Get-CimInstance { param($ClassName, $ErrorAction) "
        "$script:cimCalls += 1; "
        "if ($script:cimCalls -eq 1) { @($script:first) } else { @($script:second) } }; "
        "function Get-NetTCPConnection { param($LocalPort, $State, $ErrorAction) "
        "$script:netCalls += 1; @() }; "
        "function New-Item { param($ItemType, [switch]$Force, $Path) $script:mutations += 'new-item' }; "
        "function Set-Content { param($LiteralPath, $Value, $Encoding) $script:mutations += 'set-content' }; "
        "function Stop-ScheduledTask { param($TaskPath, $TaskName, $ErrorAction) "
        "$script:mutations += 'stop-task' }; "
        "function Stop-Process { param($Id, [switch]$Force, $ErrorAction) "
        "$script:mutations += ('stop-pid:' + $Id) }; "
        "function Write-Host { param($Object) }; "
        "Stop-AgentCoreBifrostGateway; "
        "[pscustomobject]@{ Mutations = @($script:mutations) } | ConvertTo-Json -Compress"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert "stop-task" in output["Mutations"]
    assert "stop-pid:701" in output["Mutations"]
    assert "stop-pid:702" not in output["Mutations"]
