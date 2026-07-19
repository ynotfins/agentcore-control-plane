<#
.SYNOPSIS
  Run the AgentCore Bifrost Gateway as the foreground process for the Windows startup owner.

.DESCRIPTION
  This script is intentionally long-running. The scheduled task should own this
  PowerShell process, and this PowerShell process owns bifrost-http.exe in the
  foreground. If bifrost exits unexpectedly, this script exits with the same
  code so Task Scheduler can restart it.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'H:\AgentRuntime\bifrost',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'

function Write-AgentCoreLog([string]$Message) {
  $line = "[{0}] {1}" -f (Get-Date).ToString('o'), $Message
  Write-Host $line
}

$logDir = Join-Path $RuntimeRoot 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stdoutLog = Join-Path $logDir 'bifrost-gateway.stdout.log'
$stderrLog = Join-Path $logDir 'bifrost-gateway.stderr.log'

# Copy all Windows User env vars into this process. Scheduled tasks may start
# with an environment snapshot that predates AgentCore VK/profile variables.
[Environment]::GetEnvironmentVariables('User').GetEnumerator() | ForEach-Object {
  Set-Item -Path ("Env:{0}" -f $_.Key) -Value ([string]$_.Value) -Force
}

$env:CURSOR_API_URL = if ($env:CURSOR_API_URL) { $env:CURSOR_API_URL } else { 'https://api.cursor.com' }
$env:DISABLE_THOUGHT_LOGGING = 'true'
if (-not $env:HOME) { $env:HOME = $env:USERPROFILE }
if (-not $env:OBSIDIAN_BASE_URL) { $env:OBSIDIAN_BASE_URL = 'https://127.0.0.1:27124' }
if (-not $env:OBSIDIAN_VERIFY_SSL) { $env:OBSIDIAN_VERIFY_SSL = 'false' }

$exe = Join-Path $RuntimeRoot 'bin\bifrost-http.exe'
if (-not (Test-Path -LiteralPath $exe)) {
  throw "Missing Bifrost binary: $exe"
}

$configPath = Join-Path $RuntimeRoot 'config.json'
if (-not (Test-Path -LiteralPath $configPath)) {
  throw "Missing Bifrost config: $configPath"
}

Write-AgentCoreLog "Launching AgentCore Bifrost Gateway"
Write-AgentCoreLog "exe=$exe"
Write-AgentCoreLog "app_dir=$RuntimeRoot"
Write-AgentCoreLog "bind=${HostAddress}:${Port}"
Write-AgentCoreLog ("BIFROST_MCP_VIRTUAL_KEY present={0} length={1}" -f (-not [string]::IsNullOrWhiteSpace($env:BIFROST_MCP_VIRTUAL_KEY)), ($env:BIFROST_MCP_VIRTUAL_KEY ?? '').Length)
Write-AgentCoreLog ("BIFROST_ENCRYPTION_KEY present={0}" -f (-not [string]::IsNullOrWhiteSpace($env:BIFROST_ENCRYPTION_KEY)))
Write-AgentCoreLog "stdout_log=$stdoutLog"
Write-AgentCoreLog "stderr_log=$stderrLog"

# Ensure this scheduled task becomes the sole runtime owner.
Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object {
    if ($_.OwningProcess) {
      Write-AgentCoreLog "Stopping existing listener PID=$($_.OwningProcess) on port $Port"
      Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
  }
Get-Process -Name bifrost-http -ErrorAction SilentlyContinue | ForEach-Object {
  Write-AgentCoreLog "Stopping existing bifrost-http PID=$($_.Id)"
  Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 1

$bifrostArgs = @(
  '-app-dir', $RuntimeRoot,
  '-host', $HostAddress,
  '-port', [string]$Port,
  '-log-level', 'info',
  '-log-style', 'json'
)

try {
  & $exe @bifrostArgs 1>> $stdoutLog 2>> $stderrLog
  $exitCode = $LASTEXITCODE
  Write-AgentCoreLog "bifrost-http exited code=$exitCode"
  exit $exitCode
} catch {
  Write-AgentCoreLog "bifrost-http launch failed: $($_.Exception.Message)"
  throw
}
