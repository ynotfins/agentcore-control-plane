param(
  [string]$EngineRoot = "F:\AgentCore\postgres_runtime_engine\pgsql",
  [string]$BackupRoot = "",   # auto-resolved below: E: preferred, G: fallback
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55432,
  [string]$Database = "agent_core",
  [string]$User = "agent_admin"
)

# Resolve backup root: E:\AgentCoreArchive preferred (archive USB); G:\AgentCoreArchive fallback.
# E: is the designated archive/WAL drive (PROJECT_ANCHOR §2). When E: is unmounted, write to G:
# (backup-target drive) so nightly backups do not fail silently. Reconnect E: to restore canonical path.
if ([string]::IsNullOrEmpty($BackupRoot)) {
  if (Test-Path "E:\") {
    $BackupRoot = "E:\AgentCoreArchive\backups_cold\pgvector\base"
  } else {
    Write-Warning "E: (archive USB) is not mounted. Falling back to G:\AgentCoreArchive\backups_cold\pgvector\base. Reconnect E: to restore canonical backup path."
    $BackupRoot = "G:\AgentCoreArchive\backups_cold\pgvector\base"
  }
}

$ErrorActionPreference = "Stop"

if (-not $env:PGPASSWORD) {
  $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_ADMIN_PASSWORD", "User")
}
if (-not $env:PGSSLMODE) {
  $env:PGSSLMODE = "require"
}

$pgDump = Join-Path $EngineRoot "bin\pg_dump.exe"
$pgRestore = Join-Path $EngineRoot "bin\pg_restore.exe"
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $BackupRoot "agent_core-$stamp.dump"
$manifestPath = Join-Path $BackupRoot "agent_core-$stamp.json"

& $pgDump -h $HostName -p $Port -U $User -d $Database -Fc -f $backupPath
if ($LASTEXITCODE -ne 0) {
  throw "pg_dump failed with exit code $LASTEXITCODE"
}

$listOutput = & $pgRestore --list $backupPath
if ($LASTEXITCODE -ne 0) {
  throw "pg_restore --list failed with exit code $LASTEXITCODE"
}

$manifest = [pscustomobject]@{
  ok = $true
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  backup_path = $backupPath
  backup_bytes = (Get-Item -LiteralPath $backupPath).Length
  database = "$HostName`:$Port/$Database"
  user = $User
  restore_list_entries = @($listOutput).Count
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$manifest | ConvertTo-Json -Depth 5
