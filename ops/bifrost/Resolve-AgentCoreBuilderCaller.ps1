<#
.SYNOPSIS
  Resolve a loopback builder-proxy TCP peer to an approved Trust Class A client.

.DESCRIPTION
  Windows does not expose a peer PID through Node's TCP socket API. This helper
  maps the client-side loopback tuple to its owning PID with netstat, then walks
  the live process ancestry and requires an exact, canonical executable path.
  Any missing, ambiguous, stale, or unrecognized identity fails closed.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)]
  [ValidateRange(1, 65535)]
  [int]$ServerPort,

  [Parameter(Mandatory)]
  [ValidateRange(1, 65535)]
  [int]$ClientPort,

  # Offline test inputs. The live proxy never supplies these parameters.
  [int]$TestClientPid = 0,
  [string]$TestCandidatePidsJson = '',
  [string]$TestProcessTableJson = ''
)

$ErrorActionPreference = 'Stop'

function Write-ResolutionFailure([string]$Code) {
  if ($env:AGENTCORE_BUILDER_CALLER_TEST_MODE -ne '1') {
    $logDir = 'F:\AgentCore\runtime\bifrost\logs'
    try {
      if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
      $line = '[{0}] caller_denied code={1}' -f (Get-Date).ToUniversalTime().ToString('o'), $Code
      Add-Content -LiteralPath (Join-Path $logDir 'builder-compat.stderr.log') -Value $line -Encoding utf8
    } catch {}
  }
  [pscustomobject]@{ allowed = $false; code = $Code } | ConvertTo-Json -Compress
  exit 1
}

function Get-CanonicalPath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return '' }
  try {
    return [System.IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($Path)).TrimEnd('\')
  } catch {
    return ''
  }
}

$localAppData = [Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)
$programFiles = [Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFiles)
$trustedExecutables = @(
  [pscustomobject]@{ client = 'antigravity'; path = (Join-Path $localAppData 'Programs\Antigravity IDE\Antigravity IDE.exe') },
  [pscustomobject]@{ client = 'devin'; path = (Join-Path $localAppData 'Programs\Devin Next\Devin - Next.exe') },
  [pscustomobject]@{ client = 'devin'; path = (Join-Path $localAppData 'devin\cli\bin\devin.exe') },
  [pscustomobject]@{ client = 'devin'; path = (Join-Path $localAppData 'devin\cli-next\bin\devin-next.exe') },
  [pscustomobject]@{ client = 'eigent'; path = (Join-Path $localAppData 'Programs\Eigent\Eigent.exe') },
  [pscustomobject]@{ client = 'minimax-code'; path = (Join-Path $localAppData 'Programs\MiniMax Code\MiniMax Code.exe') },
  [pscustomobject]@{ client = 'open-interpreter-desktop'; path = (Join-Path $localAppData 'Programs\Open Interpreter\bin\interpreter.exe') },
  [pscustomobject]@{ client = 'open-interpreter-desktop'; path = (Join-Path $programFiles 'Interpreter\Interpreter.exe') },
  [pscustomobject]@{ client = 'zcode'; path = (Join-Path $programFiles 'ZCode\ZCode.exe') },
  [pscustomobject]@{ client = 'zed'; path = (Join-Path $localAppData 'Programs\Zed\Zed.exe') },
  [pscustomobject]@{ client = 'opencode'; path = (Join-Path $env:APPDATA 'npm\node_modules\opencode-ai\bin\opencode.exe') }
) | ForEach-Object {
  [pscustomobject]@{ client = $_.client; path = (Get-CanonicalPath $_.path) }
}

$testMode = ($TestClientPid -gt 0) -or
  (-not [string]::IsNullOrWhiteSpace($TestCandidatePidsJson)) -or
  (-not [string]::IsNullOrWhiteSpace($TestProcessTableJson))
if ($testMode) {
  if ((($TestClientPid -le 0) -and [string]::IsNullOrWhiteSpace($TestCandidatePidsJson)) -or
      (($TestClientPid -gt 0) -and -not [string]::IsNullOrWhiteSpace($TestCandidatePidsJson)) -or
      [string]::IsNullOrWhiteSpace($TestProcessTableJson) -or
      $env:AGENTCORE_BUILDER_CALLER_TEST_MODE -ne '1') {
    Write-ResolutionFailure 'invalid_test_mode'
  }
  try {
    $testProcesses = @($TestProcessTableJson | ConvertFrom-Json -Depth 10)
  } catch {
    Write-ResolutionFailure 'invalid_test_process_table'
  }
  if (-not [string]::IsNullOrWhiteSpace($TestCandidatePidsJson)) {
    try {
      $candidatePids = @($TestCandidatePidsJson | ConvertFrom-Json -Depth 5) | ForEach-Object { [int]$_ } | Sort-Object -Unique
    } catch {
      Write-ResolutionFailure 'invalid_test_candidate_pids'
    }
    if ($candidatePids.Count -ne 1 -or $candidatePids[0] -le 4) {
      Write-ResolutionFailure 'tcp_owner_not_unique'
    }
    $clientPid = [int]$candidatePids[0]
  } else {
    $clientPid = $TestClientPid
  }
  $processLookup = {
    param([int]$ProcessId)
    return $testProcesses | Where-Object { [int]$_.ProcessId -eq $ProcessId } | Select-Object -First 1
  }
} else {
  $netstat = Join-Path $env:SystemRoot 'System32\netstat.exe'
  if (-not (Test-Path -LiteralPath $netstat -PathType Leaf)) {
    Write-ResolutionFailure 'netstat_unavailable'
  }
  try {
    $candidatePids = @(
      & $netstat -ano -p tcp 2>$null | ForEach-Object {
        if ($_ -match '^\s*TCP\s+127\.0\.0\.1:(\d+)\s+127\.0\.0\.1:(\d+)\s+ESTABLISHED\s+(\d+)\s*$') {
          if (([int]$Matches[1] -eq $ClientPort) -and ([int]$Matches[2] -eq $ServerPort)) {
            [int]$Matches[3]
          }
        }
      } | Sort-Object -Unique
    )
  } catch {
    Write-ResolutionFailure 'tcp_owner_lookup_failed'
  }
  if ($candidatePids.Count -ne 1 -or $candidatePids[0] -le 4) {
    Write-ResolutionFailure 'tcp_owner_not_unique'
  }
  $clientPid = [int]$candidatePids[0]
  $processLookup = {
    param([int]$ProcessId)
    # Keep the CimInstance in a local. A bare Get-CimInstance in this scriptblock
    # is discarded by the call operator while ErrorActionPreference is Stop, and
    # every live caller then fails as process_unavailable before the walk starts.
    $found = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue |
      Select-Object -First 1
    return $found
  }
}

$seen = [System.Collections.Generic.HashSet[int]]::new()
$currentPid = $clientPid
for ($depth = 0; $depth -lt 32; $depth++) {
  if ($currentPid -le 0 -or -not $seen.Add($currentPid)) {
    Write-ResolutionFailure 'invalid_process_ancestry'
  }
  $process = & $processLookup $currentPid
  if ($null -eq $process) {
    Write-ResolutionFailure 'process_unavailable'
  }
  $executablePath = Get-CanonicalPath ([string]$process.ExecutablePath)
  if ([string]::IsNullOrWhiteSpace($executablePath)) {
    # An ancestor can have no image path. Keep walking. Admission still requires
    # an exact trusted path later in the chain. Pid 0 and 4 are the OS root.
    $currentPid = [int]$process.ParentProcessId
    if ($currentPid -le 4) { break }
    continue
  }
  $match = $trustedExecutables | Where-Object {
    [string]::Equals($_.path, $executablePath, [StringComparison]::OrdinalIgnoreCase)
  } | Select-Object -First 1
  if ($null -ne $match) {
    [pscustomobject]@{
      allowed = $true
      client = $match.client
      client_pid = $clientPid
      matched_pid = $currentPid
    } | ConvertTo-Json -Compress
    exit 0
  }
  $currentPid = [int]$process.ParentProcessId
  if ($currentPid -le 4) { break }
}

Write-ResolutionFailure 'untrusted_process_ancestry'
