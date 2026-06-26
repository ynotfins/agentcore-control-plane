param(
  [string]$PostgresBin = "F:\AgentCore\postgres_runtime_engine\pgsql\bin",
  [string]$SwarmRecallConfigPath = "F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json",
  [string]$SwarmVaultRepoRoot = "D:\github\vendor\swarm\swarmvault",
  [string]$SwarmVaultRoot = "F:\AgentCore\agentmemory\swarmvault"
)

$ErrorActionPreference = "Stop"

function Add-AgentCoreResult {
  param(
    [System.Collections.Generic.List[object]]$Results,
    [string]$Name,
    [bool]$Passed,
    [string]$Detail
  )
  $Results.Add([pscustomobject]@{
    name = $Name
    passed = $Passed
    detail = $Detail
  }) | Out-Null
}

$results = [System.Collections.Generic.List[object]]::new()
$repoOps = Split-Path -Parent $PSCommandPath

$pgIsReady = Join-Path $PostgresBin "pg_isready.exe"
if (Test-Path -LiteralPath $pgIsReady) {
  $pgOutput = & $pgIsReady -h 127.0.0.1 -p 55432 2>&1
  Add-AgentCoreResult $results "postgres readiness" ($LASTEXITCODE -eq 0) (($pgOutput -join "`n").Trim())
} else {
  Add-AgentCoreResult $results "postgres readiness" $false "pg_isready.exe not found at $pgIsReady"
}

$recallOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoOps "Test-AgentCoreSwarmRecall.ps1") -ConfigPath $SwarmRecallConfigPath 2>&1
Add-AgentCoreResult $results "swarmrecall validator" ($LASTEXITCODE -eq 0) (($recallOutput -join "`n").Trim())

$vaultOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoOps "Test-AgentCoreSwarmVault.ps1") -RepoRoot $SwarmVaultRepoRoot -VaultRoot $SwarmVaultRoot 2>&1
Add-AgentCoreResult $results "swarmvault validator" ($LASTEXITCODE -eq 0) (($vaultOutput -join "`n").Trim())

$allPassed = -not ($results | Where-Object { -not $_.passed })
$results | ConvertTo-Json -Depth 8
if (-not $allPassed) {
  exit 1
}
