# Read the key inventory / memory / rollout docs

function Peek-File($p, $n = 200) {
    if (-not (Test-Path $p)) { Write-Host "MISSING: $p"; return }
    $item = Get-Item $p
    Write-Host "`n=========== FILE: $p (size=$($item.Length)) ==========="
    $lines = Get-Content $p -TotalCount $n -ErrorAction SilentlyContinue
    foreach ($line in $lines) { Write-Host $line }
}

Peek-File 'D:\github\agentcore-control-plane\docs\memory_system.md' 200
Peek-File 'D:\github\agentcore-control-plane\docs\rollout-runbook.md' 80
Peek-File 'D:\github\agentcore-control-plane\docs\SWARMVAULT_SOURCE_REGISTRATION.md' 80
Peek-File 'D:\github\agentcore-control-plane\docs\SYSTEM_HANDOVER_BLUEPRINT.md' 250
Peek-File 'D:\github\agentcore-control-plane\artifacts\rollout-2026-06-30\ROLLOUT_REPORT.md' 200
Peek-File 'D:\github\agentcore-control-plane\database-plan.md' 200
Peek-File 'D:\github\agentcore-control-plane\contracts\global-memory-database-contract.json' 80
Peek-File 'D:\github\agentcore-control-plane\registry\tool-registry.json' 200
Peek-File 'D:\github\agentcore-control-plane\supervisor\servers.json' 100
Peek-File 'D:\github\agentcore-control-plane\contracts\master-mcp-server-config.json' 200

Write-Host "`n===== End ====="