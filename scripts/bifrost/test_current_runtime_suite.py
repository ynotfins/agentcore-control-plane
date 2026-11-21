from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "ops" / "Test-AgentCoreRuntimeSuite.ps1"
PROJECTION = ROOT / "ops" / "Test-AgentCoreMemoryProjection.ps1"


def test_runtime_suite_uses_pg18_and_current_projection_contract() -> None:
    suite = SUITE.read_text(encoding="utf-8")
    projection = PROJECTION.read_text(encoding="utf-8")
    combined = suite + projection
    assert "F:\\PostgreSQL18\\bin" in combined
    assert "55433" in combined
    assert "Test-AgentCoreMemoryProjection.ps1" in suite
    assert "Test-AgentCoreBifrostGateway.ps1" in suite
    assert "IncludeContextFabricReadiness" in suite
    assert "PowerShell7Path" in suite
    assert "55432" not in combined
    assert "Test-AgentCoreSwarmVault.ps1" not in combined
    assert "F:\\AgentCore\\agentmemory\\swarmvault" not in combined
    assert "agentmemory\\swarmrecall" not in combined
