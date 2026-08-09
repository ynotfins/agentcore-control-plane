<#
.SYNOPSIS
  Build the final AgentCore/Swarm runtime restore-point report after live acceptance.

.DESCRIPTION
  Defaults to stdout. Writes a report only when -OutFile is explicitly provided.
  Does not mutate services, scheduled tasks, IDE configs, databases, or Swarm roots.
  Sally/Swarm evidence is linked by path; this script does not create or validate
  Swarm-owned canaries.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$SallyAcceptancePath = '',
  [string]$LangGraphCanaryPath = '',
  [string]$SwarmClawCanaryPath = '',
  [string]$OutFile = ''
)

$ErrorActionPreference = 'Stop'

function Get-CommandText {
  param([string]$Executable, [string[]]$Arguments)
  try {
    $output = & $Executable @Arguments 2>&1
    return [pscustomobject]@{
      ExitCode = $LASTEXITCODE
      Text = (($output | Out-String).Trim())
    }
  } catch {
    return [pscustomobject]@{
      ExitCode = 1
      Text = $_.Exception.Message
    }
  }
}

function Get-Sha256Status {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    return [pscustomobject]@{ Path = $Path; Exists = $false; Sha256 = ''; Bytes = 0 }
  }
  $item = Get-Item -LiteralPath $Path
  $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $Path
  return [pscustomobject]@{ Path = $Path; Exists = $true; Sha256 = $hash.Hash; Bytes = $item.Length }
}

function Get-TaskStatus {
  param([string]$TaskName)
  try {
    $task = Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName $TaskName -ErrorAction Stop
    $info = Get-ScheduledTaskInfo -TaskPath '\AgentCore\' -TaskName $TaskName -ErrorAction Stop
    return [pscustomobject]@{
      TaskName = $TaskName
      Exists = $true
      State = [string]$task.State
      LastTaskResult = [string]$info.LastTaskResult
      LastRunTime = [string]$info.LastRunTime
    }
  } catch {
    return [pscustomobject]@{
      TaskName = $TaskName
      Exists = $false
      State = 'missing'
      LastTaskResult = ''
      LastRunTime = ''
    }
  }
}

function Get-EvidencePathStatus {
  param([string]$Label, [string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path)) {
    return [pscustomobject]@{ Label = $Label; Path = ''; Exists = $false; Status = 'not_provided' }
  }
  return [pscustomobject]@{
    Label = $Label
    Path = $Path
    Exists = (Test-Path -LiteralPath $Path)
    Status = if (Test-Path -LiteralPath $Path) { 'present' } else { 'missing' }
  }
}

function Get-MorningReadiness {
  $checker = Join-Path $RepoRoot 'ops\bifrost\Test-AgentCoreMorningReadiness.ps1'
  if (-not (Test-Path -LiteralPath $checker -PathType Leaf)) {
    return [pscustomobject]@{ Status = 'missing_checker'; Json = '' }
  }
  $pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
  if (-not $pwsh) {
    $pwsh = (Get-Command powershell -ErrorAction SilentlyContinue).Source
  }
  if (-not $pwsh) {
    return [pscustomobject]@{ Status = 'missing_powershell'; Json = '' }
  }
  $output = & $pwsh -NoProfile -File $checker -Json 2>&1
  $text = ($output | Out-String).Trim()
  try {
    $parsed = $text | ConvertFrom-Json -ErrorAction Stop
    return [pscustomObject]@{ Status = [string]$parsed.status; Json = $text }
  } catch {
    return [pscustomobject]@{ Status = 'parse_failed'; Json = $text }
  }
}

function Format-HashTable {
  param($Rows)
  $lines = [System.Collections.Generic.List[string]]::new()
  $lines.Add('| Path | Exists | SHA-256 | Bytes |') | Out-Null
  $lines.Add('| --- | --- | --- | --- |') | Out-Null
  foreach ($row in $Rows) {
    $lines.Add(('| `{0}` | {1} | `{2}` | {3} |' -f $row.Path, $row.Exists, $row.Sha256, $row.Bytes)) | Out-Null
  }
  return ($lines -join [Environment]::NewLine)
}

function Format-TaskTable {
  param($Rows)
  $lines = [System.Collections.Generic.List[string]]::new()
  $lines.Add('| Task | Exists | State | Last result | Last run |') | Out-Null
  $lines.Add('| --- | --- | --- | --- | --- |') | Out-Null
  foreach ($row in $Rows) {
    $lines.Add(('| `{0}` | {1} | {2} | `{3}` | `{4}` |' -f $row.TaskName, $row.Exists, $row.State, $row.LastTaskResult, $row.LastRunTime)) | Out-Null
  }
  return ($lines -join [Environment]::NewLine)
}

function Format-EvidenceTable {
  param($Rows)
  $lines = [System.Collections.Generic.List[string]]::new()
  $lines.Add('| Evidence | Status | Path |') | Out-Null
  $lines.Add('| --- | --- | --- |') | Out-Null
  foreach ($row in $Rows) {
    $pathText = if ([string]::IsNullOrWhiteSpace($row.Path)) { '' } else { ('`{0}`' -f $row.Path) }
    $lines.Add(('| {0} | {1} | {2} |' -f $row.Label, $row.Status, $pathText)) | Out-Null
  }
  return ($lines -join [Environment]::NewLine)
}

$timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
$gitHead = Get-CommandText 'git' @('-C', $RepoRoot, 'rev-parse', 'HEAD')
$gitBranch = Get-CommandText 'git' @('-C', $RepoRoot, 'branch', '--show-current')
$gitStatus = Get-CommandText 'git' @('-C', $RepoRoot, 'status', '--short', '--branch')
$morning = Get-MorningReadiness

$hashes = @(
  Get-Sha256Status (Join-Path $RepoRoot 'renderers\bifrost\config.json')
  Get-Sha256Status (Join-Path $RuntimeRoot 'config.json')
  Get-Sha256Status (Join-Path $RuntimeRoot 'config\config.json')
)

$tasks = @(
  Get-TaskStatus 'AgentCore-Bifrost-Gateway'
  Get-TaskStatus 'AgentCore-Bifrost-Watchdog'
)

$evidence = @(
  Get-EvidencePathStatus 'Sally full Swarm acceptance' $SallyAcceptancePath
  Get-EvidencePathStatus 'LangGraph production canary' $LangGraphCanaryPath
  Get-EvidencePathStatus 'SwarmClaw autonomous canary' $SwarmClawCanaryPath
)

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# AgentCore Runtime Restore-Point Report') | Out-Null
$lines.Add('') | Out-Null
$lines.Add(('**Timestamp:** {0}' -f $timestamp)) | Out-Null
$lines.Add(('**Repository:** `@{0}`' -f $RepoRoot)) | Out-Null
$lines.Add(('**Git branch:** `{0}`' -f $gitBranch.Text)) | Out-Null
$lines.Add(('**Git HEAD:** `{0}`' -f $gitHead.Text)) | Out-Null
$lines.Add(('**Morning readiness status:** `{0}`' -f $morning.Status)) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Git state') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('```text') | Out-Null
$lines.Add($gitStatus.Text) | Out-Null
$lines.Add('```') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Bifrost config hashes') | Out-Null
$lines.Add('') | Out-Null
$lines.Add((Format-HashTable $hashes)) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Scheduled tasks') | Out-Null
$lines.Add('') | Out-Null
$lines.Add((Format-TaskTable $tasks)) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Acceptance evidence paths') | Out-Null
$lines.Add('') | Out-Null
$lines.Add((Format-EvidenceTable $evidence)) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Morning readiness JSON') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('```json') | Out-Null
$lines.Add($morning.Json) | Out-Null
$lines.Add('```') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Closeout rule') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('Do not treat this restore point as production-ready unless morning readiness is `READY` and all three acceptance evidence paths are present.') | Out-Null

$report = $lines -join [Environment]::NewLine

if ([string]::IsNullOrWhiteSpace($OutFile)) {
  $report
} else {
  $parent = Split-Path -Parent $OutFile
  if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    [IO.Directory]::CreateDirectory($parent) | Out-Null
  }
  [IO.File]::WriteAllText($OutFile, $report, [Text.UTF8Encoding]::new($false))
  Write-Host "RESTORE_POINT_REPORT_WRITTEN $OutFile"
}
