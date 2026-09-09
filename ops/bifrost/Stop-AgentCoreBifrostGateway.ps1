<#
.SYNOPSIS
  Stop the AgentCore Bifrost MCP Gateway.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$TaskPath = '\AgentCore\',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'

function ConvertTo-AgentCoreCanonicalPath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return '' }
  try {
    return [System.IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
  } catch {
    return ''
  }
}

function Test-AgentCoreBifrostProcess($Process, [string]$ExpectedExe) {
  $actual = ConvertTo-AgentCoreCanonicalPath ([string]$Process.ExecutablePath)
  $expected = ConvertTo-AgentCoreCanonicalPath $ExpectedExe
  return (-not [string]::IsNullOrWhiteSpace($actual)) -and
    [string]::Equals($actual, $expected, [System.StringComparison]::OrdinalIgnoreCase)
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

function Test-AgentCoreBifrostIdentity($Process, [string]$ExpectedExe, [string]$ExpectedRuntimeRoot, [string]$ExpectedHostAddress, [int]$ExpectedPort) {
  if (-not (Test-AgentCoreBifrostProcess -Process $Process -ExpectedExe $ExpectedExe)) { return $false }
  $commandLine = [string]$Process.CommandLine
  if (-not (Test-AgentCoreCommandLineArgument $commandLine 'app-dir' $ExpectedRuntimeRoot -PathValue)) { return $false }
  if (-not (Test-AgentCoreCommandLineArgument $commandLine 'host' $ExpectedHostAddress)) { return $false }
  return (Test-AgentCoreCommandLineArgument $commandLine 'port' ([string]$ExpectedPort))
}

function Test-AgentCoreOwnedBifrostProcess($Process, $ProcessTable, [string]$ExpectedExe, [string]$ExpectedRuntimeRoot, [string]$ExpectedHostAddress, [int]$ExpectedPort, [string]$ExpectedLauncherScript) {
  if (-not (Test-AgentCoreBifrostIdentity -Process $Process -ExpectedExe $ExpectedExe -ExpectedRuntimeRoot $ExpectedRuntimeRoot -ExpectedHostAddress $ExpectedHostAddress -ExpectedPort $ExpectedPort)) {
    return $false
  }
  $parentId = [int]$Process.ParentProcessId
  if ($parentId -le 0) { return $false }
  $parent = @($ProcessTable | Where-Object { [int]$_.ProcessId -eq $parentId })
  return ($parent.Count -eq 1) -and
    (Test-AgentCoreLauncherProcess $parent[0] $ExpectedLauncherScript $ExpectedRuntimeRoot $ExpectedHostAddress $ExpectedPort)
}

function Test-AgentCoreBuilderProxyProcess($Process, [string]$ExpectedNode, [string]$ExpectedScript) {
  if (-not (Test-AgentCoreBifrostProcess -Process $Process -ExpectedExe $ExpectedNode)) {
    return $false
  }

  $node = [regex]::Escape((ConvertTo-AgentCoreCanonicalPath $ExpectedNode))
  $script = [regex]::Escape((ConvertTo-AgentCoreCanonicalPath $ExpectedScript))
  if ([string]::IsNullOrWhiteSpace($node) -or [string]::IsNullOrWhiteSpace($script)) {
    return $false
  }

  # The launcher starts Node with the proxy script as its only argument. Match
  # that complete command line, including optional Windows quoting.
  $pattern = '^\s*"?' + $node + '"?\s+"?' + $script + '"?\s*$'
  return ([string]$Process.CommandLine) -match $pattern
}

function Assert-AgentCorePortOwnership($Listeners, $ProcessTable, [string]$ExpectedExe, [string]$ExpectedRuntimeRoot, [string]$ExpectedHostAddress, [int]$ExpectedPort, [string]$ExpectedLauncherScript) {
  foreach ($listener in @($Listeners)) {
    $ownerPid = [int]$listener.OwningProcess
    if ($ownerPid -le 0) {
      throw "Port $ExpectedPort has a listener whose process identity is unavailable."
    }
    $owner = @($ProcessTable | Where-Object { [int]$_.ProcessId -eq $ownerPid })
    if (($owner.Count -ne 1) -or
        (-not (Test-AgentCoreOwnedBifrostProcess $owner[0] $ProcessTable $ExpectedExe $ExpectedRuntimeRoot $ExpectedHostAddress $ExpectedPort $ExpectedLauncherScript))) {
      throw "Refusing to stop non-AgentCore process PID=$ownerPid holding port $ExpectedPort."
    }
  }
}

function Assert-AgentCorePortIdentityOwnership($Listeners, $ProcessTable, [string]$ExpectedExe, [string]$ExpectedRuntimeRoot, [string]$ExpectedHostAddress, [int]$ExpectedPort) {
  foreach ($listener in @($Listeners)) {
    $ownerPid = [int]$listener.OwningProcess
    if ($ownerPid -le 0) {
      throw "Port $ExpectedPort has a listener whose process identity is unavailable."
    }
    $owner = @($ProcessTable | Where-Object { [int]$_.ProcessId -eq $ownerPid })
    if (($owner.Count -ne 1) -or
        (-not (Test-AgentCoreBifrostIdentity $owner[0] $ExpectedExe $ExpectedRuntimeRoot $ExpectedHostAddress $ExpectedPort))) {
      throw "Refusing to stop non-AgentCore process PID=$ownerPid holding port $ExpectedPort."
    }
  }
}

function Get-AgentCoreGatewayProcessSnapshot([int]$ExpectedPort) {
  return [pscustomobject]@{
    Processes = @(Get-CimInstance Win32_Process -ErrorAction Stop)
    Listeners = @(Get-NetTCPConnection -LocalPort $ExpectedPort -State Listen -ErrorAction SilentlyContinue)
  }
}

function Stop-AgentCoreBifrostGateway {
  $expectedExe = Join-Path $RuntimeRoot 'bin\bifrost-http.exe'
  $expectedLauncher = Join-Path $PSScriptRoot 'Launch-AgentCoreBifrostGateway.ps1'

  # This preflight is deliberately the first operation. A foreign listener
  # must cause zero state mutation: no marker write and no scheduled-task stop.
  $preflight = Get-AgentCoreGatewayProcessSnapshot -ExpectedPort $Port
  Assert-AgentCorePortOwnership -Listeners $preflight.Listeners -ProcessTable $preflight.Processes `
    -ExpectedExe $expectedExe -ExpectedRuntimeRoot $RuntimeRoot -ExpectedHostAddress $HostAddress `
    -ExpectedPort $Port -ExpectedLauncherScript $expectedLauncher

  $maintenanceMarker = Join-Path $RuntimeRoot 'state\bifrost-maintenance.marker'
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $maintenanceMarker) | Out-Null
  Set-Content -LiteralPath $maintenanceMarker -Value 'stop_requested' -Encoding utf8
  Write-Host '[Stop] Maintenance marker set; Start clears it after health succeeds.'

  try {
    Stop-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
    Write-Host "[Stop] Stopped scheduled task $TaskPath$TaskName"
  } catch {
    Write-Host "[Stop] Scheduled task stop skipped: $($_.Exception.Message)"
  }

  # The scheduled-task stop can change the process tree. Refresh and revalidate
  # before selecting termination targets so stale PIDs are never acted on.
  # After task stop the launcher parent may already be gone, so accept exact
  # bifrost identity (exe + app-dir/host/port) rather than live-parent ownership.
  $postTask = Get-AgentCoreGatewayProcessSnapshot -ExpectedPort $Port
  Assert-AgentCorePortIdentityOwnership -Listeners $postTask.Listeners -ProcessTable $postTask.Processes `
    -ExpectedExe $expectedExe -ExpectedRuntimeRoot $RuntimeRoot -ExpectedHostAddress $HostAddress `
    -ExpectedPort $Port

  $stoppedProcessIds = [Collections.Generic.HashSet[int]]::new()
  foreach ($listener in @($postTask.Listeners)) {
    $processId = [int]$listener.OwningProcess
    if (-not $stoppedProcessIds.Add($processId)) { continue }
    $process = @($postTask.Processes | Where-Object { [int]$_.ProcessId -eq $processId })[0]
    Write-Host "[Stop] Stopping AgentCore Bifrost PID $($process.ProcessId)"
    Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
  }

  # Listener discovery can miss AgentCore processes (non-elevated Get-NetTCPConnection),
  # and Stop-ScheduledTask may already have reaped the launcher parent. Kill remaining
  # exact-identity bifrost-http processes for this runtime/host/port.
  foreach ($process in $postTask.Processes) {
    $processId = [int]$process.ProcessId
    if (-not $stoppedProcessIds.Add($processId)) { continue }
    if (-not (Test-AgentCoreBifrostIdentity -Process $process -ExpectedExe $expectedExe -ExpectedRuntimeRoot $RuntimeRoot -ExpectedHostAddress $HostAddress -ExpectedPort $Port)) {
      continue
    }
    Write-Host "[Stop] Stopping AgentCore Bifrost identity match PID $processId"
    Stop-Process -Id $processId -Force -ErrorAction Stop
  }

  $compatScript = Join-Path $PSScriptRoot 'agentcore-builder-compat-proxy.cjs'
  $node = 'C:\Users\ynotf\AppData\Local\pnpm\bin\node.exe'
  foreach ($process in $postTask.Processes) {
    if (Test-AgentCoreBuilderProxyProcess -Process $process -ExpectedNode $node -ExpectedScript $compatScript) {
      Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
      Write-Host "[Stop] Stopped builder compatibility proxy PID $($process.ProcessId)"
    }
  }

  Write-Host '[Stop] Done'
}

if ($MyInvocation.InvocationName -ne '.') {
  Stop-AgentCoreBifrostGateway
}
