<#
.SYNOPSIS
  Stop the AgentCore Serena HTTP session shim with exact-identity ownership checks.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\serena-shim',
  [string]$TaskName = 'AgentCore-Serena-Session-Shim',
  [string]$TaskPath = '\AgentCore\',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 18090,
  [string]$PythonExe = '',
  [string]$ShimScript = ''
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

function Resolve-SerenaShimPython([string]$Root, [string]$Override) {
  if (-not [string]::IsNullOrWhiteSpace($Override) -and (Test-Path -LiteralPath $Override -PathType Leaf)) {
    return (ConvertTo-AgentCoreCanonicalPath $Override)
  }
  $venvPython = Join-Path $Root 'scripts\.venv\Scripts\python.exe'
  if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
    return (ConvertTo-AgentCoreCanonicalPath $venvPython)
  }
  throw "Serena shim Python not found under $Root\scripts\.venv\Scripts\python.exe"
}

function Resolve-SerenaShimScript([string]$Root, [string]$Override) {
  if (-not [string]::IsNullOrWhiteSpace($Override) -and (Test-Path -LiteralPath $Override -PathType Leaf)) {
    return (ConvertTo-AgentCoreCanonicalPath $Override)
  }
  $scriptPath = Join-Path $Root 'scripts\bifrost\serena_session_shim.py'
  if (Test-Path -LiteralPath $scriptPath -PathType Leaf) {
    return (ConvertTo-AgentCoreCanonicalPath $scriptPath)
  }
  throw "Serena shim script missing: $scriptPath"
}

function Get-AgentCoreCommandLineArgument([string]$CommandLine, [string]$Name) {
  if ([string]::IsNullOrWhiteSpace($CommandLine) -or [string]::IsNullOrWhiteSpace($Name)) { return $null }
  # Accept both PowerShell-style -Name and argparse-style --name.
  $pattern = '(?i)(?:^|\s)-{1,2}' + [regex]::Escape($Name) + '(?:\s+|=)(?:"([^"]*)"|(\S+))'
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

function Test-AgentCoreCommandLineContainsPath([string]$CommandLine, [string]$ExpectedPath) {
  $expected = ConvertTo-AgentCoreCanonicalPath $ExpectedPath
  if ([string]::IsNullOrWhiteSpace($expected) -or [string]::IsNullOrWhiteSpace($CommandLine)) {
    return $false
  }
  $escaped = [regex]::Escape($expected)
  return $CommandLine -match ('(?i)' + $escaped)
}

function Test-AgentCoreSerenaShimProcess($Process, [string]$ExpectedPython, [string]$ExpectedShimScript) {
  $actual = ConvertTo-AgentCoreCanonicalPath ([string]$Process.ExecutablePath)
  $expected = ConvertTo-AgentCoreCanonicalPath $ExpectedPython
  if ([string]::IsNullOrWhiteSpace($actual) -or
      -not [string]::Equals($actual, $expected, [StringComparison]::OrdinalIgnoreCase)) {
    return $false
  }
  return (Test-AgentCoreCommandLineContainsPath ([string]$Process.CommandLine) $ExpectedShimScript)
}

function Test-AgentCoreSerenaShimIdentity(
  $Process,
  [string]$ExpectedPython,
  [string]$ExpectedShimScript,
  [string]$ExpectedHostAddress,
  [int]$ExpectedPort
) {
  if (-not (Test-AgentCoreSerenaShimProcess -Process $Process -ExpectedPython $ExpectedPython -ExpectedShimScript $ExpectedShimScript)) {
    return $false
  }
  $commandLine = [string]$Process.CommandLine
  if (-not (Test-AgentCoreCommandLineArgument $commandLine 'host' $ExpectedHostAddress)) { return $false }
  return (Test-AgentCoreCommandLineArgument $commandLine 'port' ([string]$ExpectedPort))
}

function Test-AgentCoreSerenaLauncherProcess(
  $Process,
  [string]$ExpectedLauncherScript,
  [string]$ExpectedRepoRoot,
  [string]$ExpectedRuntimeRoot,
  [string]$ExpectedHostAddress,
  [int]$ExpectedPort
) {
  if ($null -eq $Process) { return $false }
  $parentExe = ConvertTo-AgentCoreCanonicalPath ([string]$Process.ExecutablePath)
  if (-not [string]::Equals([IO.Path]::GetFileName($parentExe), 'pwsh.exe', [StringComparison]::OrdinalIgnoreCase)) {
    return $false
  }
  $commandLine = [string]$Process.CommandLine
  return (Test-AgentCoreCommandLineArgument $commandLine 'File' $ExpectedLauncherScript -PathValue) -and
    (Test-AgentCoreCommandLineArgument $commandLine 'RepoRoot' $ExpectedRepoRoot -PathValue) -and
    (Test-AgentCoreCommandLineArgument $commandLine 'RuntimeRoot' $ExpectedRuntimeRoot -PathValue) -and
    (Test-AgentCoreCommandLineArgument $commandLine 'HostAddress' $ExpectedHostAddress) -and
    (Test-AgentCoreCommandLineArgument $commandLine 'Port' ([string]$ExpectedPort))
}

function Test-AgentCoreOwnedSerenaShimProcess(
  $Process,
  $ProcessTable,
  [string]$ExpectedPython,
  [string]$ExpectedShimScript,
  [string]$ExpectedRepoRoot,
  [string]$ExpectedRuntimeRoot,
  [string]$ExpectedHostAddress,
  [int]$ExpectedPort,
  [string]$ExpectedLauncherScript
) {
  if (-not (Test-AgentCoreSerenaShimIdentity -Process $Process -ExpectedPython $ExpectedPython `
      -ExpectedShimScript $ExpectedShimScript -ExpectedHostAddress $ExpectedHostAddress -ExpectedPort $ExpectedPort)) {
    return $false
  }
  $parentId = [int]$Process.ParentProcessId
  if ($parentId -le 0) { return $false }
  $parent = @($ProcessTable | Where-Object { [int]$_.ProcessId -eq $parentId })
  return ($parent.Count -eq 1) -and
    (Test-AgentCoreSerenaLauncherProcess $parent[0] $ExpectedLauncherScript $ExpectedRepoRoot `
      $ExpectedRuntimeRoot $ExpectedHostAddress $ExpectedPort)
}

function Assert-AgentCoreSerenaPortOwnership(
  $Listeners,
  $ProcessTable,
  [string]$ExpectedPython,
  [string]$ExpectedShimScript,
  [string]$ExpectedRepoRoot,
  [string]$ExpectedRuntimeRoot,
  [string]$ExpectedHostAddress,
  [int]$ExpectedPort,
  [string]$ExpectedLauncherScript
) {
  foreach ($listener in @($Listeners)) {
    $ownerPid = [int]$listener.OwningProcess
    if ($ownerPid -le 0) {
      throw "Port $ExpectedPort has a listener whose process identity is unavailable."
    }
    $owner = @($ProcessTable | Where-Object { [int]$_.ProcessId -eq $ownerPid })
    if (($owner.Count -ne 1) -or
        (-not (Test-AgentCoreOwnedSerenaShimProcess $owner[0] $ProcessTable $ExpectedPython $ExpectedShimScript `
          $ExpectedRepoRoot $ExpectedRuntimeRoot $ExpectedHostAddress $ExpectedPort $ExpectedLauncherScript))) {
      throw "Refusing to stop non-AgentCore process PID=$ownerPid holding port $ExpectedPort."
    }
  }
}

function Assert-AgentCoreSerenaPortIdentityOwnership(
  $Listeners,
  $ProcessTable,
  [string]$ExpectedPython,
  [string]$ExpectedShimScript,
  [string]$ExpectedHostAddress,
  [int]$ExpectedPort
) {
  foreach ($listener in @($Listeners)) {
    $ownerPid = [int]$listener.OwningProcess
    if ($ownerPid -le 0) {
      throw "Port $ExpectedPort has a listener whose process identity is unavailable."
    }
    $owner = @($ProcessTable | Where-Object { [int]$_.ProcessId -eq $ownerPid })
    if (($owner.Count -ne 1) -or
        (-not (Test-AgentCoreSerenaShimIdentity $owner[0] $ExpectedPython $ExpectedShimScript $ExpectedHostAddress $ExpectedPort))) {
      throw "Refusing to stop non-AgentCore process PID=$ownerPid holding port $ExpectedPort."
    }
  }
}

function Get-AgentCoreSerenaProcessSnapshot([int]$ExpectedPort) {
  return [pscustomobject]@{
    Processes = @(Get-CimInstance Win32_Process -ErrorAction Stop)
    Listeners = @(Get-NetTCPConnection -LocalPort $ExpectedPort -State Listen -ErrorAction SilentlyContinue)
  }
}

function Get-AgentCoreDescendantProcessIds([int]$RootProcessId, $ProcessTable) {
  $result = [Collections.Generic.List[int]]::new()
  $pending = [Collections.Generic.Queue[int]]::new()
  $pending.Enqueue($RootProcessId)
  $seen = [Collections.Generic.HashSet[int]]::new()
  while ($pending.Count -gt 0) {
    $current = $pending.Dequeue()
    if (-not $seen.Add($current)) { continue }
    foreach ($child in @($ProcessTable | Where-Object { [int]$_.ParentProcessId -eq $current })) {
      $childId = [int]$child.ProcessId
      $result.Add($childId)
      $pending.Enqueue($childId)
    }
  }
  return @($result)
}

function Stop-AgentCoreSerenaSessionShim {
  $RepoRoot = ConvertTo-AgentCoreCanonicalPath $RepoRoot
  $RuntimeRoot = ConvertTo-AgentCoreCanonicalPath $RuntimeRoot
  $expectedPython = Resolve-SerenaShimPython -Root $RepoRoot -Override $PythonExe
  $expectedShim = Resolve-SerenaShimScript -Root $RepoRoot -Override $ShimScript
  $expectedLauncher = Join-Path $PSScriptRoot 'Launch-AgentCoreSerenaSessionShim.ps1'

  $preflight = Get-AgentCoreSerenaProcessSnapshot -ExpectedPort $Port
  Assert-AgentCoreSerenaPortOwnership -Listeners $preflight.Listeners -ProcessTable $preflight.Processes `
    -ExpectedPython $expectedPython -ExpectedShimScript $expectedShim `
    -ExpectedRepoRoot $RepoRoot -ExpectedRuntimeRoot $RuntimeRoot `
    -ExpectedHostAddress $HostAddress -ExpectedPort $Port -ExpectedLauncherScript $expectedLauncher

  $maintenanceMarker = Join-Path $RuntimeRoot 'state\serena-shim-maintenance.marker'
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $maintenanceMarker) | Out-Null
  Set-Content -LiteralPath $maintenanceMarker -Value 'stop_requested' -Encoding utf8
  Write-Host '[Stop] Maintenance marker set; Start clears it after readiness succeeds.'

  try {
    Stop-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
    Write-Host "[Stop] Stopped scheduled task $TaskPath$TaskName"
  } catch {
    Write-Host "[Stop] Scheduled task stop skipped: $($_.Exception.Message)"
  }

  $postTask = Get-AgentCoreSerenaProcessSnapshot -ExpectedPort $Port
  Assert-AgentCoreSerenaPortIdentityOwnership -Listeners $postTask.Listeners -ProcessTable $postTask.Processes `
    -ExpectedPython $expectedPython -ExpectedShimScript $expectedShim `
    -ExpectedHostAddress $HostAddress -ExpectedPort $Port

  $stoppedProcessIds = [Collections.Generic.HashSet[int]]::new()
  foreach ($listener in @($postTask.Listeners)) {
    $processId = [int]$listener.OwningProcess
    if (-not $stoppedProcessIds.Add($processId)) { continue }
    $descendants = Get-AgentCoreDescendantProcessIds -RootProcessId $processId -ProcessTable $postTask.Processes
    foreach ($childId in $descendants) {
      if ($stoppedProcessIds.Add($childId)) {
        Write-Host "[Stop] Stopping Serena shim descendant PID $childId"
        Stop-Process -Id $childId -Force -ErrorAction SilentlyContinue
      }
    }
    Write-Host "[Stop] Stopping AgentCore Serena shim PID $processId"
    Stop-Process -Id $processId -Force -ErrorAction Stop
  }

  foreach ($process in $postTask.Processes) {
    $processId = [int]$process.ProcessId
    if (-not $stoppedProcessIds.Add($processId)) { continue }
    if (-not (Test-AgentCoreSerenaShimIdentity -Process $process -ExpectedPython $expectedPython `
        -ExpectedShimScript $expectedShim -ExpectedHostAddress $HostAddress -ExpectedPort $Port)) {
      continue
    }
    $descendants = Get-AgentCoreDescendantProcessIds -RootProcessId $processId -ProcessTable $postTask.Processes
    foreach ($childId in $descendants) {
      if ($stoppedProcessIds.Add($childId)) {
        Write-Host "[Stop] Stopping Serena shim descendant PID $childId"
        Stop-Process -Id $childId -Force -ErrorAction SilentlyContinue
      }
    }
    Write-Host "[Stop] Stopping AgentCore Serena shim identity match PID $processId"
    Stop-Process -Id $processId -Force -ErrorAction Stop
  }

  # Launcher may remain in maintenance-suppressed wait with no listener yet.
  foreach ($process in $postTask.Processes) {
    $processId = [int]$process.ProcessId
    if (-not $stoppedProcessIds.Add($processId)) { continue }
    if (-not (Test-AgentCoreSerenaLauncherProcess -Process $process -ExpectedLauncherScript $expectedLauncher `
        -ExpectedRepoRoot $RepoRoot -ExpectedRuntimeRoot $RuntimeRoot `
        -ExpectedHostAddress $HostAddress -ExpectedPort $Port)) {
      continue
    }
    Write-Host "[Stop] Stopping AgentCore Serena launcher PID $processId"
    Stop-Process -Id $processId -Force -ErrorAction Stop
  }

  Write-Host '[Stop] Done'
}

if ($MyInvocation.InvocationName -ne '.') {
  Stop-AgentCoreSerenaSessionShim
}
