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
  [switch]$TestFullTransaction,
  [switch]$TestPrivilegeDenied,
  [ValidateSet('None', 'ConfigActivation', 'GatewayRegistration', 'WatchdogRegistration', 'OperationalLogEnablement')]
  [string]$TestFailurePhase = 'None',
  [ValidateSet('Absent', 'Present', 'ExportFailure')]
  [string]$TestGatewayTaskModel = 'Absent',
  [ValidateSet('Absent', 'Present', 'ExportFailure')]
  [string]$TestWatchdogTaskModel = 'Absent',
  [switch]$EmitTaskSpecs,
  [string]$TaskSpecPowerShellPath = '',
  [string]$TestRenderedConfigPath = '',
  [string]$TestEnvironmentStatePath = ''
)

$ErrorActionPreference = 'Stop'

function Write-AgentCoreInfo([string]$Message) {
  Write-Host "[Install-AgentCoreBifrostGateway] $Message"
}

function Test-ScheduledTaskNotFoundError($ErrorRecord) {
  $parts = @(
    [string]$ErrorRecord.Exception.Message,
    [string]$ErrorRecord.FullyQualifiedErrorId,
    [string]$ErrorRecord.CategoryInfo.Category,
    [string]$ErrorRecord.CategoryInfo.Reason
  ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
  $errorText = $parts -join ' '
  return ($errorText -match '(?i)not found|cannot find|does not exist|0x80070002|CmdletizationQuery_NotFound|ObjectNotFound')
}

function New-BifrostTaskSpecs([string]$PowerShellPath) {
  $launchScript = Join-Path $PSScriptRoot 'Launch-AgentCoreBifrostGateway.ps1'
  $watchdogScript = Join-Path $PSScriptRoot 'Invoke-AgentCoreBifrostWatchdog.ps1'
  return [ordered]@{
    gateway = [ordered]@{
      action = [ordered]@{
        executable = $PowerShellPath
        arguments = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$launchScript`" -RuntimeRoot `"$RuntimeRoot`" -HostAddress $HostAddress -Port $Port"
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
      }
    }
    watchdog = [ordered]@{
      action = [ordered]@{
        executable = $PowerShellPath
        arguments = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$watchdogScript`" -RuntimeRoot `"$RuntimeRoot`" -GatewayUrl http://${HostAddress}:${Port} -TaskPath `"$TaskPath`" -TaskName `"$TaskName`""
        working_directory = $RuntimeRoot
      }
      trigger = [ordered]@{
        type = 'daily_repeating'
        start_delay_seconds = 60
        repetition_interval_seconds = 60
        repetition_duration_seconds = 86400
      }
      settings = [ordered]@{
        allow_start_if_on_batteries = $true
        dont_stop_if_going_on_batteries = $true
        execution_time_limit_seconds = 60
        restart_count = 0
        start_when_available = $true
        multiple_instances = 'IgnoreNew'
      }
    }
    operational_logging = [ordered]@{ channel = 'Microsoft-Windows-TaskScheduler/Operational'; enable = $true }
  }
}

function Add-TestScheduledTaskCall([string]$Scope, [string]$Command, $Parameters) {
  if (-not $TestMode) { return }
  $script:TestScheduledTaskCalls.Add([ordered]@{
    scope = $Scope
    command = $Command
    parameters = $Parameters
  })
}

function New-InstallerScheduledTaskAction($Spec, [string]$Scope) {
  $parameters = [ordered]@{
    Execute = [string]$Spec.executable
    Argument = [string]$Spec.arguments
    WorkingDirectory = [string]$Spec.working_directory
  }
  if ($TestMode) {
    Add-TestScheduledTaskCall $Scope 'New-ScheduledTaskAction' $parameters
    return [pscustomobject]@{ action = $Scope }
  }
  return New-ScheduledTaskAction @parameters
}

function New-InstallerLogonTrigger($Spec) {
  if ($Spec.type -ne 'logon') { throw "Unsupported gateway task trigger type: $($Spec.type)" }
  $parameters = [ordered]@{ AtLogOn = $true; User = [string]$Spec.user }
  if ($TestMode) {
    Add-TestScheduledTaskCall 'gateway' 'New-ScheduledTaskTrigger' $parameters
    return [pscustomobject]@{ trigger = 'gateway' }
  }
  return New-ScheduledTaskTrigger @parameters
}

function New-InstallerRepeatingDailyTrigger($Spec) {
  if ($Spec.type -ne 'daily_repeating') { throw "Unsupported watchdog task trigger type: $($Spec.type)" }
  $startAt = (Get-Date).AddSeconds([int]$Spec.start_delay_seconds)
  $dailyParameters = [ordered]@{ Daily = $true; At = $startAt }
  $repetitionParameters = [ordered]@{
    Once = $true
    At = $startAt
    RepetitionInterval = [TimeSpan]::FromSeconds([int]$Spec.repetition_interval_seconds)
    RepetitionDuration = [TimeSpan]::FromSeconds([int]$Spec.repetition_duration_seconds)
  }
  if ($TestMode) {
    Add-TestScheduledTaskCall 'watchdog' 'New-ScheduledTaskTrigger' ([ordered]@{
      Daily = $true
      At = $startAt.ToUniversalTime().ToString('o')
    })
    Add-TestScheduledTaskCall 'watchdog' 'New-ScheduledTaskTrigger' ([ordered]@{
      Once = $true
      At = $startAt.ToUniversalTime().ToString('o')
      RepetitionIntervalSeconds = [int]$Spec.repetition_interval_seconds
      RepetitionDurationSeconds = [int]$Spec.repetition_duration_seconds
    })
    $dailyTrigger = [pscustomobject]@{ Repetition = $null }
    $repetitionTrigger = [pscustomobject]@{ Repetition = [pscustomobject]@{
      Interval = $repetitionParameters.RepetitionInterval
      Duration = $repetitionParameters.RepetitionDuration
    } }
  } else {
    $dailyTrigger = New-ScheduledTaskTrigger @dailyParameters
    $repetitionTrigger = New-ScheduledTaskTrigger @repetitionParameters
  }
  $dailyTrigger.Repetition = $repetitionTrigger.Repetition
  return $dailyTrigger
}

function New-InstallerScheduledTaskSettings($Spec, [string]$Scope) {
  $parameters = [ordered]@{
    AllowStartIfOnBatteries = [bool]$Spec.allow_start_if_on_batteries
    DontStopIfGoingOnBatteries = [bool]$Spec.dont_stop_if_going_on_batteries
    ExecutionTimeLimit = [TimeSpan]::FromSeconds([int]$Spec.execution_time_limit_seconds)
    RestartCount = [int]$Spec.restart_count
    StartWhenAvailable = [bool]$Spec.start_when_available
    MultipleInstances = [string]$Spec.multiple_instances
  }
  $capturedParameters = [ordered]@{
    AllowStartIfOnBatteries = [bool]$Spec.allow_start_if_on_batteries
    DontStopIfGoingOnBatteries = [bool]$Spec.dont_stop_if_going_on_batteries
    ExecutionTimeLimitSeconds = [int]$Spec.execution_time_limit_seconds
    RestartCount = [int]$Spec.restart_count
  }
  if ($Spec.Contains('restart_interval_seconds')) {
    $parameters.RestartInterval = [TimeSpan]::FromSeconds([int]$Spec.restart_interval_seconds)
    $capturedParameters.RestartIntervalSeconds = [int]$Spec.restart_interval_seconds
  }
  $capturedParameters.StartWhenAvailable = [bool]$Spec.start_when_available
  $capturedParameters.MultipleInstances = [string]$Spec.multiple_instances
  if ($TestMode) {
    Add-TestScheduledTaskCall $Scope 'New-ScheduledTaskSettingsSet' $capturedParameters
    return [pscustomobject]@{ settings = $Scope }
  }
  return New-ScheduledTaskSettingsSet @parameters
}

function New-InstallerScheduledTasks($TaskSpecs) {
  $watchdogScript = Join-Path $PSScriptRoot 'Invoke-AgentCoreBifrostWatchdog.ps1'
  if (-not (Test-Path -LiteralPath $watchdogScript)) { throw "Watchdog script missing: $watchdogScript" }

  $gatewayAction = New-InstallerScheduledTaskAction $TaskSpecs.gateway.action 'gateway'
  $gatewayTrigger = New-InstallerLogonTrigger $TaskSpecs.gateway.trigger
  $gatewaySettings = New-InstallerScheduledTaskSettings $TaskSpecs.gateway.settings 'gateway'
  $watchdogAction = New-InstallerScheduledTaskAction $TaskSpecs.watchdog.action 'watchdog'
  $watchdogTrigger = New-InstallerRepeatingDailyTrigger $TaskSpecs.watchdog.trigger
  $watchdogSettings = New-InstallerScheduledTaskSettings $TaskSpecs.watchdog.settings 'watchdog'

  if ($TestMode) {
    return [pscustomobject]@{
      gateway = [pscustomobject]@{ action = $gatewayAction; trigger = $gatewayTrigger; settings = $gatewaySettings }
      watchdog = [pscustomobject]@{ action = $watchdogAction; trigger = $watchdogTrigger; settings = $watchdogSettings }
    }
  }
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
  return [pscustomobject]@{
    gateway = New-ScheduledTask -Action $gatewayAction -Trigger $gatewayTrigger -Settings $gatewaySettings -Principal $principal
    watchdog = New-ScheduledTask -Action $watchdogAction -Trigger $watchdogTrigger -Settings $watchdogSettings -Principal $principal
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
  $script:TestScheduledTaskCalls = [System.Collections.Generic.List[object]]::new()
  $script:TestTaskDefinitions = @{
    gateway = if ($TestGatewayTaskModel -eq 'Absent') { $null } else { 'gateway-original' }
    watchdog = if ($TestWatchdogTaskModel -eq 'Absent') { $null } else { 'watchdog-original' }
  }
}

function Initialize-TestEnvironmentModel {
  if (-not $TestMode -or -not $TestFullTransaction) { return }
  if ([string]::IsNullOrWhiteSpace($TestEnvironmentStatePath) -or
      -not (Test-Path -LiteralPath $TestEnvironmentStatePath)) {
    throw 'INSTALL_TEST_ENVIRONMENT_STATE_REQUIRED'
  }
  $script:TestEnvironmentState = Get-Content -Raw -LiteralPath $TestEnvironmentStatePath |
    ConvertFrom-Json -AsHashtable -ErrorAction Stop
}

function Write-TestEnvironmentModel {
  if (-not $TestMode -or -not $TestFullTransaction) { return }
  $json = ConvertTo-Json -InputObject $script:TestEnvironmentState -Depth 4 -Compress
  [IO.File]::WriteAllText($TestEnvironmentStatePath, $json, [Text.UTF8Encoding]::new($false))
}

function Get-InstallerUserEnvironmentState([string]$Name) {
  if ($TestMode -and $TestFullTransaction) {
    $entry = $script:TestEnvironmentState[$Name]
    $exists = ($null -ne $entry) -and [bool]$entry.exists
    return [pscustomobject]@{ Name = $Name; Exists = $exists; Value = if ($exists) { [string]$entry.value } else { $null } }
  }
  $userEnvironment = [Environment]::GetEnvironmentVariables('User')
  $exists = $userEnvironment.Contains($Name)
  return [pscustomobject]@{ Name = $Name; Exists = $exists; Value = if ($exists) { [string]$userEnvironment[$Name] } else { $null } }
}

function Set-InstallerUserEnvironmentState([string]$Name, [bool]$Exists, $Value) {
  if ($TestMode -and $TestFullTransaction) {
    $script:TestEnvironmentState[$Name] = [ordered]@{ exists = $Exists; value = if ($Exists) { [string]$Value } else { $null } }
    Write-TestEnvironmentModel
    return
  }
  [Environment]::SetEnvironmentVariable($Name, $(if ($Exists) { [string]$Value } else { $null }), 'User')
}

function Get-InstallerEnvironmentBackup($Defaults) {
  $backup = [System.Collections.Generic.List[object]]::new()
  foreach ($key in @($Defaults.Keys | Sort-Object)) {
    $backup.Add((Get-InstallerUserEnvironmentState $key))
  }
  return @($backup)
}

function Set-InstallerEnvironmentDefaults($Defaults) {
  foreach ($key in @($Defaults.Keys | Sort-Object)) {
    $state = Get-InstallerUserEnvironmentState $key
    if (-not $state.Exists -or [string]::IsNullOrWhiteSpace([string]$state.Value)) {
      Set-InstallerUserEnvironmentState $key $true $Defaults[$key]
      Write-AgentCoreInfo "Set User env $key (non-secret default)"
    }
  }
}

function Restore-InstallerEnvironment($Backup) {
  foreach ($state in $Backup) {
    Set-InstallerUserEnvironmentState $state.Name ([bool]$state.Exists) $state.Value
  }
  return 'restored'
}

function Get-InstallerFileBackup([string]$Path) {
  $exists = Test-Path -LiteralPath $Path -PathType Leaf
  return [pscustomobject]@{
    Path = $Path
    Exists = $exists
    Bytes = if ($exists) { [IO.File]::ReadAllBytes($Path) } else { $null }
  }
}

function Restore-InstallerFile($Backup) {
  if ($Backup.Exists) {
    $parent = Split-Path -Parent $Backup.Path
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [IO.File]::WriteAllBytes($Backup.Path, $Backup.Bytes)
  } else {
    Remove-Item -LiteralPath $Backup.Path -Force -ErrorAction SilentlyContinue
  }
  return 'restored'
}

function Restore-InstallerFiles($Backups) {
  foreach ($backup in @($Backups)) {
    Restore-InstallerFile $backup | Out-Null
  }
  return 'restored'
}

function Assert-BifrostConfigSemantics($Config) {
  if (-not ($Config -is [System.Management.Automation.PSCustomObject])) {
    throw 'INSTALL_INVALID_STAGED_CONFIG'
  }
  if ([int]$Config.version -ne 2) {
    throw 'INSTALL_INVALID_STAGED_CONFIG'
  }
  if (-not ($Config.client -is [System.Management.Automation.PSCustomObject])) {
    throw 'INSTALL_INVALID_STAGED_CONFIG'
  }
  if ($Config.client.mcp_disable_auto_tool_inject -ne $true) {
    throw 'INSTALL_INVALID_STAGED_CONFIG'
  }
  if (-not ($Config.mcp -is [System.Management.Automation.PSCustomObject])) {
    throw 'INSTALL_INVALID_STAGED_CONFIG'
  }
  if (-not ($Config.mcp.client_configs -is [array]) -or $Config.mcp.client_configs.Count -lt 1) {
    throw 'INSTALL_INVALID_STAGED_CONFIG'
  }
  foreach ($clientConfig in @($Config.mcp.client_configs)) {
    if (-not ($clientConfig -is [System.Management.Automation.PSCustomObject])) {
      throw 'INSTALL_INVALID_STAGED_CONFIG'
    }
    if ([string]::IsNullOrWhiteSpace([string]$clientConfig.name)) {
      throw 'INSTALL_INVALID_STAGED_CONFIG'
    }
    if ([string]::IsNullOrWhiteSpace([string]$clientConfig.connection_type)) {
      throw 'INSTALL_INVALID_STAGED_CONFIG'
    }
    if ([string]$clientConfig.connection_type -eq 'stdio') {
      if (-not ($clientConfig.stdio_config -is [System.Management.Automation.PSCustomObject])) {
        throw 'INSTALL_INVALID_STAGED_CONFIG'
      }
      if ([string]::IsNullOrWhiteSpace([string]$clientConfig.stdio_config.command)) {
        throw 'INSTALL_INVALID_STAGED_CONFIG'
      }
    }
  }
}

function Write-TestScheduledTaskCalls {
  if ($TestMode) {
    Write-Host ('INSTALL_TASK_CALLS ' + (ConvertTo-Json -InputObject @($script:TestScheduledTaskCalls) -Depth 8 -Compress))
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
    if (Test-ScheduledTaskNotFoundError $_) {
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

function Enable-TaskSchedulerOperationalLog($Spec) {
  $enabledArgument = if ([bool]$Spec.enable) { '/e:true' } else { '/e:false' }
  $argumentList = @('sl', [string]$Spec.channel, $enabledArgument)
  if ($TestMode) {
    if ($TestFailurePhase -eq 'OperationalLogEnablement') { throw 'INSTALL_TEST_FAILURE OperationalLogEnablement' }
    Add-TestScheduledTaskCall 'operational_logging' 'wevtutil.exe' ([ordered]@{ ArgumentList = $argumentList })
    Write-AgentCoreInfo 'INSTALL_TEST_OPERATIONAL_LOG_ENABLED'
    return
  }
  & wevtutil.exe @argumentList
  if ($LASTEXITCODE -ne 0) { throw 'Task Scheduler Operational logging enablement failed.' }
}

function Get-TaskInstallBackups {
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
  return [pscustomobject]@{ Gateway = $gatewayBackup; Watchdog = $watchdogBackup }
}

function Restore-TaskInstallBackups($Backups) {
  $gatewayResult = Restore-TaskDefinition $Backups.Gateway
  $watchdogResult = Restore-TaskDefinition $Backups.Watchdog
  return [pscustomobject]@{ Gateway = $gatewayResult; Watchdog = $watchdogResult }
}

function Invoke-TaskInstallTransaction($GatewayTask, $WatchdogTask, $OperationalLoggingSpec) {
  Register-InstallerTask -Name $TaskName -Task $GatewayTask -Phase 'GatewayRegistration'
  Register-InstallerTask -Name $WatchdogTaskName -Task $WatchdogTask -Phase 'WatchdogRegistration'
  Enable-TaskSchedulerOperationalLog $OperationalLoggingSpec
}

if ($EmitTaskSpecs) {
  $specPowerShell = if ([string]::IsNullOrWhiteSpace($TaskSpecPowerShellPath)) { 'pwsh.exe' } else { $TaskSpecPowerShellPath }
  New-BifrostTaskSpecs $specPowerShell | ConvertTo-Json -Depth 8 -Compress
  exit 0
}

$binDir = Join-Path $RuntimeRoot 'bin'
$configDir = Join-Path $RuntimeRoot 'config'
$dataDir = Join-Path $RuntimeRoot 'data'
$logsDir = Join-Path $RuntimeRoot 'logs'
$stateDir = Join-Path $RuntimeRoot 'state'
$backupsDir = Join-Path $RuntimeRoot 'backups'
$exePath = Join-Path $binDir 'bifrost-http.exe'
$liveConfigPath = Join-Path $RuntimeRoot 'config.json'
$liveConfigDirPath = Join-Path $configDir 'config.json'
$renderScript = Join-Path $RepoRoot 'scripts\bifrost\render_bifrost_config.py'
$validateScript = Join-Path $RepoRoot 'scripts\bifrost\validate_contracts.py'
$nonSecretDefaults = @{
  'DISABLE_THOUGHT_LOGGING' = 'true'
  'CURSOR_API_URL'          = 'https://api.cursor.com'
  'OBSIDIAN_BASE_URL'       = 'https://127.0.0.1:27124'
  'OBSIDIAN_VERIFY_SSL'     = 'false'
}

if ($TestMode) { Initialize-TestTaskModel }

if ($TestMode -and -not $TestFullTransaction) {
  try {
    $specPowerShell = if ([string]::IsNullOrWhiteSpace($TaskSpecPowerShellPath)) { 'pwsh.exe' } else { $TaskSpecPowerShellPath }
    $taskSpecs = New-BifrostTaskSpecs $specPowerShell
    $scheduledTasks = New-InstallerScheduledTasks $taskSpecs
    $taskBackups = Get-TaskInstallBackups
    Invoke-TaskInstallTransaction -GatewayTask $scheduledTasks.gateway -WatchdogTask $scheduledTasks.watchdog -OperationalLoggingSpec $taskSpecs.operational_logging
    Write-TestScheduledTaskCalls
    Write-TestTaskModel
    Write-AgentCoreInfo 'INSTALL_TEST_SUCCESS'
    exit 0
  } catch {
    if ($null -ne $taskBackups) {
      try {
        $taskRollback = Restore-TaskInstallBackups $taskBackups
        Write-Host "INSTALL_ROLLBACK gateway=$($taskRollback.Gateway) watchdog=$($taskRollback.Watchdog)"
      } catch { throw 'INSTALL_ROLLBACK_FAILED' }
    }
    Write-TestTaskModel
    throw
  }
}

Assert-InstallerPrivileges
if (-not (Test-Path -LiteralPath $exePath)) {
  throw "bifrost-http.exe not found at $exePath. Place the binary before install."
}
if (-not $TestMode -and -not (Test-Path -LiteralPath $renderScript)) {
  throw "Renderer missing: $renderScript"
}
$pythonCmd = $null
if ($TestMode) {
  if ([string]::IsNullOrWhiteSpace($TestRenderedConfigPath) -or
      -not (Test-Path -LiteralPath $TestRenderedConfigPath -PathType Leaf)) {
    throw 'INSTALL_TEST_RENDERED_CONFIG_REQUIRED'
  }
  Initialize-TestEnvironmentModel
} else {
  foreach ($c in @('py', 'python', 'python3')) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $pythonCmd = $cmd.Source; break }
  }
  if (-not $pythonCmd -and (Test-Path 'C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe')) {
    $pythonCmd = 'C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe'
  }
  if (-not $pythonCmd) { throw 'Python interpreter not found (tried py/python/python3 and Python313 path).' }
}

$transactionId = Get-Date -Format 'yyyyMMdd-HHmmss-fffffff'
$transactionDirectory = Join-Path $backupsDir "installer\$transactionId"
$stagingDirectory = Join-Path $transactionDirectory 'staging'
$stagedConfigPath = Join-Path $stagingDirectory 'config.json'
New-Item -ItemType Directory -Force -Path $stagingDirectory | Out-Null

# Capture every live state domain before rendering or activation.
$configBackups = @(
  (Get-InstallerFileBackup $liveConfigPath),
  (Get-InstallerFileBackup $liveConfigDirPath)
)
foreach ($backup in @($configBackups)) {
  if ($backup.Exists) {
    $backupName = if ($backup.Path -eq $liveConfigPath) { 'config.json.before' } else { 'config_config.json.before' }
    [IO.File]::WriteAllBytes((Join-Path $transactionDirectory $backupName), $backup.Bytes)
  }
}
$environmentBackup = Get-InstallerEnvironmentBackup $nonSecretDefaults
$taskBackups = if ($SkipScheduledTask) { $null } else { Get-TaskInstallBackups }

Write-AgentCoreInfo "Rendering Bifrost config into staging $stagingDirectory"
if ($TestMode) {
  [IO.File]::Copy($TestRenderedConfigPath, $stagedConfigPath, $true)
} else {
  & $pythonCmd $renderScript --out $stagedConfigPath --no-also-config-dir --skip-renderer
  if ($LASTEXITCODE -ne 0) {
    throw "render_bifrost_config.py failed with exit $LASTEXITCODE"
  }
}
$stagedConfig = Get-Content -Raw -LiteralPath $stagedConfigPath | ConvertFrom-Json -ErrorAction Stop
Assert-BifrostConfigSemantics $stagedConfig
if (-not $TestMode -and (Test-Path -LiteralPath $validateScript)) {
  & $pythonCmd $validateScript
  if ($LASTEXITCODE -ne 0) { throw "validate_contracts.py failed with exit $LASTEXITCODE" }
}

$pwshPath = 'C:\Program Files\PowerShell\7\pwsh.exe'
if ($TestMode -and -not [string]::IsNullOrWhiteSpace($TaskSpecPowerShellPath)) { $pwshPath = $TaskSpecPowerShellPath }
elseif (-not (Test-Path -LiteralPath $pwshPath)) { $pwshPath = 'pwsh.exe' }
$taskSpecs = New-BifrostTaskSpecs $pwshPath
$scheduledTasks = if ($SkipScheduledTask) { $null } else { New-InstallerScheduledTasks $taskSpecs }

try {
  $runtimeDirectories = @($RuntimeRoot, $binDir, $configDir, $dataDir, $logsDir, $stateDir, $backupsDir)
  if (-not $TestMode) { $runtimeDirectories += @('F:\AgentCore\runtime\mcp-processes', 'F:\AgentCore\runtime\tentra\data') }
  foreach ($dir in $runtimeDirectories) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

  Set-InstallerEnvironmentDefaults $nonSecretDefaults
  $stagedConfigBytes = [IO.File]::ReadAllBytes($stagedConfigPath)
  [IO.File]::WriteAllBytes($liveConfigPath, $stagedConfigBytes)
  [IO.File]::WriteAllBytes($liveConfigDirPath, $stagedConfigBytes)
  if ($TestMode -and $TestFailurePhase -eq 'ConfigActivation') { throw 'INSTALL_TEST_FAILURE ConfigActivation' }

  if ($SkipScheduledTask) {
    Write-AgentCoreInfo 'Skipping scheduled task registration (-SkipScheduledTask).'
  } else {
    Invoke-TaskInstallTransaction -GatewayTask $scheduledTasks.gateway -WatchdogTask $scheduledTasks.watchdog -OperationalLoggingSpec $taskSpecs.operational_logging
    Write-AgentCoreInfo "Registered scheduled task $TaskPath$TaskName"
    Write-AgentCoreInfo "Registered scheduled task $TaskPath$WatchdogTaskName"
    Write-AgentCoreInfo 'Enabled Task Scheduler Operational logging.'
  }
} catch {
  $originalFailure = $_
  $rollbackFailed = $false
  $configResult = 'failed'
  $environmentResult = 'failed'
  $gatewayResult = if ($SkipScheduledTask) { 'not_applicable' } else { 'failed' }
  $watchdogResult = if ($SkipScheduledTask) { 'not_applicable' } else { 'failed' }
  if ($null -ne $taskBackups) {
    try {
      $taskRollback = Restore-TaskInstallBackups $taskBackups
      $gatewayResult = $taskRollback.Gateway
      $watchdogResult = $taskRollback.Watchdog
    } catch { $rollbackFailed = $true }
  }
  try { $configResult = Restore-InstallerFiles $configBackups } catch { $rollbackFailed = $true }
  try { $environmentResult = Restore-InstallerEnvironment $environmentBackup } catch { $rollbackFailed = $true }
  Write-Host "INSTALL_ROLLBACK config=$configResult environment=$environmentResult gateway=$gatewayResult watchdog=$watchdogResult"
  Write-TestTaskModel
  if ($rollbackFailed) { throw 'INSTALL_ROLLBACK_FAILED' }
  throw $originalFailure
}

Write-TestScheduledTaskCalls
Write-TestTaskModel
Write-AgentCoreInfo 'Install complete. Ensure BIFROST_MCP_VIRTUAL_KEY and upstream env vars exist as Windows User environment variables.'
