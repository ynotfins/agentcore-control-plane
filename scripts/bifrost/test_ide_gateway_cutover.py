from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CUTOVER = REPO_ROOT / "ops" / "bifrost" / "Invoke-AgentCoreIdeGatewayCutover.ps1"


def write_cursor_fixture(path: Path) -> bytes:
    payload = {
        "mcpServers": {
            "agentcore-gateway": {"type": "http", "url": "http://stale.invalid/mcp"},
            "command-runner": {"command": "command-runner"},
            "memory-bank": {"url": "http://memory-bank.invalid/mcp"},
        }
    }
    content = json.dumps(payload, indent=2).encode("utf-8")
    path.write_bytes(content)
    return content


def run_cutover(
    script: Path, config: Path, evidence: Path, *extra_args: str, client: str = "cursor"
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "pwsh", "-NoProfile", "-File", str(script), "-RepoRoot", str(REPO_ROOT),
            "-EvidenceRoot", str(evidence), "-Clients", client, *extra_args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cursor_cutover_removes_unknown_global_servers(tmp_path: Path) -> None:
    config = tmp_path / "cursor-mcp.json"
    write_cursor_fixture(config)
    source = CUTOVER.read_text(encoding="utf-8")
    fixture_script = tmp_path / "Invoke-AgentCoreIdeGatewayCutover.ps1"
    fixture_script.write_text(
        source.replace(r"C:\Users\ynotf\.cursor\mcp.json", str(config)), encoding="utf-8"
    )

    result = run_cutover(fixture_script, config, tmp_path / "evidence")

    assert result.returncode == 0, result.stderr
    assert list(json.loads(config.read_text(encoding="utf-8"))["mcpServers"]) == [
        "agentcore-gateway"
    ]


def test_cursor_config_override_normalizes_and_backs_up_fixture(tmp_path: Path) -> None:
    config = tmp_path / "cursor-mcp.json"
    original = write_cursor_fixture(config)
    evidence = tmp_path / "evidence"

    result = run_cutover(CUTOVER, config, evidence, "-CursorConfigPath", str(config))

    assert result.returncode == 0, result.stderr
    assert list(json.loads(config.read_text(encoding="utf-8"))["mcpServers"]) == [
        "agentcore-gateway"
    ]
    backups = list(tmp_path.glob("cursor-mcp.json.bifrost-cutover-*.bak"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == original


def test_non_cursor_cutover_preserves_unknown_servers(tmp_path: Path) -> None:
    config = tmp_path / "minimax-mcp.json"
    write_cursor_fixture(config)
    source = CUTOVER.read_text(encoding="utf-8")
    fixture_script = tmp_path / "Invoke-AgentCoreIdeGatewayCutover.ps1"
    fixture_script.write_text(
        source.replace(r"C:\Users\ynotf\.minimax\mcp\mcp.json", str(config)), encoding="utf-8"
    )

    result = run_cutover(
        fixture_script, config, tmp_path / "evidence", client="minimax"
    )

    assert result.returncode == 0, result.stderr
    assert list(json.loads(config.read_text(encoding="utf-8"))["mcpServers"]) == [
        "command-runner", "memory-bank", "agentcore-gateway"
    ]
