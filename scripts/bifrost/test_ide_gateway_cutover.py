from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CUTOVER = REPO_ROOT / "ops" / "bifrost" / "Invoke-AgentCoreIdeGatewayCutover.ps1"


def write_mcp_fixture(path: Path) -> bytes:
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
    config: Path, evidence: Path, *, client: str = "cursor", dry_run: bool = False
) -> subprocess.CompletedProcess[str]:
    config_parameter = "-CursorConfigPath" if client == "cursor" else "-MinimaxConfigPath"
    args = [
        "pwsh", "-NoProfile", "-File", str(CUTOVER), "-RepoRoot", str(REPO_ROOT),
        "-EvidenceRoot", str(evidence), "-Clients", client, config_parameter, str(config),
    ]
    if dry_run:
        args.append("-DryRun")
    return subprocess.run(args, capture_output=True, text=True, check=False)


def tree_snapshot(root: Path) -> dict[str, tuple[int, int, str]]:
    paths = [root, *sorted(root.rglob("*"))]
    return {
        str(path.relative_to(root)): (
            path.stat().st_size,
            path.stat().st_mtime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "<directory>",
        )
        for path in paths
    }


def test_cursor_cutover_removes_unknown_global_servers_via_explicit_path(tmp_path: Path) -> None:
    config = tmp_path / "cursor-mcp.json"
    write_mcp_fixture(config)
    evidence = tmp_path / "evidence"

    result = run_cutover(config, evidence)

    assert result.returncode == 0, result.stderr
    assert list(json.loads(config.read_text(encoding="utf-8"))["mcpServers"]) == [
        "agentcore-gateway"
    ]
    assert json.loads((evidence / "cursor.json").read_text(encoding="utf-8"))["path"] == str(config)


def test_cursor_config_override_normalizes_and_backs_up_fixture(tmp_path: Path) -> None:
    config = tmp_path / "cursor-mcp.json"
    original = write_mcp_fixture(config)

    result = run_cutover(config, tmp_path / "evidence")

    assert result.returncode == 0, result.stderr
    assert list(json.loads(config.read_text(encoding="utf-8"))["mcpServers"]) == [
        "agentcore-gateway"
    ]
    backups = list(tmp_path.glob("cursor-mcp.json.bifrost-cutover-*.bak"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == original


def test_non_cursor_cutover_preserves_unknown_servers_via_explicit_path(tmp_path: Path) -> None:
    config = tmp_path / "minimax-mcp.json"
    write_mcp_fixture(config)

    result = run_cutover(config, tmp_path / "evidence", client="minimax")

    assert result.returncode == 0, result.stderr
    assert list(json.loads(config.read_text(encoding="utf-8"))["mcpServers"]) == [
        "command-runner", "memory-bank", "agentcore-gateway"
    ]


def test_dry_run_leaves_config_evidence_parent_and_backups_unchanged(tmp_path: Path) -> None:
    config = tmp_path / "cursor-mcp.json"
    write_mcp_fixture(config)
    evidence = tmp_path / "missing-evidence"
    before = tree_snapshot(tmp_path)

    result = run_cutover(config, evidence, dry_run=True)

    assert result.returncode == 0, result.stderr
    assert tree_snapshot(tmp_path) == before
    assert not evidence.exists()
    plan = json.loads(result.stdout)
    assert (plan if isinstance(plan, dict) else plan[0])["action"] == "dry-run"


def test_immediate_cutovers_create_distinct_byte_exact_backups(tmp_path: Path) -> None:
    config = tmp_path / "cursor-mcp.json"
    original = write_mcp_fixture(config)

    first = run_cutover(config, tmp_path / "evidence-one")
    first_result = config.read_bytes()
    second = run_cutover(config, tmp_path / "evidence-two")

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    backups = sorted(tmp_path.glob("cursor-mcp.json.bifrost-cutover-*.bak"))
    assert len(backups) == 2
    assert backups[0] != backups[1]
    assert all(
        re.fullmatch(
            r"cursor-mcp\.json\.bifrost-cutover-\d{8}-\d{13}(?:-\d+)?\.bak",
            backup.name,
        )
        for backup in backups
    )
    assert {backup.read_bytes() for backup in backups} == {original, first_result}
