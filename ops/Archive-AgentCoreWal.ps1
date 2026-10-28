param(
  [Parameter(Mandatory = $true)]
  [string]$SourcePath,

  [Parameter(Mandatory = $true)]
  [string]$WalFileName,

  [string]$ArchiveRoot = "E:\AgentCoreArchive\agentcore-memory\wal\pg18",
  [string]$SecondaryArchiveRoot = "G:\AgentCoreArchive\agentcore-memory\wal\pg18",
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

function Copy-WalUnique {
  param([string]$DestinationRoot)
  if ([string]::IsNullOrWhiteSpace($DestinationRoot)) { return }
  $drive = [System.IO.Path]::GetPathRoot($DestinationRoot)
  if (-not (Test-Path -LiteralPath $drive -ErrorAction SilentlyContinue)) {
    throw "Archive destination drive not available: $drive"
  }
  New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
  $target = Join-Path $DestinationRoot $WalFileName
  if (Test-Path -LiteralPath $target) {
    $sourceHash = (Get-FileHash -LiteralPath $SourcePath -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($sourceHash -eq $targetHash) {
      return
    }
    throw "WAL archive collision with different hash: $target"
  }
  Copy-Item -LiteralPath $SourcePath -Destination $target
}

function Copy-WalSecondary {
  param([string]$DestinationRoot)
  if ([string]::IsNullOrWhiteSpace($DestinationRoot)) { return }
  try {
    $drive = [System.IO.Path]::GetPathRoot($DestinationRoot)
    if (-not (Test-Path -LiteralPath $drive -ErrorAction SilentlyContinue)) {
      Write-ArchiveLog -Level "warn" -Message "secondary archive drive not available, skipping: $DestinationRoot"
      return
    }
    $letter = $drive.Substring(0, 1)
    $psdrive = Get-PSDrive -Name $letter -ErrorAction SilentlyContinue
    if ($psdrive) {
      $total = [int64]$psdrive.Used + [int64]$psdrive.Free
      $usedPercent = if ($total -gt 0) { (100.0 * [int64]$psdrive.Used / $total) } else { 100 }
      if ($usedPercent -ge 75 -or [int64]$psdrive.Free -lt 8GB) {
        Write-ArchiveLog -Level "warn" -Message "secondary archive headroom exceeded (used=$([math]::Round($usedPercent,1))% free=$([int64]$psdrive.Free)), skipping"
        return
      }
    }
    Copy-WalUnique -DestinationRoot $DestinationRoot
  } catch {
    Write-ArchiveLog -Level "warn" -Message "secondary archive skipped: $($_.Exception.Message)"
  }
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
  Copy-WalUnique -DestinationRoot $ArchiveRoot
  Copy-WalSecondary -DestinationRoot $SecondaryArchiveRoot
  Invoke-Retention -DestinationRoot $ArchiveRoot
  Invoke-Retention -DestinationRoot $SecondaryArchiveRoot
  Write-ArchiveLog -Level "info" -Message "archived to primary root; secondary copy is best-effort"
  exit 0
} catch {
  Write-ArchiveLog -Level "error" -Message $_.Exception.Message
  exit 1
}
