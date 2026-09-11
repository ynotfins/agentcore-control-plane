<#
.SYNOPSIS
  Install the AgentCore Serena HTTP session shim runtime dirs and hidden logon scheduled task.

.NOTES
  Does not print secret values.
  Does not enable filesystem/depwire/tentra/context-fabric/github-mcp.
  Does not touch Swarm roots.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\serena-shim',
  [string]$TaskName = 'AgentCore-Serena-Session-Shim',
  [string]$TaskPath = '\AgentCore\',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 18090,
  [switch]$SkipScheduledTask,
  [switch]$TestMode,
  [switch]$EmitTaskSpecs,
  [string]$TaskSpecPowerShellPath = ''
)

$ErrorActionPreference = 'Stop'

function Write-AgentCoreInfo([string]$Message) {
  Write-Host "[Install-AgentCoreSerenaSessionShim] $Message"
}

function ConvertTo-AgentCoreCanonicalPath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return '' }
  try { return [IO.Path]::GetFullPath($Path).TrimEnd('\', '/') } catch { return '' }
}

function Resolve-InstallerPowerShellPath {
  $pwsh = (Get-Command 'pwsh.exe' -ErrorAction SilentlyContinue)?.Source
  if (-not [string]::IsNullOrWhiteSpace($pwsh)) { return $pwsh }
  $fallback = 'C:\Program Files\PowerShell\7\pwsh.exe'
  if (Test-Path -LiteralPath $fallback -PathType Leaf) { return $fallback }
  throw 'pwsh.exe not found for Serena shim scheduled task.'
}

function New-SerenaShimTaskSpec([string]$PowerShellPath) {
  $launchScript = Join-Path $PSScriptRoot 'Launch-AgentCoreSerenaSessionShim.ps1'
  $arguments = @(
    '-NoProfile',
    '-NonInteractive',
    '-WindowStyle Hidden',
    '-ExecutionPolicy Bypass',
    '-File', "`"$launchScript`"",
    '-RepoRoot', "`"$RepoRoot`"",
    '-RuntimeRoot', "`"$RuntimeRoot`"",
    '-HostAddress', $HostAddress,
    '-Port', ([string]$Port)
  ) -join ' '
  return [ordered]@{
    action = [ordered]@{
      executable = $PowerShellPath
      arguments = $arguments
      working_directory = $RuntimeRoot
    }
    trigger = [ordered]@{ type = 'logon'; user = $env:USERNAME }
    settings = [ordered]@{
      allow_start_if_on_batteries = $true
      dont_stop_if_going_on_batteries = $true
      execution_time_limit_seconds = 0
      restart_count = 999
      restart_interval_seconds = 60
      start_when_available = $true
      multiple_instances = 'IgnoreNew'
      hidden = $true
    }
    principal = [ordered]@{
      user_id = $env:USERNAME
      logon_type = 'Interactive'
      run_level = 'Limited'
    }
  }
}

$RepoRoot = ConvertTo-AgentCoreCanonicalPath $RepoRoot
$RuntimeRoot = ConvertTo-AgentCoreCanonicalPath $RuntimeRoot
$shimScript = Join-Path $RepoRoot 'scripts\bifrost\serena_session_shim.py'
$pythonExe = Join-Path $RepoRoot 'scripts\.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $shimScript -PathType Leaf)) {
  throw "Missing Serena shim script: $shimScript"
}
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
  throw "Missing repo venv python: $pythonExe"
}

New-Item -ItemType Directory -Force -Path `
  (Join-Path $RuntimeRoot 'logs'),
  (Join-Path $RuntimeRoot 'state') | Out-Null
Write-AgentCoreInfo "Runtime directories ready under $RuntimeRoot"

$powerShellPath = if (-not [string]::IsNullOrWhiteSpace($TaskSpecPowerShellPath)) {
  $TaskSpecPowerShellPath
} else {
  Resolve-InstallerPowerShellPath
}
$spec = New-SerenaShimTaskSpec -PowerShellPath $powerShellPath

if ($EmitTaskSpecs -or $TestMode) {
  $payload = [ordered]@{
    task_name = $TaskName
    task_path = $TaskPath
    repo_root = $RepoRoot
    runtime_root = $RuntimeRoot
    host = $HostAddress
    port = $Port
    python_exe = $pythonExe
    shim_script = $shimScript
    task = $spec
  }
  $payload | ConvertTo-Json -Depth 8
  if ($EmitTaskSpecs -and -not $TestMode) { return }
  if ($TestMode) { return }
}

if ($SkipScheduledTask) {
  Write-AgentCoreInfo 'SkipScheduledTask set; runtime dirs only.'
  return
}

$action = New-ScheduledTaskAction `
  -Execute ([string]$spec.action.executable) `
  -Argument ([string]$spec.action.arguments) `
  -WorkingDirectory ([string]$spec.action.working_directory)
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([string]$spec.trigger.user)
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RestartCount ([int]$spec.settings.restart_count) `
  -RestartInterval (New-TimeSpan -Seconds ([int]$spec.settings.restart_interval_seconds)) `
  -ExecutionTimeLimit ([TimeSpan]::Zero) `
  -MultipleInstances IgnoreNew `
  -Hidden
$principal = New-ScheduledTaskPrincipal `
  -UserId ([string]$spec.principal.user_id) `
  -LogonType Interactive `
  -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal

Register-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -InputObject $task -Force | Out-Null
Write-AgentCoreInfo "Registered scheduled task $TaskPath$TaskName (Hidden=$([bool]$spec.settings.hidden))"
