import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROXY = ROOT / "ops" / "bifrost" / "agentcore-builder-compat-proxy.cjs"
RESOLVER = ROOT / "ops" / "bifrost" / "Resolve-AgentCoreBuilderCaller.ps1"
LAUNCHER = ROOT / "ops" / "bifrost" / "Launch-AgentCoreBifrostGateway.ps1"
STOPPER = ROOT / "ops" / "bifrost" / "Stop-AgentCoreBifrostGateway.ps1"
ADOPTION_VALIDATOR = ROOT / "ops" / "Test-AgentCoreLiveClientAdoption.ps1"
GATEWAY_CONTRACT = ROOT / "contracts" / "agentcore-gateway-client.json"


def _run_launcher_ownership_functions(expression: str) -> subprocess.CompletedProcess[str]:
    function_names = (
        "ConvertTo-AgentCoreCanonicalPath",
        "Get-AgentCoreCommandLineArgument",
        "Test-AgentCoreCommandLineArgument",
        "Test-AgentCoreLauncherProcess",
        "Test-AgentCoreOwnedProcess",
    )
    names = ",".join(f"'{name}'" for name in function_names)
    command = (
        f"$tokens=$null; $errors=$null; $ast=[System.Management.Automation.Language.Parser]::ParseFile('{LAUNCHER}',[ref]$tokens,[ref]$errors); "
        f"foreach($name in @({names})){{ $fn=$ast.Find({{param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name}},$true); if(-not $fn){{throw ('missing function '+$name)}}; Invoke-Expression $fn.Extent.Text }}; "
        "$ErrorActionPreference='Stop'; " + expression
    )
    return subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )


def test_proxy_is_loopback_only_and_injects_process_identity() -> None:
    text = PROXY.read_text(encoding="utf-8")
    assert "127.0.0.1" in text
    assert "BIFROST_MCP_VIRTUAL_KEY" in text
    assert "delete result.authorization" in text
    assert "Bearer ${virtualKey}" in text
    assert "request.pipe(upstream)" in text
    assert "resolveSocketIdentity(request.socket)" in text
    assert "Resolve-AgentCoreBuilderCaller.ps1" in text
    assert "caller identity denied" in text
    assert "timingSafeEqual" in text
    assert "hasValidAuthorization(request.headers)" in text
    log_lines = [line for line in text.splitlines() if "stderr.write" in line]
    assert all("${virtualKey}" not in line for line in log_lines)


def test_gateway_lifecycle_owns_proxy_without_command_line_secret() -> None:
    launch = LAUNCHER.read_text(encoding="utf-8")
    stop = STOPPER.read_text(encoding="utf-8")
    assert "Ensure-BuilderCompatProxy" in launch
    assert "agentcore-builder-compat-proxy.cjs" in launch
    assert "Resolve-AgentCoreBuilderCaller.ps1" in launch
    assert "-ArgumentList @($proxyScript)" in launch
    assert "BuilderCompatPort = 18082" in launch
    assert "agentcore-builder-compat-proxy.cjs" in stop
    assert "CommandLine" in stop
    assert "$compatScript = Join-Path $PSScriptRoot" in stop
    assert "Test-AgentCoreBuilderProxyProcess" in stop
    assert "ExpectedNode $node -ExpectedScript $compatScript" in stop


def test_proxy_failure_is_degraded_and_cannot_block_core_gateway_loop() -> None:
    launch = LAUNCHER.read_text(encoding="utf-8")
    proxy_call = launch.rindex("Ensure-BuilderCompatProxy")
    core_loop = launch.index("while ($true)", proxy_call)
    startup_block = launch[launch.rfind("try {", 0, proxy_call):core_loop]

    assert "try {" in startup_block
    assert "catch {" in startup_block
    assert "BUILDER_COMPAT_PROXY_DEGRADED" in startup_block
    assert "throw" not in startup_block
    assert "Starting bifrost-http process" in launch[core_loop:]


def test_launcher_cleanup_is_listener_scoped_and_rejects_incomplete_ownership() -> None:
    launch = LAUNCHER.read_text(encoding="utf-8")
    assert "Get-Process -Name bifrost-http" not in launch

    runtime = r"F:\AgentCore\runtime\bifrost"
    executable = runtime + r"\bin\bifrost-http.exe"
    launcher = str(LAUNCHER)
    pwsh = r"C:\Program Files\PowerShell\7\pwsh.exe"
    valid_bifrost = {
        "ProcessId": 501,
        "ParentProcessId": 401,
        "ExecutablePath": executable,
        "CommandLine": (
            f'"{executable}" -app-dir "{runtime}" -host 127.0.0.1 -port 8080 '
            "-log-level info -log-style json"
        ),
    }
    valid_parent = {
        "ProcessId": 401,
        "ParentProcessId": 4,
        "ExecutablePath": pwsh,
        "CommandLine": (
            f'"{pwsh}" -NoProfile -NonInteractive -File "{launcher}" '
            f'-RuntimeRoot "{runtime}" -HostAddress 127.0.0.1 -Port 8080'
        ),
    }
    wrong_port = valid_bifrost | {
        "ProcessId": 502,
        "CommandLine": valid_bifrost["CommandLine"].replace("-port 8080", "-port 9999"),
    }
    wrong_parent = valid_parent | {
        "ProcessId": 402,
        "CommandLine": f'"{pwsh}" -File "C:\\Temp\\foreign.ps1"',
    }
    processes = [valid_bifrost, valid_parent, wrong_port, wrong_parent]
    encoded = json.dumps(processes, separators=(",", ":")).replace("'", "''")
    result = _run_launcher_ownership_functions(
        f"$script:processes='{encoded}'|ConvertFrom-Json; "
        "function Get-CimInstance { param($ClassName,$Filter,$ErrorAction); "
        "if($Filter -match '(\\d+)$'){ $pidValue=[int]$Matches[1]; "
        "return @($script:processes|Where-Object { [int]$_.ProcessId -eq $pidValue }) } }; "
        f"$valid=Test-AgentCoreOwnedProcess 501 '{executable}' '{runtime}' '127.0.0.1' 8080 '{launcher}'; "
        f"$badTuple=Test-AgentCoreOwnedProcess 502 '{executable}' '{runtime}' '127.0.0.1' 8080 '{launcher}'; "
        "$script:processes[0].ParentProcessId=402; "
        f"$badParent=Test-AgentCoreOwnedProcess 501 '{executable}' '{runtime}' '127.0.0.1' 8080 '{launcher}'; "
        "@($valid,$badTuple,$badParent)|ConvertTo-Json -Compress"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == [True, False, False]


def _resolve(processes: list[dict[str, object]], pid: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["AGENTCORE_BUILDER_CALLER_TEST_MODE"] = "1"
    return subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(RESOLVER),
            "-ServerPort",
            "18082",
            "-ClientPort",
            "49152",
            "-TestClientPid",
            str(pid),
            "-TestProcessTableJson",
            json.dumps(processes, separators=(",", ":")),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
        env=env,
    )


def _local_app_data() -> Path:
    return Path(os.environ["LOCALAPPDATA"])


def test_resolver_accepts_exact_trusted_ancestor() -> None:
    processes = [
        {
            "ProcessId": 101,
            "ParentProcessId": 100,
            "ExecutablePath": r"C:\Program Files\nodejs\node.exe",
        },
        {
            "ProcessId": 100,
            "ParentProcessId": 4,
            "ExecutablePath": str(
                _local_app_data() / "Programs" / "Devin Next" / "Devin - Next.exe"
            ),
        },
    ]
    result = _resolve(processes, 101)
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["allowed"] is True
    assert output["client"] == "devin"
    assert output["client_pid"] == 101
    assert output["matched_pid"] == 100


def test_resolver_accepts_current_devin_cli() -> None:
    cli = _local_app_data() / "devin" / "cli-next" / "bin" / "devin-next.exe"
    result = _resolve(
        [
            {
                "ProcessId": 201,
                "ParentProcessId": 4,
                "ExecutablePath": str(cli),
            }
        ],
        201,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["allowed"] is True
    assert output["client"] == "devin"
    assert output["matched_pid"] == 201


def test_resolver_accepts_opencode_trusted_exe() -> None:
    opencode = (
        Path(os.environ["APPDATA"])
        / "npm"
        / "node_modules"
        / "opencode-ai"
        / "bin"
        / "opencode.exe"
    )
    result = _resolve(
        [
            {
                "ProcessId": 301,
                "ParentProcessId": 300,
                "ExecutablePath": r"C:\Program Files\nodejs\node.exe",
            },
            {
                "ProcessId": 300,
                "ParentProcessId": 4,
                "ExecutablePath": str(opencode),
            },
        ],
        301,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["allowed"] is True
    assert output["client"] == "opencode"
    assert output["matched_pid"] == 300


def test_resolver_rejects_opencode_name_at_untrusted_path() -> None:
    result = _resolve(
        [
            {
                "ProcessId": 301,
                "ParentProcessId": 4,
                "ExecutablePath": r"C:\Temp\opencode.exe",
            }
        ],
        301,
    )
    assert result.returncode != 0
    assert json.loads(result.stdout)["allowed"] is False


def test_resolver_rejects_same_name_at_untrusted_path() -> None:
    result = _resolve(
        [
            {
                "ProcessId": 101,
                "ParentProcessId": 4,
                "ExecutablePath": r"C:\Temp\Devin - Next.exe",
            }
        ],
        101,
    )
    assert result.returncode != 0
    assert json.loads(result.stdout)["allowed"] is False


def test_resolver_rejects_missing_process() -> None:
    result = _resolve([], 101)
    assert result.returncode != 0
    assert json.loads(result.stdout)["code"] == "process_unavailable"


def test_resolver_rejects_missing_executable_identity() -> None:
    result = _resolve(
        [
            {"ProcessId": 101, "ParentProcessId": 100, "ExecutablePath": ""},
            {
                "ProcessId": 100,
                "ParentProcessId": 4,
                "ExecutablePath": r"C:\Windows\System32\cmd.exe",
            },
        ],
        101,
    )
    assert result.returncode != 0
    assert json.loads(result.stdout)["code"] == "untrusted_process_ancestry"


def test_resolver_continues_past_empty_ancestor_to_exact_devin_path() -> None:
    result = _resolve(
        [
            {"ProcessId": 101, "ParentProcessId": 100, "ExecutablePath": ""},
            {
                "ProcessId": 100,
                "ParentProcessId": 4,
                "ExecutablePath": str(
                    _local_app_data() / "Programs" / "Devin Next" / "Devin - Next.exe"
                ),
            },
        ],
        101,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["allowed"] is True
    assert output["client"] == "devin"
    assert output["matched_pid"] == 100


def test_resolver_rejects_process_cycle() -> None:
    result = _resolve(
        [
            {
                "ProcessId": 101,
                "ParentProcessId": 101,
                "ExecutablePath": r"C:\Program Files\nodejs\node.exe",
            }
        ],
        101,
    )
    assert result.returncode != 0
    assert json.loads(result.stdout)["code"] == "invalid_process_ancestry"


def test_resolver_rejects_ambiguous_tcp_owner_mapping() -> None:
    env = os.environ.copy()
    env["AGENTCORE_BUILDER_CALLER_TEST_MODE"] = "1"
    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(RESOLVER),
            "-ServerPort",
            "18082",
            "-ClientPort",
            "49152",
            "-TestCandidatePidsJson",
            "[101,102]",
            "-TestProcessTableJson",
            "[]",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
        env=env,
    )
    assert result.returncode != 0
    assert json.loads(result.stdout)["code"] == "tcp_owner_not_unique"


def test_resolver_test_hook_is_disabled_without_explicit_environment() -> None:
    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(RESOLVER),
            "-ServerPort",
            "18082",
            "-ClientPort",
            "49152",
            "-TestClientPid",
            "101",
            "-TestProcessTableJson",
            "[]",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
        env={key: value for key, value in os.environ.items() if key != "AGENTCORE_BUILDER_CALLER_TEST_MODE"},
    )
    assert result.returncode != 0
    assert json.loads(result.stdout)["code"] == "invalid_test_mode"


def test_resolver_allowlist_excludes_direct_authenticated_clients() -> None:
    text = RESOLVER.read_text(encoding="utf-8").lower()
    assert "cursor.exe" not in text
    assert "codex.exe" not in text
    assert "minimax agent" not in text
    assert "commandline" not in text
    assert "netstat.exe" in text
    assert "Interpreter\\Interpreter.exe" in RESOLVER.read_text(encoding="utf-8")


def test_proxy_denies_untrusted_loopback_but_accepts_existing_bearer() -> None:
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    env = os.environ.copy()
    env["AGENTCORE_BUILDER_COMPAT_PORT"] = str(port)
    env["BIFROST_MCP_VIRTUAL_KEY"] = "builder-proxy-test-key"
    process = subprocess.Popen(
        ["node", str(PROXY)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        deadline = time.monotonic() + 10
        while True:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1) as response:
                    assert response.status == 200
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)

        unauthenticated = urllib.request.Request(
            f"http://127.0.0.1:{port}/mcp", data=b"{}", method="POST"
        )
        try:
            urllib.request.urlopen(unauthenticated, timeout=10)
            raise AssertionError("untrusted loopback request unexpectedly succeeded")
        except urllib.error.HTTPError as error:
            assert error.code == 403
            assert error.read() == b"caller identity denied"

        authenticated = urllib.request.Request(
            f"http://127.0.0.1:{port}/mcp",
            data=b"{}",
            method="POST",
            headers={"Authorization": "Bearer builder-proxy-test-key"},
        )
        try:
            urllib.request.urlopen(authenticated, timeout=10)
            status = 200
        except urllib.error.HTTPError as error:
            status = error.code
        assert status != 403
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_live_adoption_uses_machine_readable_process_attested_routes() -> None:
    contract = json.loads(GATEWAY_CONTRACT.read_text(encoding="utf-8"))
    hints = contract["client_render_hints"]
    expected = {
        "minimax",
        "antigravity",
        "zcode",
        "open-interpreter",
        "devin",
        "eigent",
        "zed",
        "opencode",
    }
    actual = {
        name
        for name, hint in hints.items()
        if hint.get("gateway_auth_mode") == "process_attested_proxy"
    }
    # Trust Class A set must include the priority clients; allow additional peers.
    assert expected.issubset(actual)
    assert all(hints[name]["gateway_url"] == "http://127.0.0.1:18082/mcp" for name in expected)

    validator = ADOPTION_VALIDATOR.read_text(encoding="utf-8")
    assert "gateway_auth_mode -eq 'process_attested_proxy'" in validator
    assert "gateway_url" in validator
    assert '"$proxyBase/healthz"' in validator
    assert "headerless_status=$deniedStatus" in validator
