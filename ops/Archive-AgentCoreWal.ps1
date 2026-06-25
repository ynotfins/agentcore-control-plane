param(
  [Parameter(Mandatory = $true)]
  [string]$SourcePath,

  [Parameter(Mandatory = $true)]
  [string]$WalFileName,

  [string]$ArchiveRoot = "E:\AgentCoreArchive\backups_cold\pgvector\wal"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Path $ArchiveRoot -Force | Out-Null
$target = Join-Path $ArchiveRoot $WalFileName

if (Test-Path -LiteralPath $target) {
  exit 0
}

Copy-Item -LiteralPath $SourcePath -Destination $target -Force
exit 0
