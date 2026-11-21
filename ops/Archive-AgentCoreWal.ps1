param(
  [Parameter(Mandatory = $true)]
  [string]$SourcePath,

  [Parameter(Mandatory = $true)]
  [string]$WalFileName,

  [string]$ArchiveRoot = "E:\AgentCoreArchive\agentcore-memory\wal\pg18",
  # Second copy (contracts/secondary-backup-drive-policy.json). Moved from removable G:
  # to internal I: (AgentCore_Staging) 2026-11-17 with Tony's approval.
  [string]$SecondaryArchiveRoot = "I:\AgentCoreArchive\agentcore-memory\wal\pg18",
  # Volume identity guard: the secondary copy is written only when the volume mounted at
  # the secondary root's drive letter has this volume GUID. Empty string disables the guard
  # (tests only).
  [string]$SecondaryVolumeGuid = "\\?\Volume{ac27f734-60e4-4783-a6ec-6e9f922ad9d1}\",
  [int]$SecondaryMaxUsedPercent = 75,
  [int]$SecondaryMinFreeGB = 8,
  # Disabled by default. WAL removal must be recovery-chain aware and is not
  # safe as an age-only operation.
  [int]$RetentionDays = 0,
  [string]$LogRoot = "E:\AgentCoreArchive\agentcore-memory\wal\pg18\logs"
)

$ErrorActionPreference = "Stop"

function Write-ArchiveLog {
  param([string]$Level, [string]$Message)
  try {
    New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
    $line = [pscustomobject]@{
      timestamp = (Get-Date).ToUniversalTime().ToString("o")
      level = $Level
      wal_file = $WalFileName
      message = $Message
    } | ConvertTo-Json -Compress
    Add-Content -LiteralPath (Join-Path $LogRoot "archive.log") -Value $line -Encoding utf8
  } catch {
    # PostgreSQL must receive the archive exit code; logging is best-effort only.
  }
}

function Get-VolumeGuidForRoot {
  param([string]$Root)
  try {
    $out = & mountvol.exe $Root /L 2>$null
    $guid = (@($out) -join "").Trim()
    if ($LASTEXITCODE -eq 0 -and $guid -like "\\?\Volume{*}\") { return $guid }
  } catch { }
  try {
    $letter = $Root.TrimEnd("\")
    $vol = Get-CimInstance -ClassName Win32_Volume -Filter "DriveLetter='$letter'" -ErrorAction Stop
    if ($vol -and $vol.DeviceID) { return [string]$vol.DeviceID }
  } catch { }
  return $null
}

function Test-SecondaryTarget {
  # Returns $null when the secondary copy may proceed, otherwise a skip reason.
  param([string]$DestinationRoot)
  $root = [System.IO.Path]::GetPathRoot($DestinationRoot)
  if (-not (Test-Path -LiteralPath $root -ErrorAction SilentlyContinue)) {
    return "secondary archive drive not available"
  }
  if (-not [string]::IsNullOrWhiteSpace($SecondaryVolumeGuid)) {
    $actual = Get-VolumeGuidForRoot -Root $root
    if (-not $actual) { return "secondary volume identity unreadable at $root" }
    if (-not [string]::Equals($actual, $SecondaryVolumeGuid, [System.StringComparison]::OrdinalIgnoreCase)) {
      return "secondary volume identity mismatch at $root (found $actual)"
    }
  }
  try {
    $info = [System.IO.DriveInfo]::new($root)
    if ($info.IsReady -and $info.TotalSize -gt 0) {
      $usedPercent = 100.0 * ($info.TotalSize - $info.AvailableFreeSpace) / $info.TotalSize
      if ($usedPercent -ge $SecondaryMaxUsedPercent) { return ("secondary drive used {0:N1}% >= {1}%" -f $usedPercent, $SecondaryMaxUsedPercent) }
      if ($info.AvailableFreeSpace -lt ([int64]$SecondaryMinFreeGB * 1GB)) { return "secondary drive free space below $SecondaryMinFreeGB GB" }
    }
  } catch { }
  return $null
}

function Copy-WalUnique {
  param([string]$DestinationRoot, [switch]$Optional)
  if ([string]::IsNullOrWhiteSpace($DestinationRoot)) { return $false }
  if ($Optional) {
    $skip = Test-SecondaryTarget -DestinationRoot $DestinationRoot
    if ($skip) {
      Write-ArchiveLog -Level "warn" -Message "$skip, skipping secondary copy: $DestinationRoot"
      return $false
    }
  } else {
    $drive = [System.IO.Path]::GetPathRoot($DestinationRoot)
    if (-not (Test-Path -LiteralPath $drive -ErrorAction SilentlyContinue)) {
      throw "Archive destination drive not available: $drive"
    }
  }
  New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
  $target = Join-Path $DestinationRoot $WalFileName
  if (Test-Path -LiteralPath $target) {
    $sourceHash = (Get-FileHash -LiteralPath $SourcePath -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($sourceHash -eq $targetHash) {
      return $true
    }
    throw "WAL archive collision with different hash: $target"
  }
  Copy-Item -LiteralPath $SourcePath -Destination $target
  return $true
}

function Invoke-Retention {
  param([string]$DestinationRoot)
  if ($RetentionDays -le 0 -or -not (Test-Path -LiteralPath $DestinationRoot)) { return }
  throw "Age-only WAL deletion is forbidden. Use an accepted recovery-chain-aware retention runner."
}

try {
  if (-not (Test-Path -LiteralPath $SourcePath)) {
    throw "WAL source path missing: $SourcePath"
  }
  [void](Copy-WalUnique -DestinationRoot $ArchiveRoot)
  Invoke-Retention -DestinationRoot $ArchiveRoot
} catch {
  Write-ArchiveLog -Level "error" -Message $_.Exception.Message
  exit 1
}

# The secondary copy is optional and must never fail archive_command
# (contracts/secondary-backup-drive-policy.json: wal_copy_must_not_fail_archive_command).
$secondaryCopied = $false
try {
  $secondaryCopied = [bool](Copy-WalUnique -DestinationRoot $SecondaryArchiveRoot -Optional)
} catch {
  Write-ArchiveLog -Level "warn" -Message ("secondary copy failed (archive still succeeded): " + $_.Exception.Message)
}
if ($secondaryCopied) {
  Write-ArchiveLog -Level "info" -Message "archived to primary and secondary roots"
} else {
  Write-ArchiveLog -Level "info" -Message "archived to primary root (secondary skipped)"
}
exit 0
