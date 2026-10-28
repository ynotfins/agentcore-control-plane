param(
  [string]$PostgresBin = "F:\PostgreSQL18\bin",
  [int]$PostgresPort = 55433,
  [string]$ProjectRoot = "D:\github\agentcore-control-plane",
  [string]$PowerShell7Path = "C:\Program Files\PowerShell\7\pwsh.exe",
  [switch]$IncludeContextFabricReadiness,
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
  $pgOutput = Invoke-AgentCoreNative -Command $pgIsReady -Arguments @("-h", "127.0.0.1", "-p", [string]$PostgresPort, "-d", "agent_core")
  Add-AgentCoreResult $results "postgres readiness" ($pgOutput.ExitCode -eq 0) $pgOutput.Output
} else {
  Add-AgentCoreResult $results "postgres readiness" $false "pg_isready.exe not found at $pgIsReady"
}

$bifrostOutput = Invoke-AgentCoreNative -Command $PowerShell7Path -Arguments @("-NoProfile", "-NonInteractive", "-File", (Join-Path $repoOps "bifrost\Test-AgentCoreBifrostGateway.ps1"), "-RepoRoot", $ProjectRoot)
Add-AgentCoreResult $results "bifrost gateway validator" ($bifrostOutput.ExitCode -eq 0) $bifrostOutput.Output

$projectionOutput = Invoke-AgentCoreNative -Command "powershell.exe" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $repoOps "Test-AgentCoreMemoryProjection.ps1"), "-ProjectRoot", $ProjectRoot)
Add-AgentCoreResult $results "memory projection validator" ($projectionOutput.ExitCode -eq 0) $projectionOutput.Output

if ($IncludeContextFabricReadiness) {
  $contextFabricOutput = Invoke-AgentCoreNative -Command $PowerShell7Path -Arguments @("-NoProfile", "-NonInteractive", "-File", (Join-Path $repoOps "Test-AgentCoreContextFabricReadiness.ps1"))
  Add-AgentCoreResult $results "context-fabric readiness" ($contextFabricOutput.ExitCode -eq 0) $contextFabricOutput.Output
}

$liveClientAdoptionPassed = $true
if ($IncludeLiveClientAdoption) {
  $liveClientAdoptionOutput = Invoke-AgentCoreNative -Command $PowerShell7Path -Arguments @("-NoProfile", "-NonInteractive", "-File", (Join-Path $repoOps "Test-AgentCoreLiveClientAdoption.ps1"))
  $liveClientAdoptionPassed = ($liveClientAdoptionOutput.ExitCode -eq 0)
  Add-AgentCoreResult $results "live client adoption" $liveClientAdoptionPassed $liveClientAdoptionOutput.Output
}

$allPassed = -not ($results | Where-Object { -not $_.passed })
$results | ConvertTo-Json -Depth 8
if (-not $allPassed) {
  exit 1
}
