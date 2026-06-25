param(
  [string]$EngineRoot = "F:\AgentCore\postgres_runtime_engine\pgsql",
  [string]$BackupRoot = "E:\AgentCoreArchive\backups_cold\pgvector\base",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55432,
  [string]$MaintenanceDb = "postgres",
  [string]$RestoreDb = "agent_core_restore_test",
  [string]$User = "agent_admin"
)

$ErrorActionPreference = "Stop"

if (-not $env:PGPASSWORD) {
  $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_ADMIN_PASSWORD", "User")
}
if (-not $env:PGSSLMODE) {
  $env:PGSSLMODE = "require"
}

$psql = Join-Path $EngineRoot "bin\psql.exe"
$pgRestore = Join-Path $EngineRoot "bin\pg_restore.exe"
$latest = Get-ChildItem -LiteralPath $BackupRoot -Filter "agent_core-*.dump" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) {
  throw "No backup dump found under $BackupRoot"
}

& $psql -h $HostName -p $Port -U $User -d $MaintenanceDb -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $RestoreDb WITH (FORCE);"
& $psql -h $HostName -p $Port -U $User -d $MaintenanceDb -v ON_ERROR_STOP=1 -c "CREATE DATABASE $RestoreDb;"
& $pgRestore -h $HostName -p $Port -U $User -d $RestoreDb --clean --if-exists $latest.FullName
if ($LASTEXITCODE -ne 0) {
  throw "pg_restore failed with exit code $LASTEXITCODE"
}

$check = & $psql -h $HostName -p $Port -U $User -d $RestoreDb -t -A -v ON_ERROR_STOP=1 -c "SELECT COUNT(*) FROM global_vector_memory_store;"
if ($LASTEXITCODE -ne 0) {
  throw "restore validation query failed"
}

& $psql -h $HostName -p $Port -U $User -d $MaintenanceDb -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $RestoreDb WITH (FORCE);"

[pscustomobject]@{
  ok = $true
  backup_path = $latest.FullName
  restored_database = $RestoreDb
  vector_rows = ($check -join "").Trim()
  validated_at = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json -Depth 5
