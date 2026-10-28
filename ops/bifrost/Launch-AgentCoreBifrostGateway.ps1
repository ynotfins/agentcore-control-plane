<#
.SYNOPSIS
  Run the AgentCore Bifrost Gateway as the foreground process for the Windows startup owner.

.DESCRIPTION
  This script is intentionally long-running. The scheduled task should own this
  PowerShell process, and this PowerShell process owns bifrost-http.exe in the
  foreground. If bifrost exits unexpectedly, this script restarts it quietly so
  clean-but-unexpected exits do not leave the gateway offline.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080,
  [int]$BuilderCompatPort = 18082,
  [int]$MaxDependencyWaitSeconds = 180,
  [switch]$RequireRedisVectorStore,
  [long]$MaxLogBytes = 50MB,
  [int]$InitialRestartBackoffSeconds = 2,
  [int]$MaxRestartBackoffSeconds = 30,
  [int]$MinRunSecondsForBackoffReset = 30,
  [int]$MaintenanceMarkerTtlSeconds = 900
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
  if ([string]::IsNullOrWhiteSpace($Endpoint)) { return $true }
  $deadline = (Get-Date).AddSeconds($MaxDependencyWaitSeconds)
  $lastLogAt = [datetime]::MinValue
  while ((Get-Date) -lt $deadline) {
    if (Test-TcpEndpoint $Endpoint) {
      Write-AgentCoreLog "REDIS_VECTOR_STORE_READY endpoint=$Endpoint"
      return $true
    }
    if (((Get-Date) - $lastLogAt).TotalSeconds -ge 30) {
      Write-AgentCoreLog "Waiting for redis vector store $Endpoint"
      $lastLogAt = Get-Date
    }
    Start-Sleep -Seconds 2
  }
  Write-AgentCoreLog "REDIS_VECTOR_STORE_DEGRADED endpoint=$Endpoint waited_seconds=$MaxDependencyWaitSeconds"
  return $false
}

function ConvertTo-AgentCoreCanonicalPath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return '' }
  try { return [IO.Path]::GetFullPath($Path).TrimEnd('\', '/') } catch { return '' }
}

function Get-AgentCoreCommandLineArgument([string]$CommandLine, [string]$Name) {
  if ([string]::IsNullOrWhiteSpace($CommandLine) -or [string]::IsNullOrWhiteSpace($Name)) { return $null }
  $pattern = '(?i)(?:^|\s)-' + [regex]::Escape($Name) + '(?:\s+|=)(?:"([^"]*)"|(\S+))'
  $match = [regex]::Match($CommandLine, $pattern)
  if (-not $match.Success) { return $null }
  if ($match.Groups[1].Success) { return $match.Groups[1].Value }
  return $match.Groups[2].Value
}

function Test-AgentCoreCommandLineArgument([string]$CommandLine, [string]$Name, [string]$ExpectedValue, [switch]$PathValue) {
  $actual = Get-AgentCoreCommandLineArgument -CommandLine $CommandLine -Name $Name
  if ($null -eq $actual) { return $false }
  if ($PathValue) {
    $actual = ConvertTo-AgentCoreCanonicalPath $actual
    $ExpectedValue = ConvertTo-AgentCoreCanonicalPath $ExpectedValue
  }
  return (-not [string]::IsNullOrWhiteSpace($actual)) -and
    [string]::Equals($actual, $ExpectedValue, [StringComparison]::OrdinalIgnoreCase)
}

function Test-AgentCoreLauncherProcess($Process, [string]$ExpectedLauncherScript, [string]$ExpectedRuntimeRoot, [string]$ExpectedHostAddress, [int]$ExpectedPort) {
  if ($null -eq $Process) { return $false }
  $parentExe = ConvertTo-AgentCoreCanonicalPath ([string]$Process.ExecutablePath)
  if (-not [string]::Equals([IO.Path]::GetFileName($parentExe), 'pwsh.exe', [StringComparison]::OrdinalIgnoreCase)) { return $false }
  $commandLine = [string]$Process.CommandLine
  return (Test-AgentCoreCommandLineArgument $commandLine 'File' $ExpectedLauncherScript -PathValue) -and
    (Test-AgentCoreCommandLineArgument $commandLine 'RuntimeRoot' $ExpectedRuntimeRoot -PathValue) -and
    (Test-AgentCoreCommandLineArgument $commandLine 'HostAddress' $ExpectedHostAddress) -and
    (Test-AgentCoreCommandLineArgument $commandLine 'Port' ([string]$ExpectedPort))
}

function Test-AgentCoreOwnedProcess([int]$ProcessId, [string]$ExpectedExe, [string]$ExpectedRuntimeRoot, [string]$ExpectedHostAddress, [int]$ExpectedPort, [string]$ExpectedLauncherScript) {
  try {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop
  } catch { return $false }
  if ($null -eq $process) { return $false }
  $actualExe = ConvertTo-AgentCoreCanonicalPath ([string]$process.ExecutablePath)
  $expectedExePath = ConvertTo-AgentCoreCanonicalPath $ExpectedExe
  if (-not [string]::Equals($actualExe, $expectedExePath, [StringComparison]::OrdinalIgnoreCase)) { return $false }

  $commandLine = [string]$process.CommandLine
  if (-not (Test-AgentCoreCommandLineArgument $commandLine 'app-dir' $ExpectedRuntimeRoot -PathValue)) { return $false }
  if (-not (Test-AgentCoreCommandLineArgument $commandLine 'host' $ExpectedHostAddress)) { return $false }
  if (-not (Test-AgentCoreCommandLineArgument $commandLine 'port' ([string]$ExpectedPort))) { return $false }

  $parentId = [int]$process.ParentProcessId
  if ($parentId -le 0) { return $false }
  try {
    $parent = Get-CimInstance Win32_Process -Filter "ProcessId = $parentId" -ErrorAction Stop
  } catch { return $false }
  return Test-AgentCoreLauncherProcess $parent $ExpectedLauncherScript $ExpectedRuntimeRoot $ExpectedHostAddress $ExpectedPort
}

function Stop-AgentCoreOwnedProcess([int]$ProcessId, [string]$Reason) {
  if (-not (Test-AgentCoreOwnedProcess -ProcessId $ProcessId -ExpectedExe $exe -ExpectedRuntimeRoot $RuntimeRoot `
      -ExpectedHostAddress $HostAddress -ExpectedPort $Port -ExpectedLauncherScript $launchScriptPath)) {
    throw "Refusing to stop non-AgentCore process PID=$ProcessId reason=$Reason port=$Port"
  }
  Write-AgentCoreLog "Stopping AgentCore-owned process PID=$ProcessId reason=$Reason"
  Stop-Process -Id $ProcessId -Force -ErrorAction Stop
}

function Invoke-LogRotation {
  $rotationScript = Join-Path $PSScriptRoot 'Rotate-BifrostLogs.ps1'
  if (-not (Test-Path -LiteralPath $rotationScript)) {
    Write-AgentCoreLog "Log rotation skipped: missing $rotationScript"
    return
  }
  try {
    & $rotationScript -LogDir $logDir -MaxBytes $MaxLogBytes -KeepCount 0 | ForEach-Object {
      Write-AgentCoreLog "log_rotation: $_"
    }
  } catch {
    Write-AgentCoreLog "Log rotation skipped: $($_.Exception.Message)"
  }
}

function Get-MaintenanceMarkerInfo {
  if (-not (Test-Path -LiteralPath $maintenanceMarker)) {
    return [pscustomobject]@{ Present = $false; Value = ''; AgeSeconds = $null; Active = $false }
  }
  $item = Get-Item -LiteralPath $maintenanceMarker -ErrorAction Stop
  $ageSeconds = [math]::Floor(((Get-Date).ToUniversalTime() - $item.LastWriteTimeUtc).TotalSeconds)
  $value = ''
  try { $value = ((Get-Content -LiteralPath $maintenanceMarker -Raw -ErrorAction Stop) ?? '').Trim() } catch { $value = '' }
  $active = ($ageSeconds -le $MaintenanceMarkerTtlSeconds)
  return [pscustomobject]@{ Present = $true; Value = $value; AgeSeconds = $ageSeconds; Active = $active }
}

function Test-StopMaintenanceMarker {
  $marker = Get-MaintenanceMarkerInfo
  if (-not $marker.Present) { return $false }
  if (-not $marker.Active) {
    Write-AgentCoreLog "Maintenance marker stale; ignoring for launcher age_seconds=$($marker.AgeSeconds)"
    return $false
  }
  return -not [string]::Equals([string]$marker.Value, 'start_requested', [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-NextRestartBackoff([int]$CurrentBackoff, [double]$RuntimeSeconds) {
  if ($RuntimeSeconds -ge $MinRunSecondsForBackoffReset) { return $InitialRestartBackoffSeconds }
  $next = [Math]::Max($InitialRestartBackoffSeconds, $CurrentBackoff * 2)
  return [Math]::Min($next, $MaxRestartBackoffSeconds)
}

$stateDir = Join-Path $RuntimeRoot 'state'
$logDir = Join-Path $RuntimeRoot 'logs'
$launchScriptPath = $PSCommandPath
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$maintenanceMarker = Join-Path $stateDir 'bifrost-maintenance.marker'
$stdoutLog = Join-Path $logDir 'bifrost-gateway.stdout.log'
$stderrLog = Join-Path $logDir 'bifrost-gateway.stderr.log'

# Copy all Windows User env vars into this process. Scheduled tasks may start
# with an environment snapshot that predates AgentCore VK/profile variables.
[Environment]::GetEnvironmentVariables('User').GetEnumerator() | ForEach-Object {
  Set-Item -Path ("Env:{0}" -f $_.Key) -Value ([string]$_.Value) -Force
}

function Ensure-BuilderCompatProxy {
  $proxyScript = Join-Path $PSScriptRoot 'agentcore-builder-compat-proxy.cjs'
  $callerResolver = Join-Path $PSScriptRoot 'Resolve-AgentCoreBuilderCaller.ps1'
  $node = 'C:\Users\ynotf\AppData\Local\pnpm\bin\node.exe'
  if (-not (Test-Path -LiteralPath $proxyScript -PathType Leaf) -or
      -not (Test-Path -LiteralPath $callerResolver -PathType Leaf) -or
      -not (Test-Path -LiteralPath $node -PathType Leaf)) {
    throw 'Builder compatibility proxy runtime is incomplete.'
  }
  if ([string]::IsNullOrWhiteSpace($env:BIFROST_MCP_VIRTUAL_KEY)) {
    throw 'Builder compatibility proxy identity is unavailable.'
  }
  $listener = Get-NetTCPConnection -LocalPort $BuilderCompatPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($listener) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction Stop
    if (([string]$process.CommandLine).IndexOf($proxyScript, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
      throw "Port $BuilderCompatPort is owned by a non-AgentCore process."
    }
    return
  }
  $env:AGENTCORE_BUILDER_COMPAT_PORT = [string]$BuilderCompatPort
  Start-Process -FilePath $node -ArgumentList @($proxyScript) -WorkingDirectory $PSScriptRoot `
    -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDir 'builder-compat.stdout.log') `
    -RedirectStandardError (Join-Path $logDir 'builder-compat.stderr.log') | Out-Null
  $deadline = (Get-Date).AddSeconds(15)
  do {
    Start-Sleep -Milliseconds 250
    try {
      if ((Invoke-WebRequest -Uri "http://127.0.0.1:$BuilderCompatPort/healthz" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { return }
    } catch {}
  } while ((Get-Date) -lt $deadline)
  throw 'Builder compatibility proxy did not become healthy.'
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

Write-AgentCoreLog "Launching AgentCore Bifrost Gateway supervisor"
Write-AgentCoreLog "exe=$exe"
Write-AgentCoreLog "app_dir=$RuntimeRoot"
Write-AgentCoreLog "bind=${HostAddress}:${Port}"
Write-AgentCoreLog ("BIFROST_MCP_VIRTUAL_KEY present={0} length={1}" -f (-not [string]::IsNullOrWhiteSpace($env:BIFROST_MCP_VIRTUAL_KEY)), ($env:BIFROST_MCP_VIRTUAL_KEY ?? '').Length)
Write-AgentCoreLog ("BIFROST_ENCRYPTION_KEY present={0}" -f (-not [string]::IsNullOrWhiteSpace($env:BIFROST_ENCRYPTION_KEY)))
Write-AgentCoreLog "stdout_log=$stdoutLog"
Write-AgentCoreLog "stderr_log=$stderrLog"

$bifrostArgs = @(
  '-app-dir', $RuntimeRoot,
  '-host', $HostAddress,
  '-port', [string]$Port,
  '-log-level', 'info',
  '-log-style', 'json'
)

$restartBackoffSeconds = $InitialRestartBackoffSeconds

try {
  Ensure-BuilderCompatProxy
  Write-AgentCoreLog "BUILDER_COMPAT_PROXY_READY port=$BuilderCompatPort"
} catch {
  Write-AgentCoreLog "BUILDER_COMPAT_PROXY_DEGRADED port=$BuilderCompatPort reason=$($_.Exception.Message)"
}

while ($true) {
  if (Test-StopMaintenanceMarker) {
    Write-AgentCoreLog 'LAUNCH_SUPPRESSED maintenance_marker'
    exit 0
  }

  $redisReady = Wait-ForRedisVectorStore $redisEndpoint
  if ((-not $redisReady) -and $RequireRedisVectorStore) {
    throw "Redis vector store dependency unavailable after ${MaxDependencyWaitSeconds}s: $redisEndpoint"
  }

  # Ensure this scheduled task becomes the sole runtime owner without killing unrelated listeners.
  Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
      if ($_.OwningProcess) {
        Stop-AgentCoreOwnedProcess -ProcessId $_.OwningProcess -Reason "listener:${Port}"
      }
    }
  Start-Sleep -Seconds 1
  Invoke-LogRotation

  $startedAt = Get-Date
  $exitCode = 1
  try {
    Write-AgentCoreLog "Starting bifrost-http process..."
    & $exe @bifrostArgs 1>> $stdoutLog 2>> $stderrLog
    $exitCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
  } catch {
    $exitCode = 1
    Write-AgentCoreLog "bifrost-http launch failed: $($_.Exception.Message)"
  }

  $runtimeSeconds = ((Get-Date) - $startedAt).TotalSeconds
  Write-AgentCoreLog ("bifrost-http process exited code={0} runtime_seconds={1:N1}" -f $exitCode, $runtimeSeconds)

  if (Test-StopMaintenanceMarker) {
    Write-AgentCoreLog "SUPERVISOR_EXIT maintenance_marker code=$exitCode"
    exit $exitCode
  }

  $restartBackoffSeconds = Get-NextRestartBackoff -CurrentBackoff $restartBackoffSeconds -RuntimeSeconds $runtimeSeconds
  Write-AgentCoreLog "SUPERVISOR_RESTART delay_seconds=$restartBackoffSeconds previous_exit_code=$exitCode"
  Start-Sleep -Seconds $restartBackoffSeconds
}
