#Requires -Version 5.1
<#
.SYNOPSIS
  Shared helpers for conhost --headless silent scheduled-task actions.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-AgentCoreRepoRootFromCommon {
  if ((Split-Path -Leaf $PSScriptRoot) -eq 'ops') {
    return (Split-Path -Parent $PSScriptRoot)
  }
  return (Split-Path -Parent $PSScriptRoot)
}

function Get-AgentCoreSilentPolicyContract {
  $root = if ($env:AGENTCORE_REPO_ROOT) { $env:AGENTCORE_REPO_ROOT } else { Get-AgentCoreRepoRootFromCommon }
  $path = Join-Path $root 'contracts\agentcore-silent-automation-policy.json'
  if (-not (Test-Path -LiteralPath $path)) { throw "Missing silent automation policy contract: $path" }
  return (Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Get-AgentCoreJsonPropertyValue {
  param($Object, [Parameter(Mandatory)][string]$Name, $Default = $null)
  if ($null -eq $Object) { return $Default }
  if ($Object.PSObject.Properties.Name -contains $Name) { return $Object.$Name }
  return $Default
}

function Get-AgentCoreSilentContractRepairBool {
  param($Entry, [Parameter(Mandatory)][string]$Name, [bool]$Default = $false)
  $repair = Get-AgentCoreJsonPropertyValue -Object $Entry -Name 'repair'
  $value = Get-AgentCoreJsonPropertyValue -Object $repair -Name $Name
  if ($null -eq $value) { return $Default }
  return [bool]$value
}

function Test-AgentCoreSilentPreserveFileArgs {
  param($Entry)
  $onTask = Get-AgentCoreJsonPropertyValue -Object $Entry -Name 'preserve_file_args'
  if ($null -ne $onTask) { return [bool]$onTask }
  $repair = Get-AgentCoreJsonPropertyValue -Object $Entry -Name 'repair'
  $onRepair = Get-AgentCoreJsonPropertyValue -Object $repair -Name 'preserve_file_args'
  if ($null -ne $onRepair) { return [bool]$onRepair }
  return $false
}

function Get-AgentCoreConhostPath {
  $candidates = @((Join-Path $env:Windir 'System32\conhost.exe'), 'C:\Windows\System32\conhost.exe')
  foreach ($c in $candidates) { if (Test-Path -LiteralPath $c -PathType Leaf) { return $c } }
  throw 'conhost.exe not found'
}

function Get-AgentCorePwshPath {
  $candidates = @('C:\Program Files\PowerShell\7\pwsh.exe', (Join-Path $env:ProgramFiles 'PowerShell\7\pwsh.exe'))
  foreach ($c in $candidates) { if (Test-Path -LiteralPath $c -PathType Leaf) { return $c } }
  $cmd = Get-Command 'pwsh.exe' -ErrorAction SilentlyContinue
  if ($cmd -and (Test-Path -LiteralPath $cmd.Source)) { return $cmd.Source }
  throw 'pwsh.exe not found'
}

function New-AgentCoreSilentConhostArgument {
  param([Parameter(Mandatory)][string]$PwshPath, [Parameter(Mandatory)][string]$PwshArgumentTail)
  $tail = $PwshArgumentTail.Trim()
  if ($tail -notmatch '(?i)-WindowStyle\s+Hidden') {
    if ($tail.Length -gt 0) {
      $tail = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass $tail"
    } else {
      $tail = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass'
    }
  }
  return "--headless `"$PwshPath`" $tail"
}

function New-AgentCoreSilentPwshFileArguments {
  param([Parameter(Mandatory)][string]$FilePath, [string]$ExtraArgs = '')
  $arg = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$FilePath`""
  if (-not [string]::IsNullOrWhiteSpace($ExtraArgs)) { $arg = "$arg $ExtraArgs" }
  return $arg
}

function ConvertTo-AgentCoreSilentPwshArguments {
  param([Parameter(Mandatory)][string]$ExistingArguments)
  $a = $ExistingArguments.Trim()
  if ($a -match '(?i)^"?((?:.+?\\)?(?:pwsh|powershell)\.exe)"?\s+(.*)$') { $a = $Matches[2] }
  if ($a -notmatch '(?i)-WindowStyle\s+Hidden') {
    if ($a -match '(?i)^-NoProfile') { $a = $a -replace '(?i)^-NoProfile', '-NoProfile -NonInteractive -WindowStyle Hidden' }
    else { $a = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass $a" }
  }
  if ($a -notmatch '(?i)-ExecutionPolicy\s+Bypass') {
    $a = $a -replace '(?i)-WindowStyle\s+Hidden', '-WindowStyle Hidden -ExecutionPolicy Bypass'
  }
  return $a.Trim()
}

function Set-AgentCoreScheduledTaskActionViaXml {
  param([Parameter(Mandatory)][string]$TaskName, [Parameter(Mandatory)][string]$TaskPath, [Parameter(Mandatory)][string]$Execute, [Parameter(Mandatory)][string]$Arguments, [string]$WorkingDirectory = '')
  [xml]$xml = (Export-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath)
  $exec = $xml.Task.Actions.Exec
  if ($null -eq $exec) { throw "Task $TaskPath$TaskName has no Exec action" }
  $exec.Command = $Execute
  $exec.Arguments = $Arguments
  if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) { $exec.WorkingDirectory = $WorkingDirectory }
  $xml.Task.Settings.Hidden = 'true'
  Register-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -Xml $xml.OuterXml -Force | Out-Null
}

# Changes ONLY window visibility (conhost --headless + Hidden). No stop, disable, or schedule changes.
function Set-AgentCoreSilentConhostTask {
  param([Parameter(Mandatory)][string]$TaskName, [string]$TaskPath = '\', [string]$FilePath = '', [string]$ExtraArgs = '', [switch]$PreserveFileArgs)
  $t = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction Stop
  $conhost = Get-AgentCoreConhostPath
  $pwsh = Get-AgentCorePwshPath
  $action0 = $t.Actions | Select-Object -First 1
  $wd = [string]$action0.WorkingDirectory
  if ($PreserveFileArgs) {
    $existingArgs = [string]$action0.Arguments
    if ($existingArgs -match '(?i)--headless\s+"[^"]+"\s+(.*)$') { $inner = $Matches[1] }
    elseif ([string]$action0.Execute -match '(?i)(powershell|pwsh)\.exe$') { $inner = [string]$action0.Arguments }
    else { $inner = $existingArgs }
    $pwshTail = ConvertTo-AgentCoreSilentPwshArguments -ExistingArguments $inner
  } elseif (-not [string]::IsNullOrWhiteSpace($FilePath)) {
    $pwshTail = New-AgentCoreSilentPwshFileArguments -FilePath $FilePath -ExtraArgs $ExtraArgs
  } else { throw 'Set-AgentCoreSilentConhostTask requires FilePath or -PreserveFileArgs' }
  $conhostArgs = New-AgentCoreSilentConhostArgument -PwshPath $pwsh -PwshArgumentTail $pwshTail
  Set-AgentCoreScheduledTaskActionViaXml -TaskName $TaskName -TaskPath $TaskPath -Execute $conhost -Arguments $conhostArgs -WorkingDirectory $wd
}

function Test-AgentCoreTaskNameMatchesSilentPolicy {
  param([Parameter(Mandatory)][string]$TaskName, $Policy = $null)
  if (-not $Policy) { $Policy = Get-AgentCoreSilentPolicyContract }
  $patterns = @(Get-AgentCoreJsonPropertyValue -Object $Policy -Name 'name_match_patterns' -Default @())
  foreach ($p in $patterns) { if ($TaskName -like "*$p*") { return $true } }
  return $false
}

function Get-AgentCoreTaskSilentReason {
  param($ScheduledTask, $Policy = $null)
  if (-not $ScheduledTask) { return 'task_missing' }
  if (-not $Policy) { $Policy = Get-AgentCoreSilentPolicyContract }
  if (-not $ScheduledTask.Settings.Enabled) { return $null }
  if (-not [bool]$ScheduledTask.Settings.Hidden) { return 'settings_not_hidden' }
  $sawShell = $false
  foreach ($action in @($ScheduledTask.Actions)) {
    $exe = [string]$action.Execute
    $exeLeaf = [IO.Path]::GetFileName($exe)
    $skip = $false
    $nonShellList = @(Get-AgentCoreJsonPropertyValue -Object $Policy -Name 'non_shell_action_executables' -Default @())
    foreach ($nonShell in $nonShellList) { if ($exeLeaf -ieq $nonShell) { $skip = $true; break } }
    if ($skip) { continue }
    $args = [string]$action.Arguments
    if ($exe -match '(?i)(?:^|[\\/])(powershell|pwsh)\.exe$') { return 'direct_shell_executable' }
    if ($exe -match '(?i)conhost\.exe$') {
      $sawShell = $true
      if ($args -notmatch '(?i)--headless') { return 'conhost_missing_headless' }
      if ($args -notmatch '(?i)(powershell|pwsh)\.exe') { return 'conhost_missing_pwsh' }
      if ($args -notmatch '(?i)-WindowStyle\s+Hidden') { return 'pwsh_missing_hidden_window' }
    }
  }
  if (-not $sawShell) { return 'no_conhost_shell_action' }
  return $null
}

function Test-AgentCoreTaskIsSilent {
  param([Parameter(Mandatory)]$ScheduledTask, $Policy = $null)
  if (-not $Policy) { $Policy = Get-AgentCoreSilentPolicyContract }
  if (-not $ScheduledTask.Settings.Enabled) { return $true }
  if (-not [bool]$ScheduledTask.Settings.Hidden) { return $false }
  $sawShell = $false
  foreach ($action in @($ScheduledTask.Actions)) {
    $exe = [string]$action.Execute
    $exeLeaf = [IO.Path]::GetFileName($exe)
    $skip = $false
    $nonShellList = @(Get-AgentCoreJsonPropertyValue -Object $Policy -Name 'non_shell_action_executables' -Default @())
    foreach ($nonShell in $nonShellList) { if ($exeLeaf -ieq $nonShell) { $skip = $true; break } }
    if ($skip) { continue }
    $args = [string]$action.Arguments
    if ($exe -match '(?i)(?:^|[\\/])(powershell|pwsh)\.exe$') { return $false }
    if ($exe -match '(?i)conhost\.exe$') {
      $sawShell = $true
      if ($args -notmatch '(?i)--headless') { return $false }
      if ($args -notmatch '(?i)(powershell|pwsh)\.exe') { return $false }
      if ($args -notmatch '(?i)-WindowStyle\s+Hidden') { return $false }
    }
  }
  return $true
}

function Write-AgentCoreSilentAutomationAudit {
  param([Parameter(Mandatory)][string]$Message, $Policy = $null)
  if (-not $Policy) { $Policy = Get-AgentCoreSilentPolicyContract }
  $log = [string](Get-AgentCoreJsonPropertyValue -Object $Policy -Name 'audit_log_path' -Default '')
  if ([string]::IsNullOrWhiteSpace($log)) { return }
  $dir = Split-Path -Parent $log
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Add-Content -LiteralPath $log -Value ("{0:u} {1}" -f (Get-Date).ToUniversalTime(), $Message) -Encoding UTF8
}

function Find-AgentCoreSilentContractTask {
  param([Parameter(Mandatory)][string]$TaskName, [string]$TaskPath = '', $Policy = $null)
  if (-not $Policy) { $Policy = Get-AgentCoreSilentPolicyContract }
  foreach ($entry in @($Policy.tasks)) {
    $entryName = [string](Get-AgentCoreJsonPropertyValue -Object $entry -Name 'task_name' -Default '')
    if ($entryName -ne $TaskName) { continue }
    if (-not [string]::IsNullOrWhiteSpace($TaskPath)) {
      $normalized = if ([string]::IsNullOrWhiteSpace($TaskPath)) { '\' } else { $TaskPath }
      $entryPathRaw = Get-AgentCoreJsonPropertyValue -Object $entry -Name 'task_path'
      $entryPath = if ([string]::IsNullOrWhiteSpace($entryPathRaw)) { '\' } else { [string]$entryPathRaw }
      if ($entryPath -ne $normalized) { continue }
    }
    return $entry
  }
  return $null
}
