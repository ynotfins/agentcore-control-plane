param(
  [Parameter(Mandatory = $true)]
  [string]$SourcePath,

  [Parameter(Mandatory = $true)]
  [string]$WalFileName,

  [string]$ArchiveRoot = "E:\AgentCoreArchive\agentcore-memory\wal\pg18",
  [string]$SecondaryArchiveRoot = "G:\AgentCoreArchive\agentcore-memory\wal\pg18",
  [int]$RetentionDays = 30,
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

function Invoke-Retention {
  param([string]$DestinationRoot)
  if ($RetentionDays -le 0 -or -not (Test-Path -LiteralPath $DestinationRoot)) { return }
  $cutoff = (Get-Date).AddDays(-1 * $RetentionDays)
  Get-ChildItem -LiteralPath $DestinationRoot -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff -and $_.Name -match '^[0-9A-F]{24}(\.[0-9A-F]{8}\.backup)?$' } |
    Remove-Item -Force -ErrorAction Stop
}

try {
  if (-not (Test-Path -LiteralPath $SourcePath)) {
    throw "WAL source path missing: $SourcePath"
  }
  Copy-WalUnique -DestinationRoot $ArchiveRoot
  Copy-WalUnique -DestinationRoot $SecondaryArchiveRoot
  Invoke-Retention -DestinationRoot $ArchiveRoot
  Invoke-Retention -DestinationRoot $SecondaryArchiveRoot
  Write-ArchiveLog -Level "info" -Message "archived to primary and secondary roots"
  exit 0
} catch {
  Write-ArchiveLog -Level "error" -Message $_.Exception.Message
  exit 1
}
