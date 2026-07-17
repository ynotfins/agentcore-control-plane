param(
  [string]$PgRoot = "F:\PostgreSQL18",
  [string]$DataDir = "F:\PostgreSQL18\data",
  [string]$ServiceName = "AgentCore-PostgreSQL18",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55433,
  [string]$AdminUser = "postgres",
  [string]$ArchiveCommandScript = "D:\github\agentcore-control-plane\ops\Archive-AgentCoreWal.ps1",
  [string]$ArchiveRoot = "E:\AgentCoreArchive\agentcore-memory\wal\pg18",
  [string]$EvidenceDir = "audits\M5",
  [int]$ArchiveWaitSeconds = 30
)

$ErrorActionPreference = "Stop"
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-NativeChecked {
  param([string]$Command, [string[]]$Arguments, [string]$FailureMessage)
  $output = & $Command @Arguments 2>&1
  $code = $LASTEXITCODE
  if ($code -ne 0) { throw "$FailureMessage (exit $code): $($output -join "`n")" }
  return (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

function Invoke-PsqlValue {
  param([string]$Sql, [string]$Database = "postgres")
  return Invoke-NativeChecked -Command $psql -Arguments @("-h", $HostName, "-p", [string]$Port, "-U", $AdminUser, "-d", $Database, "-t", "-A", "-v", "ON_ERROR_STOP=1", "-c", $Sql) -FailureMessage "psql failed"
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$evidencePath = Join-Path $repoRoot $EvidenceDir
New-Item -ItemType Directory -Path $evidencePath -Force | Out-Null
New-Item -ItemType Directory -Path $ArchiveRoot -Force | Out-Null

$pgBin = Join-Path $PgRoot "bin"
$psql = Join-Path $pgBin "psql.exe"
$pgIsReady = Join-Path $pgBin "pg_isready.exe"
foreach ($required in @($psql, $pgIsReady, $ArchiveCommandScript)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "Required path missing: $required" }
}

if (-not $env:PGPASSWORD) {
  $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
}
if (-not $env:PGPASSWORD) { throw "AGENT_CORE_POSTGRES_PASSWORD is not available in Windows User env" }
if (-not $env:PGSSLMODE) { $env:PGSSLMODE = "require" }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$configBackupRoot = Join-Path "E:\AgentCoreArchive\agentcore-memory\config-backups\pg18-wal" $stamp
New-Item -ItemType Directory -Path $configBackupRoot -Force | Out-Null
foreach ($file in @("postgresql.conf", "postgresql.auto.conf", "pg_hba.conf")) {
  $path = Join-Path $DataDir $file
  if (Test-Path -LiteralPath $path) {
    Copy-Item -LiteralPath $path -Destination (Join-Path $configBackupRoot $file) -Force
  }
}

$pgHba = Join-Path $DataDir "pg_hba.conf"
$hbaText = Get-Content -LiteralPath $pgHba -Raw
$managedLine = "hostssl replication postgres 127.0.0.1/32 scram-sha-256"
if ($hbaText -notmatch [regex]::Escape($managedLine)) {
  Add-Content -LiteralPath $pgHba -Value @"

# AgentCore PG18 base-backup/PITR localhost replication (managed by Enable-AgentCorePg18Wal.ps1)
$managedLine
"@ -Encoding utf8
}

$archiveCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ArchiveCommandScript`" -SourcePath `"%p`" -WalFileName `"%f`" -ArchiveRoot `"$ArchiveRoot`""
$archiveCommandSql = $archiveCommand.Replace("'", "''")
Invoke-PsqlValue -Sql "ALTER SYSTEM SET wal_level = 'replica';" | Out-Null
Invoke-PsqlValue -Sql "ALTER SYSTEM SET archive_mode = 'on';" | Out-Null
Invoke-PsqlValue -Sql "ALTER SYSTEM SET archive_command = '$archiveCommandSql';" | Out-Null
Invoke-PsqlValue -Sql "ALTER SYSTEM SET archive_timeout = '300s';" | Out-Null
Invoke-PsqlValue -Sql "ALTER SYSTEM SET max_wal_senders = '5';" | Out-Null

Restart-Service -Name $ServiceName -Force -ErrorAction Stop
Invoke-NativeChecked -Command $pgIsReady -Arguments @("-h", $HostName, "-p", [string]$Port, "-d", "agent_core") -FailureMessage "pg_isready after restart failed" | Out-Null

$settings = [ordered]@{
  wal_level = Invoke-PsqlValue -Sql "SHOW wal_level;"
  archive_mode = Invoke-PsqlValue -Sql "SHOW archive_mode;"
  archive_command = Invoke-PsqlValue -Sql "SHOW archive_command;"
  archive_timeout = Invoke-PsqlValue -Sql "SHOW archive_timeout;"
  max_wal_senders = Invoke-PsqlValue -Sql "SHOW max_wal_senders;"
}

$switchedWal = Invoke-PsqlValue -Sql "SELECT pg_walfile_name(pg_switch_wal());"
$archivePath = Join-Path $ArchiveRoot $switchedWal
$deadline = (Get-Date).AddSeconds($ArchiveWaitSeconds)
while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $archivePath)) {
  Start-Sleep -Seconds 1
}
$archiveFound = Test-Path -LiteralPath $archivePath

$report = [pscustomobject]@{
  ok = ($settings.archive_mode -eq "on" -and $archiveFound)
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  service = $ServiceName
  endpoint = "$HostName`:$Port"
  config_backup_root = $configBackupRoot
  archive_root = $ArchiveRoot
  settings = $settings
  switched_wal = $switchedWal
  switched_wal_archived = $archiveFound
  archive_path = if ($archiveFound) { $archivePath } else { $null }
  active_pg_wal_root = (Join-Path $DataDir "pg_wal")
}
$reportPath = Join-Path $evidencePath "pg18-wal-enable-$stamp.json"
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding utf8
$report | ConvertTo-Json -Depth 10

if (-not $report.ok) { exit 1 }
