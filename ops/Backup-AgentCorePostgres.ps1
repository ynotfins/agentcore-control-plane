param(
  [string]$EngineRoot = "F:\AgentCore\postgres_runtime_engine\pgsql",
  [string]$BackupRoot = "E:\AgentCoreArchive\backups_cold\pgvector\base",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55432,
  [string]$Database = "agent_core",
  [string]$User = "agent_admin"
)

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
