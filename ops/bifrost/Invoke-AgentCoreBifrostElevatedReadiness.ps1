#Requires -Version 7.0
<#
.SYNOPSIS
  Run the elevated Bifrost gateway installer and restart-readiness validator.

.DESCRIPTION
  This helper can be launched from any current directory. If it is not already
  elevated, it starts an Administrator PowerShell child, waits for it, and then
  prints the latest readiness summary path. The elevated child runs the managed
  installer followed by Test-AgentCoreBifrostGateway.ps1 -RequireWatchdogEnabled.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$EvidenceRoot = '',
  [switch]$ElevatedChild
)

$ErrorActionPreference = 'Stop'

function Test-IsAdministrator {
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = [Security.Principal.WindowsPrincipal]::new($identity)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-PowerShellPath {
  $processPath = (Get-Process -Id $PID).Path
  if ($processPath -and (Test-Path -LiteralPath $processPath -PathType Leaf)) {
    return $processPath
  }
  $pwsh = Get-Command 'pwsh.exe' -ErrorAction SilentlyContinue
  if ($pwsh) { return $pwsh.Source }
  throw 'pwsh.exe not found.'
}

function Add-ArgumentPair([System.Collections.Generic.List[string]]$Arguments, [string]$Name, [string]$Value) {
  $Arguments.Add($Name) | Out-Null
  $Arguments.Add($Value) | Out-Null
}

function Get-TaskSummary {
  $tasks = @()
  foreach ($name in @('AgentCore-Bifrost-Gateway', 'AgentCore-Bifrost-Watchdog')) {
    try {
      $task = Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName $name -ErrorAction Stop
      $tasks += [pscustomobject]@{
        task_name = $name
        state = [string]$task.State
        enabled = [bool]$task.Settings.Enabled
        hidden = [bool]$task.Settings.Hidden
        multiple_instances = [string]$task.Settings.MultipleInstances
        execution_time_limit = [string]$task.Settings.ExecutionTimeLimit
        user_id = [string]$task.Principal.UserId
        logon_type = [string]$task.Principal.LogonType
        run_level = [string]$task.Principal.RunLevel
      }
    } catch {
      $tasks += [pscustomobject]@{
        task_name = $name
        error = $_.Exception.Message
      }
    }
  }
  return @($tasks)
}

if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) {
  $EvidenceRoot = Join-Path $RuntimeRoot 'evidence\bifrost-readiness'
}
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$summaryPath = Join-Path $EvidenceRoot "bifrost-readiness-$stamp.json"
$transcriptPath = Join-Path $EvidenceRoot "bifrost-readiness-$stamp.transcript.txt"

if (-not (Test-IsAdministrator)) {
  $pwsh = Get-PowerShellPath
  $argsList = [System.Collections.Generic.List[string]]::new()
  foreach ($arg in @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath)) {
    $argsList.Add($arg) | Out-Null
  }
  Add-ArgumentPair $argsList '-RuntimeRoot' $RuntimeRoot
  Add-ArgumentPair $argsList '-RepoRoot' $RepoRoot
  Add-ArgumentPair $argsList '-EvidenceRoot' $EvidenceRoot
  $argsList.Add('-ElevatedChild') | Out-Null

  Write-Host "[Readiness] Launching elevated Bifrost readiness runner. Approve the Windows UAC prompt."
  $proc = Start-Process -FilePath $pwsh -ArgumentList $argsList.ToArray() -Verb RunAs -Wait -PassThru
  $latest = Get-ChildItem -LiteralPath $EvidenceRoot -Filter 'bifrost-readiness-*.json' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if ($latest) {
    Write-Host "[Readiness] Latest summary: $($latest.FullName)"
    try {
      $summary = Get-Content -LiteralPath $latest.FullName -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 20
      if ($summary.ready_for_restart -eq $true) {
        Write-Host '[Readiness] RESULT: PASSED. Restart is allowed.'
        exit 0
      }
      Write-Host '[Readiness] RESULT: FAILED. Do not restart yet.'
      exit 1
    } catch {
      Write-Host "[Readiness] Could not parse latest summary: $($_.Exception.Message)"
    }
  }
  if ($proc.ExitCode -eq 0) { exit 0 }
  exit 1
}

Start-Transcript -LiteralPath $transcriptPath -Force | Out-Null
$installExit = 1
$validatorExit = 1
$installOutput = @()
$validatorOutput = @()
$errorText = $null

try {
  Set-Location -LiteralPath $RepoRoot
  $pwsh = Get-PowerShellPath
  $installScript = Join-Path $RepoRoot 'ops\bifrost\Install-AgentCoreBifrostGateway.ps1'
  $validatorScript = Join-Path $RepoRoot 'ops\bifrost\Test-AgentCoreBifrostGateway.ps1'

  Write-Host "[Readiness] Running installer: $installScript"
  $installOutput = @(& $pwsh -NoProfile -ExecutionPolicy Bypass -File $installScript -RuntimeRoot $RuntimeRoot -RepoRoot $RepoRoot 2>&1)
  $installExit = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
  $installOutput | ForEach-Object { Write-Host $_ }

  if ($installExit -eq 0) {
    Write-Host "[Readiness] Running validator: $validatorScript -RequireWatchdogEnabled"
    $validatorOutput = @(& $pwsh -NoProfile -ExecutionPolicy Bypass -File $validatorScript -RequireWatchdogEnabled 2>&1)
    $validatorExit = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    $validatorOutput | ForEach-Object { Write-Host $_ }
  }
} catch {
  $errorText = $_.Exception.Message
  Write-Host "[Readiness] ERROR: $errorText"
} finally {
  $summary = [ordered]@{
    schema = 'agentcore.bifrost.elevated_readiness.v1'
    generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    repo_root = $RepoRoot
    runtime_root = $RuntimeRoot
    evidence_root = $EvidenceRoot
    transcript_path = $transcriptPath
    elevated = [bool](Test-IsAdministrator)
    install_exit_code = $installExit
    validator_exit_code = $validatorExit
    ready_for_restart = [bool]($installExit -eq 0 -and $validatorExit -eq 0)
    error = $errorText
    scheduled_tasks = @(Get-TaskSummary)
    validator_tail = @($validatorOutput | Select-Object -Last 30 | ForEach-Object { [string]$_ })
  }
  $summary | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
  Write-Host "[Readiness] Summary: $summaryPath"
  Write-Host "[Readiness] Transcript: $transcriptPath"
  if ($summary.ready_for_restart) {
    Write-Host '[Readiness] RESULT: PASSED. Restart is allowed.'
  } else {
    Write-Host '[Readiness] RESULT: FAILED. Do not restart yet.'
  }
  Stop-Transcript | Out-Null
}

if ($installExit -eq 0 -and $validatorExit -eq 0) { exit 0 }
exit 1
