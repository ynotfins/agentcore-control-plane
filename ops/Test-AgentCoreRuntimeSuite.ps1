param(
  [string]$PostgresBin = "F:\AgentCore\postgres_runtime_engine\pgsql\bin",
  [string]$SwarmRecallConfigPath = "F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json",
  [string]$SwarmVaultRepoRoot = "D:\github\vendor\swarm\swarmvault",
  [string]$SwarmVaultRoot = "F:\AgentCore\agentmemory\swarmvault",
  [switch]$IncludeLiveClientAdoption
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

function Invoke-AgentCoreNative {
  param(
    [string]$Command,
    [string[]]$Arguments
  )

  $previousNativePref = $null
  $hadNativePref = Test-Path Variable:PSNativeCommandUseErrorActionPreference
  if ($hadNativePref) {
    $previousNativePref = $PSNativeCommandUseErrorActionPreference
    $PSNativeCommandUseErrorActionPreference = $false
  }
  try {
    $output = & $Command @Arguments 2>&1
    return [pscustomobject]@{
      ExitCode = $LASTEXITCODE
      Output = (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
    }
  } catch {
    return [pscustomobject]@{
      ExitCode = 1
      Output = $_.Exception.Message
    }
  } finally {
    if ($hadNativePref) {
      $PSNativeCommandUseErrorActionPreference = $previousNativePref
    }
  }
}

$results = [System.Collections.Generic.List[object]]::new()
$repoOps = Split-Path -Parent $PSCommandPath

$pgIsReady = Join-Path $PostgresBin "pg_isready.exe"
if (Test-Path -LiteralPath $pgIsReady) {
  $pgOutput = Invoke-AgentCoreNative -Command $pgIsReady -Arguments @("-h", "127.0.0.1", "-p", "55432")
  Add-AgentCoreResult $results "postgres readiness" ($pgOutput.ExitCode -eq 0) $pgOutput.Output
} else {
  Add-AgentCoreResult $results "postgres readiness" $false "pg_isready.exe not found at $pgIsReady"
}

$recallOutput = Invoke-AgentCoreNative -Command "powershell.exe" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $repoOps "Test-AgentCoreSwarmRecall.ps1"), "-ConfigPath", $SwarmRecallConfigPath)
Add-AgentCoreResult $results "swarmrecall validator" ($recallOutput.ExitCode -eq 0) $recallOutput.Output

$vaultOutput = Invoke-AgentCoreNative -Command "powershell.exe" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $repoOps "Test-AgentCoreSwarmVault.ps1"), "-RepoRoot", $SwarmVaultRepoRoot, "-VaultRoot", $SwarmVaultRoot)
Add-AgentCoreResult $results "swarmvault validator" ($vaultOutput.ExitCode -eq 0) $vaultOutput.Output

$projectionOutput = Invoke-AgentCoreNative -Command "powershell.exe" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $repoOps "Test-AgentCoreMemoryProjection.ps1"))
Add-AgentCoreResult $results "memory projection validator" ($projectionOutput.ExitCode -eq 0) $projectionOutput.Output

$contextFabricOutput = Invoke-AgentCoreNative -Command "powershell.exe" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $repoOps "Test-AgentCoreContextFabricReadiness.ps1"))
Add-AgentCoreResult $results "context-fabric readiness" ($contextFabricOutput.ExitCode -eq 0) $contextFabricOutput.Output

$liveClientAdoptionPassed = $true
if ($IncludeLiveClientAdoption) {
  $liveClientAdoptionOutput = Invoke-AgentCoreNative -Command "powershell.exe" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $repoOps "Test-AgentCoreLiveClientAdoption.ps1"))
  $liveClientAdoptionPassed = ($liveClientAdoptionOutput.ExitCode -eq 0)
  Add-AgentCoreResult $results "live client adoption" $liveClientAdoptionPassed $liveClientAdoptionOutput.Output
}

$allPassed = -not ($results | Where-Object { -not $_.passed })
$results | ConvertTo-Json -Depth 8
if (-not $allPassed) {
  exit 1
}
