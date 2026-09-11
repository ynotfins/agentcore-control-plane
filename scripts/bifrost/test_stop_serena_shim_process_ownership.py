import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STOPPER = ROOT / "ops" / "bifrost" / "Stop-AgentCoreSerenaSessionShim.ps1"
PYTHON = ROOT / "scripts" / ".venv" / "Scripts" / "python.exe"
SHIM = ROOT / "scripts" / "bifrost" / "serena_session_shim.py"
LAUNCHER = ROOT / "ops" / "bifrost" / "Launch-AgentCoreSerenaSessionShim.ps1"
RUNTIME = Path(r"F:\AgentCore\runtime\serena-shim")


def _run(expression: str) -> subprocess.CompletedProcess[str]:
    command = f". '{STOPPER}'; $ErrorActionPreference = 'Stop'; {expression}"
    return subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
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


def _owned_shim_process(pid: int, parent_pid: int, port: int = 18090) -> str:
    python = str(PYTHON)
    shim = str(SHIM)
    return _process(
        pid,
        python,
        f'"{python}" -u "{shim}" --host 127.0.0.1 --port {port}',
        parent_pid,
    )


def _launcher_process(pid: int, port: int = 18090) -> str:
    pwsh = r"C:\Program Files\PowerShell\7\pwsh.exe"
    return _process(
        pid,
        pwsh,
        f'"{pwsh}" -NoProfile -NonInteractive -File "{LAUNCHER}" '
        f'-RepoRoot "{ROOT}" -RuntimeRoot "{RUNTIME}" '
        f"-HostAddress 127.0.0.1 -Port {port}",
        4,
    )


def test_same_name_python_at_unrelated_path_is_not_owned() -> None:
    process = _process(101, r"C:\Temp\python.exe", f'C:\\Temp\\python.exe -u "{SHIM}"')
    result = _run(
        f"$p = '{process}' | ConvertFrom-Json; "
        f"Test-AgentCoreSerenaShimProcess $p '{PYTHON}' '{SHIM}' | ConvertTo-Json"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) is False


def test_exact_python_and_shim_script_are_required() -> None:
    process = _owned_shim_process(102, 202)
    result = _run(
        f"$p = '{process}' | ConvertFrom-Json; "
        f"Test-AgentCoreSerenaShimProcess $p '{PYTHON}' '{SHIM}' | ConvertTo-Json"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) is True


def test_identity_requires_host_and_port() -> None:
    wrong_port = _process(
        103,
        str(PYTHON),
        f'"{PYTHON}" -u "{SHIM}" --host 127.0.0.1 --port 18091',
        203,
    )
    result = _run(
        f"$p = '{wrong_port}' | ConvertFrom-Json; "
        f"Test-AgentCoreSerenaShimIdentity $p '{PYTHON}' '{SHIM}' '127.0.0.1' 18090 | ConvertTo-Json"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) is False


def test_port_owner_mismatch_fails_closed() -> None:
    process = _process(104, r"C:\Other\python.exe")
    result = _run(
        f"$p = '{process}' | ConvertFrom-Json; "
        "$listener = [pscustomobject]@{ OwningProcess = 104 }; "
        "Assert-AgentCoreSerenaPortOwnership @($listener) @($p) "
        f"'{PYTHON}' '{SHIM}' '{ROOT}' '{RUNTIME}' '127.0.0.1' 18090 '{LAUNCHER}'"
    )
    assert result.returncode != 0
    assert "Refusing to stop non-AgentCore process PID=104 holding port 18090" in (
        result.stdout + result.stderr
    )


def test_port_owner_with_exact_identity_passes() -> None:
    process = _owned_shim_process(105, 205)
    parent = _launcher_process(205)
    result = _run(
        f"$p = @('{process}','{parent}') | ForEach-Object {{ $_ | ConvertFrom-Json }}; "
        "$listener = [pscustomobject]@{ OwningProcess = 105 }; "
        "Assert-AgentCoreSerenaPortOwnership @($listener) @($p) "
        f"'{PYTHON}' '{SHIM}' '{ROOT}' '{RUNTIME}' '127.0.0.1' 18090 '{LAUNCHER}'"
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_identity_ownership_accepts_orphan_after_launcher_exit() -> None:
    process = _owned_shim_process(106, 9999)
    result = _run(
        f"$p = '{process}' | ConvertFrom-Json; "
        "$listener = [pscustomobject]@{ OwningProcess = 106 }; "
        "Assert-AgentCoreSerenaPortIdentityOwnership @($listener) @($p) "
        f"'{PYTHON}' '{SHIM}' '127.0.0.1' 18090"
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_unrelated_script_on_same_python_is_rejected() -> None:
    process = _process(
        107,
        str(PYTHON),
        f'"{PYTHON}" -u "D:\\Temp\\other.py" --host 127.0.0.1 --port 18090',
        207,
    )
    result = _run(
        f"$p = '{process}' | ConvertFrom-Json; "
        f"Test-AgentCoreSerenaShimIdentity $p '{PYTHON}' '{SHIM}' '127.0.0.1' 18090 | ConvertTo-Json"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) is False
