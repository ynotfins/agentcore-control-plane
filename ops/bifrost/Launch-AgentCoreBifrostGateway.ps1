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
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080,
  [int]$MaxDependencyWaitSeconds = 180
)

$ErrorActionPreference = 'Stop'

function Write-AgentCoreLog([string]$Message) {
  $line = "[{0}] {1}" -f (Get-Date).ToString('o'), $Message
  Write-Host $line
}

function Test-TcpEndpoint([string]$Endpoint) {
  $parts = $Endpoint -split ':'
  if ($parts.Count -lt 2) { return $false }
  $targetPort = 0
  if (-not [int]::TryParse($parts[-1], [ref]$targetPort)) { return $false }
  $targetHost = ($parts[0..($parts.Count - 2)] -join ':').Trim('[', ']')
  if ([string]::IsNullOrWhiteSpace($targetHost)) { return $false }

  $client = [System.Net.Sockets.TcpClient]::new()
  try {
    $connect = $client.BeginConnect($targetHost, $targetPort, $null, $null)
    if (-not $connect.AsyncWaitHandle.WaitOne(1000, $false)) { return $false }
    $client.EndConnect($connect)
    return $true
  } catch {
    return $false
  } finally {
    $client.Dispose()
  }
}

function Get-RedisVectorStoreEndpoint([string]$ConfigPath) {
  try {
    $config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding utf8 | ConvertFrom-Json -Depth 100
  } catch {
    Write-AgentCoreLog "Dependency preflight skipped: config parse failed"
    return ''
  }
  if (($config.vector_store.enabled -eq $true) -and ($config.vector_store.type -eq 'redis')) {
    return [string]$config.vector_store.config.addr
  }
  return ''
}

function Wait-ForRedisVectorStore([string]$Endpoint) {
  if ([string]::IsNullOrWhiteSpace($Endpoint)) { return }
  $deadline = (Get-Date).AddSeconds($MaxDependencyWaitSeconds)
  $lastLogAt = [datetime]::MinValue
  while ((Get-Date) -lt $deadline) {
    if (Test-TcpEndpoint $Endpoint) {
      Write-AgentCoreLog "Dependency ready: redis vector store $Endpoint"
      return
    }
    if (((Get-Date) - $lastLogAt).TotalSeconds -ge 30) {
      Write-AgentCoreLog "Waiting for redis vector store $Endpoint"
      $lastLogAt = Get-Date
    }
    Start-Sleep -Seconds 2
  }
  throw "Redis vector store dependency unavailable after ${MaxDependencyWaitSeconds}s: $Endpoint"
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
# Obsidian vault MCP upstream disabled 2026-07-22; env defaults removed.
# Restore if re-enabling obsidian_vault:
#   if (-not $env:OBSIDIAN_BASE_URL) { $env:OBSIDIAN_BASE_URL = 'https://127.0.0.1:27124' }
#   if (-not $env:OBSIDIAN_VERIFY_SSL) { $env:OBSIDIAN_VERIFY_SSL = 'false' }

$exe = Join-Path $RuntimeRoot 'bin\bifrost-http.exe'
if (-not (Test-Path -LiteralPath $exe)) {
  throw "Missing Bifrost binary: $exe"
}

$configPath = Join-Path $RuntimeRoot 'config.json'
if (-not (Test-Path -LiteralPath $configPath)) {
  throw "Missing Bifrost config: $configPath"
}
$redisEndpoint = Get-RedisVectorStoreEndpoint $configPath

Write-AgentCoreLog "Launching AgentCore Bifrost Gateway"
Write-AgentCoreLog "exe=$exe"
Write-AgentCoreLog "app_dir=$RuntimeRoot"
Write-AgentCoreLog "bind=${HostAddress}:${Port}"
Write-AgentCoreLog ("BIFROST_MCP_VIRTUAL_KEY present={0} length={1}" -f (-not [string]::IsNullOrWhiteSpace($env:BIFROST_MCP_VIRTUAL_KEY)), ($env:BIFROST_MCP_VIRTUAL_KEY ?? '').Length)
Write-AgentCoreLog ("BIFROST_ENCRYPTION_KEY present={0}" -f (-not [string]::IsNullOrWhiteSpace($env:BIFROST_ENCRYPTION_KEY)))
Write-AgentCoreLog "stdout_log=$stdoutLog"
Write-AgentCoreLog "stderr_log=$stderrLog"
Wait-ForRedisVectorStore $redisEndpoint

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
  Write-AgentCoreLog "Starting bifrost-http process..."
  & $exe @bifrostArgs 1>> $stdoutLog 2>> $stderrLog
  $exitCode = $LASTEXITCODE
  Write-AgentCoreLog "bifrost-http process exited code=$exitCode"
  exit $exitCode
} catch {
  Write-AgentCoreLog 'bifrost-http launch failed'
  exit 1
}
