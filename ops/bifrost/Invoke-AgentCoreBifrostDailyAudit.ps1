<#
.SYNOPSIS
  Daily Bifrost MCP health audit with bounded self-healing.

.DESCRIPTION
  Validates the AgentCore Bifrost source contracts and live gateway. When
  -Repair is set, only Bifrost runtime drift is repaired: backup current runtime
  config, render from the repository authority, restart the scheduled gateway,
  and re-run postflight. IDE configs and dormant MCP activation are never
  changed by this script.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$BaseUrl = 'http://127.0.0.1:8080',
  [string]$LogRoot = 'F:\AgentCore\runtime\bifrost\audits',
  [switch]$Repair
)

$ErrorActionPreference = 'Stop'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$logPath = Join-Path $LogRoot "$stamp-bifrost-daily-audit.log"

function Invoke-Step {
  param(
    [string]$Label,
    [scriptblock]$Block
  )
  Write-Host "== $Label =="
  & $Block
}

Push-Location $RepoRoot
try {
  Start-Transcript -Path $logPath -Force | Out-Null
  Write-Host "AgentCore Bifrost daily audit started: $stamp"
  Write-Host "RepoRoot=$RepoRoot"
  Write-Host "RuntimeRoot=$RuntimeRoot"
  Write-Host "Repair=$($Repair.IsPresent)"

  Invoke-Step 'Validate source contracts' {
    python scripts\bifrost\validate_contracts.py
    if ($LASTEXITCODE -ne 0) { throw "validate_contracts.py failed with $LASTEXITCODE" }
  }

  $initialOk = $true
  try {
    Invoke-Step 'Live gateway postflight' {
      & .\ops\bifrost\Test-AgentCoreBifrostGateway.ps1 -RuntimeRoot $RuntimeRoot -BaseUrl $BaseUrl -RepoRoot $RepoRoot
      if ($LASTEXITCODE -ne 0) { throw "gateway postflight failed with $LASTEXITCODE" }
    }
  } catch {
    $initialOk = $false
    Write-Host "Initial postflight failed: $($_.Exception.Message)"
  }

  if (-not $initialOk -and $Repair.IsPresent) {
    Invoke-Step 'Bounded Bifrost runtime repair' {
      & .\ops\bifrost\Backup-AgentCoreBifrostConfig.ps1 -RuntimeRoot $RuntimeRoot
      python scripts\bifrost\render_bifrost_config.py
      if ($LASTEXITCODE -ne 0) { throw "render_bifrost_config.py failed with $LASTEXITCODE" }
      & .\ops\bifrost\Stop-AgentCoreBifrostGateway.ps1 -RuntimeRoot $RuntimeRoot
      & .\ops\bifrost\Start-AgentCoreBifrostGateway.ps1 -RuntimeRoot $RuntimeRoot
    }
    Invoke-Step 'Post-repair gateway postflight' {
      & .\ops\bifrost\Test-AgentCoreBifrostGateway.ps1 -RuntimeRoot $RuntimeRoot -BaseUrl $BaseUrl -RepoRoot $RepoRoot
      if ($LASTEXITCODE -ne 0) { throw "post-repair gateway postflight failed with $LASTEXITCODE" }
    }
  } elseif (-not $initialOk) {
    throw 'Initial postflight failed and -Repair was not set.'
  }

  Write-Host 'RESULT: PASSED'
} catch {
  Write-Host "RESULT: FAILED $($_.Exception.Message)"
  throw
} finally {
  try { Stop-Transcript | Out-Null } catch { }
  Pop-Location
  Write-Host "Audit log: $logPath"
}
