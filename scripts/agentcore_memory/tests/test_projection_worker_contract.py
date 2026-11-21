from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WORKER = ROOT / "scripts" / "memory_platform" / "Invoke-M3ProjectionWorker.ps1"


def test_projection_worker_bounds_state_and_rejects_malformed_output() -> None:
    source = WORKER.read_text(encoding="utf-8")
    assert "$timelineLimit = 100" in source
    assert "Assert-ProjectionContent -Name 'global_state'" in source
    assert "forbidden control character" in source
    assert "unexpanded PowerShell placeholder" in source
    assert "IsReadOnly = $true" in source
    assert "`agentcore-memory`" not in source
    assert "(`$ProjectKey`)" not in source
    assert "—" not in source
    assert "â€”" not in source
