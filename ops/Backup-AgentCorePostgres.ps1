param(
  [string]$PgRoot = "F:\PostgreSQL18",
  [string]$DataDir = "F:\PostgreSQL18\data",
  [string]$PrimaryRoot = "E:\AgentCoreArchive\agentcore-memory\backups\pg18",
  [string]$SecondaryRoot = "G:\AgentCoreArchive\agentcore-memory\backups\pg18",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55433,
  [string[]]$Databases = @("agent_core", "cognee_core"),
  [string]$AdminUser = "postgres",
  [string]$RepoRoot = "D:\github\agentcore-control-plane",
  [string]$BifrostRuntimeConfig = "H:\AgentRuntime\bifrost\config.json",
  [switch]$SkipBaseBackup
)

$ErrorActionPreference = "Stop"
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-NativeChecked {
  param(
    [string]$Command,
    [string[]]$Arguments,
    [string]$FailureMessage
  )
  $output = & $Command @Arguments 2>&1
  $code = $LASTEXITCODE
  if ($code -ne 0) {
    throw "$FailureMessage (exit $code): $($output -join "`n")"
  }
  return @($output | ForEach-Object { [string]$_ })
}

function Copy-IfPresent {
  param([string]$Source, [string]$DestinationRoot)
  if (-not (Test-Path -LiteralPath $Source)) { return }
  $leaf = Split-Path -Leaf $Source
  $destination = Join-Path $DestinationRoot $leaf
  Copy-Item -LiteralPath $Source -Destination $destination -Force
}

function ConvertTo-RedactedJsonValue {
  param([object]$Value, [string]$Key = "")
  if ($null -eq $Value) { return $null }
  if ($Key -match "(?i)(password|secret|token|key|authorization|credential)") {
    return "<redacted>"
  }
  if ($Value -is [pscustomobject]) {
    $result = [ordered]@{}
    foreach ($property in $Value.PSObject.Properties) {
      $result[$property.Name] = ConvertTo-RedactedJsonValue -Value $property.Value -Key $property.Name
    }
    return $result
  }
  if ($Value -is [System.Collections.IDictionary]) {
    $result = [ordered]@{}
    foreach ($itemKey in $Value.Keys) {
      $result[$itemKey] = ConvertTo-RedactedJsonValue -Value $Value[$itemKey] -Key ([string]$itemKey)
    }
    return $result
  }
  if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
    return @($Value | ForEach-Object { ConvertTo-RedactedJsonValue -Value $_ })
  }
  return $Value
}

function Write-SanitizedRuntimeConfig {
  param([string]$Source, [string]$Destination)
  if (-not (Test-Path -LiteralPath $Source)) { return $false }
  $parsed = Get-Content -LiteralPath $Source -Raw | ConvertFrom-Json
  $redacted = ConvertTo-RedactedJsonValue -Value $parsed
  $redacted | ConvertTo-Json -Depth 32 | Set-Content -LiteralPath $Destination -Encoding utf8
  return $true
}

function Get-RelativePathSafe {
  param([string]$Root, [string]$Path)
  $rootPath = (Resolve-Path -LiteralPath $Root).Path.TrimEnd("\") + "\"
  $targetPath = (Resolve-Path -LiteralPath $Path).Path
  $rootUri = [Uri]::new($rootPath)
  $targetUri = [Uri]::new($targetPath)
  return [Uri]::UnescapeDataString($rootUri.MakeRelativeUri($targetUri).ToString()).Replace("/", "\")
}

$pgBin = Join-Path $PgRoot "bin"
$psql = Join-Path $pgBin "psql.exe"
$pgDump = Join-Path $pgBin "pg_dump.exe"
$pgDumpAll = Join-Path $pgBin "pg_dumpall.exe"
$pgRestore = Join-Path $pgBin "pg_restore.exe"
$pgBaseBackup = Join-Path $pgBin "pg_basebackup.exe"

foreach ($required in @($psql, $pgDump, $pgDumpAll, $pgRestore)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "Required PostgreSQL executable missing: $required" }
}
if (-not $SkipBaseBackup -and -not (Test-Path -LiteralPath $pgBaseBackup)) {
  throw "Required PostgreSQL base-backup executable missing: $pgBaseBackup"
}

if (-not $env:PGPASSWORD) {
  $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "User")
}
if (-not $env:PGPASSWORD) { throw "AGENT_CORE_POSTGRES_PASSWORD is not available in Windows User env" }
if (-not $env:PGSSLMODE) { $env:PGSSLMODE = "require" }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$runRoot = Join-Path $PrimaryRoot $stamp
$logicalRoot = Join-Path $runRoot "logical"
$baseRoot = Join-Path $runRoot "base"
$sourceRoot = Join-Path $runRoot "source-config"
New-Item -ItemType Directory -Path $logicalRoot, $sourceRoot -Force | Out-Null

$pgReady = Invoke-NativeChecked -Command (Join-Path $pgBin "pg_isready.exe") -Arguments @("-h", $HostName, "-p", [string]$Port, "-d", "agent_core") -FailureMessage "pg_isready failed"

$globalsPath = Join-Path $logicalRoot "globals-no-role-passwords.sql"
Invoke-NativeChecked -Command $pgDumpAll -Arguments @("-h", $HostName, "-p", [string]$Port, "-U", $AdminUser, "--globals-only", "--no-role-passwords", "-f", $globalsPath) -FailureMessage "pg_dumpall globals failed" | Out-Null

$databaseManifests = @()
foreach ($database in $Databases) {
  $dumpPath = Join-Path $logicalRoot "$database.dump"
  Invoke-NativeChecked -Command $pgDump -Arguments @("-h", $HostName, "-p", [string]$Port, "-U", $AdminUser, "-d", $database, "-Fc", "-f", $dumpPath) -FailureMessage "pg_dump $database failed" | Out-Null
  $listOutput = Invoke-NativeChecked -Command $pgRestore -Arguments @("--list", $dumpPath) -FailureMessage "pg_restore --list $database failed"
  $databaseManifests += [pscustomobject]@{
    database = $database
    dump = Get-RelativePathSafe -Root $runRoot -Path $dumpPath
    restore_list_entries = @($listOutput).Count
  }
}

if (-not $SkipBaseBackup) {
  New-Item -ItemType Directory -Path $baseRoot -Force | Out-Null
  Invoke-NativeChecked -Command $pgBaseBackup -Arguments @("-h", $HostName, "-p", [string]$Port, "-U", $AdminUser, "-D", $baseRoot, "-Ft", "-X", "stream", "-c", "fast") -FailureMessage "pg_basebackup failed" | Out-Null
}

$inventorySql = @"
SELECT jsonb_build_object(
  'generated_at', now(),
  'databases', (SELECT jsonb_agg(datname ORDER BY datname) FROM pg_database WHERE datname = ANY(ARRAY['agent_core','cognee_core'])),
  'agentcore_roles', (SELECT jsonb_agg(rolname ORDER BY rolname) FROM pg_roles WHERE rolname LIKE 'agentcore_%'),
  'agent_core_extensions', (SELECT jsonb_agg(extname || '=' || extversion ORDER BY extname) FROM pg_extension),
  'schemas', (SELECT jsonb_agg(nspname ORDER BY nspname) FROM pg_namespace WHERE nspname IN ('agentcore','public'))
)::text;
"@
$inventoryJson = Invoke-NativeChecked -Command $psql -Arguments @("-h", $HostName, "-p", [string]$Port, "-U", $AdminUser, "-d", "agent_core", "-t", "-A", "-v", "ON_ERROR_STOP=1", "-c", $inventorySql) -FailureMessage "inventory query failed"
$inventoryPath = Join-Path $runRoot "pg18-inventory.json"
($inventoryJson -join "`n").Trim() | Set-Content -LiteralPath $inventoryPath -Encoding utf8

$rowCountsMap = [ordered]@{}
foreach ($tableName in @(
  "agentcore.evidence_events",
  "agentcore.context_summaries",
  "agentcore.projection_revisions",
  "agentcore.retrieval_documents",
  "agentcore.knowledge_promotions"
)) {
  $exists = Invoke-NativeChecked -Command $psql -Arguments @("-h", $HostName, "-p", [string]$Port, "-U", $AdminUser, "-d", "agent_core", "-t", "-A", "-v", "ON_ERROR_STOP=1", "-c", "SELECT to_regclass('$tableName') IS NOT NULL;") -FailureMessage "row-count existence query failed"
  if (($exists -join "").Trim() -eq "t") {
    $count = Invoke-NativeChecked -Command $psql -Arguments @("-h", $HostName, "-p", [string]$Port, "-U", $AdminUser, "-d", "agent_core", "-t", "-A", "-v", "ON_ERROR_STOP=1", "-c", "SELECT COUNT(*)::text FROM $tableName;") -FailureMessage "row-count query failed for $tableName"
    $rowCountsMap[$tableName] = [int64](($count -join "").Trim())
  } else {
    $rowCountsMap[$tableName] = $null
  }
}
$rowCountPath = Join-Path $runRoot "agent-core-row-counts.json"
$rowCountsMap | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $rowCountPath -Encoding utf8

$repoBackupRoot = Join-Path $sourceRoot "repo"
New-Item -ItemType Directory -Path $repoBackupRoot -Force | Out-Null
foreach ($relative in @(
  "scripts\agentcore_memory\server.py",
  "scripts\agentcore_memory\knowledge_memory.py",
  "contracts\bifrost-upstream-mcp-registry.json",
  "contracts\agentcore-gateway-client.json",
  "renderers\bifrost\config.sanitized.json",
  "scripts\memory_platform\Invoke-M3ProjectionWorker.ps1",
  "scripts\memory_platform\Test-M2CanonicalIdentity.ps1",
  "scripts\memory_platform\Test-M3LosslessContext.ps1",
  "scripts\memory_platform\Test-M4Gateway.ps1",
  "scripts\memory_platform\Test-M5HybridRetrieval.ps1"
)) {
  Copy-IfPresent -Source (Join-Path $RepoRoot $relative) -DestinationRoot $repoBackupRoot
}
$migrationBackupRoot = Join-Path $sourceRoot "migrations"
New-Item -ItemType Directory -Path $migrationBackupRoot -Force | Out-Null
foreach ($migrationDir in @("m2", "m3", "m4", "m5")) {
  $sourceDir = Join-Path (Join-Path $RepoRoot "migrations") $migrationDir
  if (Test-Path -LiteralPath $sourceDir) {
    Copy-Item -LiteralPath $sourceDir -Destination (Join-Path $migrationBackupRoot $migrationDir) -Recurse -Force
  }
}
$runtimeConfigCopied = Write-SanitizedRuntimeConfig -Source $BifrostRuntimeConfig -Destination (Join-Path $sourceRoot "bifrost-runtime-config.sanitized.json")

$files = @(Get-ChildItem -LiteralPath $runRoot -Recurse -File | Sort-Object FullName)
$hashes = @($files | ForEach-Object {
  $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
  [pscustomobject]@{
    path = Get-RelativePathSafe -Root $runRoot -Path $_.FullName
    bytes = $_.Length
    sha256 = $hash.Hash
  }
})
$hashPath = Join-Path $runRoot "sha256-manifest.json"
$hashes | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $hashPath -Encoding utf8

$manifest = [pscustomobject]@{
  ok = $true
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  backup_kind = "pg18-logical-base-source-config"
  pg_endpoint = "$HostName`:$Port"
  pg_root = $PgRoot
  data_dir = $DataDir
  primary_path = $runRoot
  secondary_path = $null
  databases = $databaseManifests
  globals = Get-RelativePathSafe -Root $runRoot -Path $globalsPath
  base_backup = if ($SkipBaseBackup) { $null } else { Get-RelativePathSafe -Root $runRoot -Path $baseRoot }
  source_config = Get-RelativePathSafe -Root $runRoot -Path $sourceRoot
  bifrost_runtime_config_sanitized = $runtimeConfigCopied
  pg_ready = $pgReady
  hash_manifest = "sha256-manifest.json"
}
$manifestPath = Join-Path $runRoot "backup-manifest.json"
$manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $manifestPath -Encoding utf8

if (Test-Path -LiteralPath (Split-Path -Qualifier $SecondaryRoot)) {
  New-Item -ItemType Directory -Path $SecondaryRoot -Force | Out-Null
  $secondaryRunRoot = Join-Path $SecondaryRoot $stamp
  Copy-Item -LiteralPath $runRoot -Destination $secondaryRunRoot -Recurse -Force
  $manifest.secondary_path = $secondaryRunRoot
  $manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $manifestPath -Encoding utf8
}

$manifest | ConvertTo-Json -Depth 12
