<#
.SYNOPSIS
  Install AgentCore Bifrost MCP Gateway runtime directories, config, and logon scheduled task.

.NOTES
  Does not print secret values.
  Does not touch SwarmRecall/SwarmVault/SwarmClaw product installs.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'H:\AgentRuntime\bifrost',
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$TaskPath = '\AgentCore\',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080,
  [switch]$SkipScheduledTask
)

$ErrorActionPreference = 'Stop'

function Write-AgentCoreInfo([string]$Message) {
  Write-Host "[Install-AgentCoreBifrostGateway] $Message"
}

$binDir = Join-Path $RuntimeRoot 'bin'
$configDir = Join-Path $RuntimeRoot 'config'
$dataDir = Join-Path $RuntimeRoot 'data'
$logsDir = Join-Path $RuntimeRoot 'logs'
$stateDir = Join-Path $RuntimeRoot 'state'
$backupsDir = Join-Path $RuntimeRoot 'backups'
$exePath = Join-Path $binDir 'bifrost-http.exe'
$renderScript = Join-Path $RepoRoot 'scripts\bifrost\render_bifrost_config.py'

foreach ($dir in @($RuntimeRoot, $binDir, $configDir, $dataDir, $logsDir, $stateDir, $backupsDir, 'H:\AgentRuntime\mcp-processes', 'H:\AgentRuntime\tentra\data')) {
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
python $renderScript --out (Join-Path $RuntimeRoot 'config.json')
if ($LASTEXITCODE -ne 0) {
  throw "render_bifrost_config.py failed with exit $LASTEXITCODE"
}

$validateScript = Join-Path $RepoRoot 'scripts\bifrost\validate_contracts.py'
if (Test-Path -LiteralPath $validateScript) {
  python $validateScript
  if ($LASTEXITCODE -ne 0) {
    throw "validate_contracts.py failed with exit $LASTEXITCODE"
  }
}

if ($SkipScheduledTask) {
  Write-AgentCoreInfo 'Skipping scheduled task registration (-SkipScheduledTask).'
  return
}

$argument = "-app-dir `"$RuntimeRoot`" -host $HostAddress -port $Port -log-level info -log-style json"
$action = New-ScheduledTaskAction -Execute $exePath -Argument $argument -WorkingDirectory $RuntimeRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -ExecutionTimeLimit ([TimeSpan]::Zero) `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -StartWhenAvailable `
  -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal

try {
  Register-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -InputObject $task -Force | Out-Null
  Write-AgentCoreInfo "Registered scheduled task $TaskPath$TaskName"
} catch {
  Write-Warning "Scheduled task registration failed (may need elevation): $($_.Exception.Message)"
  Write-AgentCoreInfo "Manual launch: `"$exePath`" $argument"
}

Write-AgentCoreInfo 'Install complete. Ensure BIFROST_MCP_VIRTUAL_KEY and upstream env vars exist as Windows User environment variables.'
