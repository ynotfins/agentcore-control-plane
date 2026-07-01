param(
  [Parameter(Mandatory = $true)]
  [string]$SourcePath,

  [Parameter(Mandatory = $true)]
  [string]$WalFileName,

  [string]$ArchiveRoot = ""   # auto-resolved below: E: preferred, G: fallback
)

# Resolve archive root: E:\AgentCoreArchive preferred (archive USB); G:\AgentCoreArchive fallback.
# When E: is unmounted WAL files accumulate in pg_wal and risk filling the F: runtime drive.
# G: (backup-target drive) is an acceptable interim WAL sink. Reconnect E: to restore canonical path.
if ([string]::IsNullOrEmpty($ArchiveRoot)) {
  if (Test-Path "E:\") {
    $ArchiveRoot = "E:\AgentCoreArchive\backups_cold\pgvector\wal"
  } else {
    $ArchiveRoot = "G:\AgentCoreArchive\backups_cold\pgvector\wal"
  }
}

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Path $ArchiveRoot -Force | Out-Null
$target = Join-Path $ArchiveRoot $WalFileName

if (Test-Path -LiteralPath $target) {
  exit 0
}

Copy-Item -LiteralPath $SourcePath -Destination $target -Force
exit 0
