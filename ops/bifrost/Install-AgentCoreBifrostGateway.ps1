<#
.SYNOPSIS
  Install AgentCore Bifrost MCP Gateway runtime directories, config, and logon scheduled task.

.NOTES
  Does not print secret values.
  Does not touch SwarmRecall/SwarmVault/SwarmClaw product installs.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$WatchdogTaskName = 'AgentCore-Bifrost-Watchdog',
  [string]$TaskPath = '\AgentCore\',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080,
  [switch]$SkipScheduledTask,
  [switch]$TestMode,
  [switch]$TestPrivilegeDenied,
  [ValidateSet('None', 'GatewayRegistration', 'WatchdogRegistration', 'OperationalLogEnablement')]
  [string]$TestFailurePhase = 'None',
  [ValidateSet('Absent', 'Present', 'ExportFailure')]
  [string]$TestGatewayTaskModel = 'Absent',
  [ValidateSet('Absent', 'Present', 'ExportFailure')]
  [string]$TestWatchdogTaskModel = 'Absent',
  [switch]$EmitTaskSpecs,
  [string]$TaskSpecPowerShellPath = ''
)

$ErrorActionPreference = 'Stop'

function Write-AgentCoreInfo([string]$Message) {
  Write-Host "[Install-AgentCoreBifrostGateway] $Message"
}

function New-BifrostTaskSpecs([string]$PowerShellPath) {
  $launchScript = Join-Path $PSScriptRoot 'Launch-AgentCoreBifrostGateway.ps1'
  $watchdogScript = Join-Path $PSScriptRoot 'Invoke-AgentCoreBifrostWatchdog.ps1'
  return [ordered]@{
    gateway = [ordered]@{
      action = [ordered]@{
        executable = $PowerShellPath
        arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$launchScript`" -RuntimeRoot `"$RuntimeRoot`" -HostAddress $HostAddress -Port $Port"
        working_directory = $RuntimeRoot
      }
      trigger = [ordered]@{ type = 'logon'; user = $env:USERNAME }
      settings = [ordered]@{
        execution_time_limit_seconds = 0
        restart_count = 1
        restart_interval_seconds = 60
        multiple_instances = 'IgnoreNew'
      }
    }
    watchdog = [ordered]@{
      action = [ordered]@{
        executable = $PowerShellPath
        arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$watchdogScript`" -RuntimeRoot `"$RuntimeRoot`" -GatewayUrl http://${HostAddress}:${Port} -TaskPath `"$TaskPath`" -TaskName `"$TaskName`""
        working_directory = $RuntimeRoot
      }
      trigger = [ordered]@{ type = 'daily_repeating'; repetition_interval_seconds = 60; repetition_duration_seconds = 86400 }
      settings = [ordered]@{
        execution_time_limit_seconds = 60
        restart_count = 0
        multiple_instances = 'IgnoreNew'
      }
    }
    operational_logging = [ordered]@{ channel = 'Microsoft-Windows-TaskScheduler/Operational'; enable = $true }
  }
}

function Assert-InstallerPrivileges {
  if ($TestMode) {
    if ($TestPrivilegeDenied) { throw 'INSTALL_PRIVILEGE_PREFLIGHT_FAILED' }
    return
  }
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = [Security.Principal.WindowsPrincipal]::new($identity)
  if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'INSTALL_PRIVILEGE_PREFLIGHT_FAILED'
  }
}

function Initialize-TestTaskModel {
  if (-not $TestMode) { return }
  $script:TestTaskDefinitions = @{
    gateway = if ($TestGatewayTaskModel -eq 'Absent') { $null } else { 'gateway-original' }
    watchdog = if ($TestWatchdogTaskModel -eq 'Absent') { $null } else { 'watchdog-original' }
  }
}

function Write-TestTaskModel {
  if ($TestMode) {
    Write-Host ('INSTALL_TASK_MODEL ' + (@{ gateway = $script:TestTaskDefinitions.gateway; watchdog = $script:TestTaskDefinitions.watchdog } | ConvertTo-Json -Compress))
  }
}

function Get-TaskDefinitionBackup([string]$Name) {
  if ($TestMode) {
    $key = if ($Name -eq $TaskName) { 'gateway' } else { 'watchdog' }
    $model = if ($key -eq 'gateway') { $TestGatewayTaskModel } else { $TestWatchdogTaskModel }
    if ($model -eq 'Absent') {
      return [pscustomobject]@{ Name = $Name; Exists = $false; BackupAvailable = $true; Definition = $null }
    }
    if ($model -eq 'ExportFailure') {
      return [pscustomobject]@{ Name = $Name; Exists = $true; BackupAvailable = $false; Definition = $null }
    }
    return [pscustomobject]@{ Name = $Name; Exists = $true; BackupAvailable = $true; Definition = $script:TestTaskDefinitions[$key] }
  }
  try {
    $existing = Get-ScheduledTask -TaskPath $TaskPath -TaskName $Name -ErrorAction Stop
  } catch {
    if ($_.Exception.Message -match '(?i)not found|cannot find|does not exist|0x80070002') {
      return [pscustomobject]@{ Name = $Name; Exists = $false; BackupAvailable = $true; Definition = $null }
    }
    return [pscustomobject]@{ Name = $Name; Exists = $true; BackupAvailable = $false; Definition = $null }
  }
  if (-not $existing) {
    return [pscustomobject]@{ Name = $Name; Exists = $false; BackupAvailable = $true; Definition = $null }
  }
  try {
    $definition = Export-ScheduledTask -TaskPath $TaskPath -TaskName $Name -ErrorAction Stop
    $definition | Set-Content -LiteralPath (Join-Path $script:TaskBackupDirectory "$Name.xml") -Encoding utf8
    return [pscustomobject]@{ Name = $Name; Exists = $true; BackupAvailable = $true; Definition = $definition }
  } catch {
    return [pscustomobject]@{ Name = $Name; Exists = $true; BackupAvailable = $false; Definition = $null }
  }
}

function Restore-TaskDefinition($Backup) {
  $key = if ($Backup.Name -eq $TaskName) { 'gateway' } else { 'watchdog' }
  if ($TestMode) {
    $script:TestTaskDefinitions[$key] = if ($Backup.Exists) { $Backup.Definition } else { $null }
    return 'restored'
  }
  if ($Backup.Exists) {
    if (-not $Backup.BackupAvailable -or -not $Backup.Definition) { throw "INSTALL_TASK_BACKUP_FAILED $($Backup.Name)" }
    Register-ScheduledTask -TaskPath $TaskPath -TaskName $Backup.Name -Xml $Backup.Definition -Force | Out-Null
  } else {
    Unregister-ScheduledTask -TaskPath $TaskPath -TaskName $Backup.Name -Confirm:$false -ErrorAction SilentlyContinue
  }
  return 'restored'
}

function Register-InstallerTask([string]$Name, $Task, [string]$Phase) {
  if ($TestMode) {
    if ($TestFailurePhase -eq $Phase) { throw "INSTALL_TEST_FAILURE $Phase" }
    if ($Name -eq $TaskName) { $script:TestTaskDefinitions.gateway = 'gateway-new' } else { $script:TestTaskDefinitions.watchdog = 'watchdog-new' }
    Write-AgentCoreInfo "INSTALL_TEST_REGISTER $Name"
    return
  }
  Register-ScheduledTask -TaskPath $TaskPath -TaskName $Name -InputObject $Task -Force | Out-Null
}

function Enable-TaskSchedulerOperationalLog {
  if ($TestMode) {
    if ($TestFailurePhase -eq 'OperationalLogEnablement') { throw 'INSTALL_TEST_FAILURE OperationalLogEnablement' }
    Write-AgentCoreInfo 'INSTALL_TEST_OPERATIONAL_LOG_ENABLED'
    return
  }
  & wevtutil.exe sl 'Microsoft-Windows-TaskScheduler/Operational' '/e:true'
  if ($LASTEXITCODE -ne 0) { throw 'Task Scheduler Operational logging enablement failed.' }
}

function Invoke-TaskInstallTransaction($GatewayTask, $WatchdogTask) {
  Assert-InstallerPrivileges
  if (-not $TestMode) {
    $script:TaskBackupDirectory = Join-Path $backupsDir ("scheduled-tasks\\{0}" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Force -Path $script:TaskBackupDirectory | Out-Null
  }
  $gatewayBackup = Get-TaskDefinitionBackup $TaskName
  $watchdogBackup = Get-TaskDefinitionBackup $WatchdogTaskName
  foreach ($backup in @($gatewayBackup, $watchdogBackup)) {
    if ($backup.Exists -and -not $backup.BackupAvailable) { throw "INSTALL_TASK_BACKUP_FAILED $($backup.Name)" }
  }
  try {
    Register-InstallerTask -Name $TaskName -Task $GatewayTask -Phase 'GatewayRegistration'
    Register-InstallerTask -Name $WatchdogTaskName -Task $WatchdogTask -Phase 'WatchdogRegistration'
    Enable-TaskSchedulerOperationalLog
  } catch {
    $originalFailure = $_
    $gatewayResult = 'failed'
    $watchdogResult = 'failed'
    $rollbackFailed = $false
    try { $gatewayResult = Restore-TaskDefinition $gatewayBackup } catch { $rollbackFailed = $true }
    try { $watchdogResult = Restore-TaskDefinition $watchdogBackup } catch { $rollbackFailed = $true }
    Write-Host "INSTALL_ROLLBACK gateway=$gatewayResult watchdog=$watchdogResult"
    if ($rollbackFailed) { throw 'INSTALL_ROLLBACK_FAILED' }
    throw $originalFailure
  }
}

if ($EmitTaskSpecs) {
  $specPowerShell = if ([string]::IsNullOrWhiteSpace($TaskSpecPowerShellPath)) { 'pwsh.exe' } else { $TaskSpecPowerShellPath }
  New-BifrostTaskSpecs $specPowerShell | ConvertTo-Json -Depth 8 -Compress
  exit 0
}

if ($TestMode) {
  Initialize-TestTaskModel
  try {
    Invoke-TaskInstallTransaction -GatewayTask ([pscustomobject]@{ name = $TaskName; restart_count = 1 }) -WatchdogTask ([pscustomobject]@{ name = $WatchdogTaskName })
    Write-TestTaskModel
    Write-AgentCoreInfo 'INSTALL_TEST_SUCCESS'
    exit 0
  } catch {
    Write-TestTaskModel
    throw
  }
}

Assert-InstallerPrivileges

$binDir = Join-Path $RuntimeRoot 'bin'
$configDir = Join-Path $RuntimeRoot 'config'
$dataDir = Join-Path $RuntimeRoot 'data'
$logsDir = Join-Path $RuntimeRoot 'logs'
$stateDir = Join-Path $RuntimeRoot 'state'
$backupsDir = Join-Path $RuntimeRoot 'backups'
$exePath = Join-Path $binDir 'bifrost-http.exe'
$renderScript = Join-Path $RepoRoot 'scripts\bifrost\render_bifrost_config.py'

foreach ($dir in @($RuntimeRoot, $binDir, $configDir, $dataDir, $logsDir, $stateDir, $backupsDir, 'F:\AgentCore\runtime\mcp-processes', 'F:\AgentCore\runtime\tentra\data')) {
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

if (-not (Test-Path -LiteralPath $exePath)) {
  throw "bifrost-http.exe not found at $exePath. Place the binary before install."
}

if (-not (Test-Path -LiteralPath $renderScript)) {
  throw "Renderer missing: $renderScript"
}

# Non-secret User env defaults required by upstream stdio servers
$nonSecretDefaults = @{
  'DISABLE_THOUGHT_LOGGING' = 'true'
  'CURSOR_API_URL'          = 'https://api.cursor.com'
  'OBSIDIAN_BASE_URL'       = 'https://127.0.0.1:27124'
  'OBSIDIAN_VERIFY_SSL'     = 'false'
}
foreach ($key in $nonSecretDefaults.Keys) {
  $existing = [Environment]::GetEnvironmentVariable($key, 'User')
  if ([string]::IsNullOrWhiteSpace($existing)) {
    [Environment]::SetEnvironmentVariable($key, $nonSecretDefaults[$key], 'User')
    Write-AgentCoreInfo "Set User env $key (non-secret default)"
  }
}

Write-AgentCoreInfo "Rendering Bifrost config into $RuntimeRoot"
$pythonCmd = $null
foreach ($c in @('py', 'python', 'python3')) {
  $cmd = Get-Command $c -ErrorAction SilentlyContinue
  if ($cmd) { $pythonCmd = $cmd.Source; break }
}
if (-not $pythonCmd -and (Test-Path 'C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe')) {
  $pythonCmd = 'C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe'
}
if (-not $pythonCmd) { throw 'Python interpreter not found (tried py/python/python3 and Python313 path).' }
& $pythonCmd $renderScript --out (Join-Path $RuntimeRoot 'config.json')
if ($LASTEXITCODE -ne 0) {
  throw "render_bifrost_config.py failed with exit $LASTEXITCODE"
}

$validateScript = Join-Path $RepoRoot 'scripts\bifrost\validate_contracts.py'
if (Test-Path -LiteralPath $validateScript) {
  & $pythonCmd $validateScript
  if ($LASTEXITCODE -ne 0) {
    throw "validate_contracts.py failed with exit $LASTEXITCODE"
  }
}

if ($SkipScheduledTask) {
  Write-AgentCoreInfo 'Skipping scheduled task registration (-SkipScheduledTask).'
  return
}

$pwshPath = 'C:\Program Files\PowerShell\7\pwsh.exe'
if (-not (Test-Path -LiteralPath $pwshPath)) {
  $pwshPath = 'pwsh.exe'
}
$taskSpecs = New-BifrostTaskSpecs $pwshPath
$gatewaySpec = $taskSpecs.gateway
$watchdogSpec = $taskSpecs.watchdog
$launchScript = Join-Path $PSScriptRoot 'Launch-AgentCoreBifrostGateway.ps1'
$watchdogScript = Join-Path $PSScriptRoot 'Invoke-AgentCoreBifrostWatchdog.ps1'
$action = New-ScheduledTaskAction -Execute $gatewaySpec.action.executable -Argument $gatewaySpec.action.arguments -WorkingDirectory $gatewaySpec.action.working_directory
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -ExecutionTimeLimit ([TimeSpan]::FromSeconds($gatewaySpec.settings.execution_time_limit_seconds)) `
  -RestartCount $gatewaySpec.settings.restart_count `
  -RestartInterval (New-TimeSpan -Seconds $gatewaySpec.settings.restart_interval_seconds) `
  -StartWhenAvailable `
  -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal

if (-not (Test-Path -LiteralPath $watchdogScript)) {
  throw "Watchdog script missing: $watchdogScript"
}
$watchdogAction = New-ScheduledTaskAction -Execute $watchdogSpec.action.executable -Argument $watchdogSpec.action.arguments -WorkingDirectory $watchdogSpec.action.working_directory
$watchdogTrigger = New-ScheduledTaskTrigger -Daily -At (Get-Date).AddMinutes(1)
$watchdogRepetition = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Seconds $watchdogSpec.trigger.repetition_interval_seconds) -RepetitionDuration (New-TimeSpan -Seconds $watchdogSpec.trigger.repetition_duration_seconds)
$watchdogTrigger.Repetition = $watchdogRepetition.Repetition
$watchdogSettings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -ExecutionTimeLimit (New-TimeSpan -Seconds $watchdogSpec.settings.execution_time_limit_seconds) `
  -RestartCount $watchdogSpec.settings.restart_count `
  -StartWhenAvailable `
  -MultipleInstances IgnoreNew
$watchdogTask = New-ScheduledTask -Action $watchdogAction -Trigger $watchdogTrigger -Settings $watchdogSettings -Principal $principal

Invoke-TaskInstallTransaction -GatewayTask $task -WatchdogTask $watchdogTask
Write-AgentCoreInfo "Registered scheduled task $TaskPath$TaskName"
Write-AgentCoreInfo "Registered scheduled task $TaskPath$WatchdogTaskName"
Write-AgentCoreInfo 'Enabled Task Scheduler Operational logging.'

Write-AgentCoreInfo 'Install complete. Ensure BIFROST_MCP_VIRTUAL_KEY and upstream env vars exist as Windows User environment variables.'
