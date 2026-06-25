param(
  [string]$EngineRoot = "F:\AgentCore\postgres_runtime_engine\pgsql",
  [string]$Root = "D:\MCP-Control-Plane",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 55432,
  [string]$Database = "agent_core",
  [string]$User = "agent_admin"
)

$ErrorActionPreference = "Stop"

if (-not $env:PGPASSWORD) {
  if ($User -eq "agent_admin") {
    $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_ADMIN_PASSWORD", "User")
  } else {
    $env:PGPASSWORD = [Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_INGEST_PASSWORD", "User")
  }
}
if (-not $env:PGSSLMODE) {
  $env:PGSSLMODE = "require"
}

$psql = Join-Path $EngineRoot "bin\psql.exe"
$files = @(
  "AGENT_DATABASE_BOOTSTRAP.md",
  "contracts\global-memory-database-contract.json",
  "docs\AGENTCORE_STORAGE_DESIGN.md",
  "docs\MCP_SERVER_CONFIGURATION_REFERENCE.md",
  "docs\DRIVE_WRITE_BOUNDARY_RULE.md"
)

$facts = @()
foreach ($rel in $files) {
  $path = Join-Path $Root $rel
  if (-not (Test-Path -LiteralPath $path)) { continue }
  $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
  $facts += [pscustomobject]@{
    fact_key = "file_hash:$rel"
    fact_value = @{ path = $path; sha256 = $hash; checked_at = (Get-Date).ToUniversalTime().ToString("o") }
  }
}

$projectKey = "mcp-control-plane"
$projectName = "MCP Control Plane"
$rootJson = (@{ root = $Root } | ConvertTo-Json -Compress).Replace("'", "''")
& $psql -h $HostName -p $Port -U $User -d $Database -v ON_ERROR_STOP=1 -c "INSERT INTO projects(project_key, display_name, root_path, metadata) VALUES ('$projectKey', '$projectName', '$Root', '$rootJson'::jsonb) ON CONFLICT (project_key) DO NOTHING;"
if ($LASTEXITCODE -ne 0) { throw "project upsert failed" }

$changed = 0
foreach ($fact in $facts) {
  $key = $fact.fact_key.Replace("'", "''")
  $value = ($fact.fact_value | ConvertTo-Json -Compress).Replace("'", "''")
  $sql = @"
WITH p AS (
  SELECT id FROM projects WHERE project_key = '$projectKey'
), current_fact AS (
  SELECT pf.*
  FROM project_facts pf, p
  WHERE pf.project_id = p.id AND pf.fact_key = '$key' AND pf.is_current = true
  ORDER BY pf.version DESC
  LIMIT 1
), inserted AS (
  INSERT INTO project_facts(project_id, fact_key, fact_value, version, supersedes_fact_id, source, is_current)
  SELECT
    p.id,
    '$key',
    '$value'::jsonb,
    COALESCE((SELECT version + 1 FROM current_fact), 1),
    (SELECT id FROM current_fact),
    'Test-AgentCoreDrift.ps1',
    true
  FROM p
  WHERE NOT EXISTS (SELECT 1 FROM current_fact WHERE fact_value = '$value'::jsonb)
  RETURNING id
)
UPDATE project_facts
SET is_current = false
WHERE id IN (SELECT supersedes_fact_id FROM inserted WHERE supersedes_fact_id IS NOT NULL);
"@
  & $psql -h $HostName -p $Port -U $User -d $Database -v ON_ERROR_STOP=1 -c $sql | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "fact drift check failed for $key" }
}

[pscustomobject]@{
  ok = $true
  checked_files = $facts.Count
  completed_at = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json -Depth 5
