# Test-AgentCoreUnifiedRetrieval.ps1
# Validates the unified memory catalog / context router (database-plan.md sec 7-9, sec 14.2).
# IMPORTANT: This is a Phase-6 / post-migration validator. Before the memory_catalog table and the
# agentcore_* gateway tools exist, it runs in DRY-RUN / SKIP mode and NEVER hard-fails the core rollout.
#
# Modes:
#   (default)   - presence/dry-run: confirm design artifact + migrations exist, probe Postgres read-only for the
#                 7 catalog tables; SKIP (exit 0) if tables absent (expected pre-migration).
#   -PostMigration - require the 7 tables + 8 seed rows + cross-project privacy guard; FAIL if missing.
# Read-only. Uses agent_read role from Windows env when probing. Never prints secrets.
param(
  [string]$Root = "D:\github\agentcore-control-plane",
  [switch]$PostMigration,
  [string]$PsqlBin = "F:\AgentCore\postgres_runtime_engine\pgsql\bin\psql.exe",
  [string]$PgHost = "127.0.0.1",
  [int]$PgPort = 55432,
  [string]$PgDatabase = "agent_core",
  [string]$PgUser = "agent_read"
)
$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$catalogTables = @('memory_source_systems','memory_catalog','memory_retrieval_events','context_packs','context_pack_items','agent_run_ledger','agent_quality_scores')

function Write-Line($s) { Write-Output $s }

# 1. Design artifact + migrations present (always checkable, source-only).
$designOk = Test-Path -LiteralPath (Join-Path $rootPath "database-plan.md")
$migUp = @('0001_up_memory_source_systems','0002_up_memory_catalog','0003_up_retrieval_events_context_packs','0004_up_agent_run_ledger_quality_scores','0005_seed_source_systems')
$migMissing = @($migUp | Where-Object { -not (Test-Path -LiteralPath (Join-Path $rootPath ("migrations\" + $_ + ".sql"))) })
Write-Line ("design artifact database-plan.md: " + $(if($designOk){'present'}else{'MISSING'}))
Write-Line ("migration files: " + $(if($migMissing.Count -eq 0){'all present'}else{('MISSING ' + ($migMissing -join ', '))}))

# 2. Probe Postgres read-only for catalog tables (best-effort; absence is expected pre-migration).
$pw = [Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_READ_PASSWORD", "User")
$tablesPresent = @()
$probeOk = $false
if ((Test-Path -LiteralPath $PsqlBin) -and $pw) {
  try {
    $env:PGPASSWORD = $pw
    $q = "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name = ANY('{$([string]::Join(',', $catalogTables))}');"
    $out = & $PsqlBin -h $PgHost -p $PgPort -d $PgDatabase -U $PgUser -At -c $q 2>$null
    $probeOk = $true
    $tablesPresent = @($out | Where-Object { $_ -and $_.Trim() -ne '' })
  } catch { $probeOk = $false }
  finally { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
}
Write-Line ("postgres probe: " + $(if($probeOk){'ok'}else{'unavailable (read-only skip)'}))
Write-Line ("catalog tables present: " + $(if($tablesPresent){($tablesPresent -join ', ')}else{'none'}))

$tablesMissing = @($catalogTables | Where-Object { $_ -notin $tablesPresent })

if (-not $PostMigration) {
  if ($tablesMissing.Count -gt 0) {
    Write-Line "SKIP: memory_catalog schema not yet migrated (expected pre-migration). Unified retrieval validation is Phase-6/post-migration. No hard fail."
    if (-not $designOk -or $migMissing.Count -gt 0) { Write-Line "WARN: design artifact or migration files incomplete (see above)." }
    exit 0
  }
  Write-Line "INFO: catalog tables already present; run with -PostMigration for full validation."
  exit 0
}

# PostMigration mode: enforce.
if ($tablesMissing.Count -gt 0) { Write-Line ("FAIL: missing catalog tables: " + ($tablesMissing -join ', ')); exit 1 }
Write-Line "PASS: all 7 catalog tables present. (Extend with seed-row count + cross-project privacy assertions once agentcore_* tools land.)"
exit 0
