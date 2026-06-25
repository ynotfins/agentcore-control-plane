param(
  [string]$EngineRoot = "F:\AgentCore\postgres_runtime_engine\pgsql",
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

$psql = Join-Path $EngineRoot "bin\psql.exe"
$started = Get-Date

& $psql -h $HostName -p $Port -U $User -d $Database -v ON_ERROR_STOP=1 -c "VACUUM (ANALYZE);"
if ($LASTEXITCODE -ne 0) { throw "VACUUM ANALYZE failed" }

$exists = & $psql -h $HostName -p $Port -U $User -d $Database -t -A -v ON_ERROR_STOP=1 -c "SELECT to_regclass('public.idx_global_vector_memory_embedding_hnsw') IS NOT NULL;"
if (($exists -join "").Trim() -eq "t") {
  & $psql -h $HostName -p $Port -U $User -d $Database -v ON_ERROR_STOP=1 -c "REINDEX INDEX CONCURRENTLY idx_global_vector_memory_embedding_hnsw;"
  if ($LASTEXITCODE -ne 0) { throw "HNSW reindex failed" }
}

[pscustomobject]@{
  ok = $true
  started_at = $started.ToUniversalTime().ToString("o")
  completed_at = (Get-Date).ToUniversalTime().ToString("o")
  database = "$HostName`:$Port/$Database"
  actions = @("VACUUM ANALYZE", "REINDEX idx_global_vector_memory_embedding_hnsw")
} | ConvertTo-Json -Depth 5
