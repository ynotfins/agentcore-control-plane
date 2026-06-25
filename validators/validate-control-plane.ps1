param(
  [string]$Root = "D:\MCP-Control-Plane"
)

$ErrorActionPreference = "Stop"

function Add-Result {
  param(
    [System.Collections.Generic.List[object]]$Results,
    [string]$Name,
    [bool]$Passed,
    [string]$Detail
  )
  $Results.Add([pscustomobject]@{
    name = $Name
    passed = $Passed
    detail = $Detail
  }) | Out-Null
}

function Read-Json {
  param([string]$Path)
  return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Get-ServerContainer {
  param($Json)
  if ($Json.mcpServers) { return $Json.mcpServers }
  if ($Json.mcp -and $Json.mcp.servers) { return $Json.mcp.servers }
  return $null
}

$results = [System.Collections.Generic.List[object]]::new()
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$critical = @("global-memory-gateway", "arabold-docs", "artiforge", "sequential-thinking")
$managedRelative = @(
  "AGENTS.md",
  "SECURITY.md",
  "rules\global-mcp-routing.md",
  "rules\environment-and-secrets.md",
  "registry\tool-registry.json",
  "registry\tool-registry.schema.json",
  "supervisor\servers.json",
  "supervisor\servers.yaml",
  "renderers\cursor-global.mcp.json",
  "renderers\open-interpreter.config.fragment.json",
  "renderers\openclaw.openclaw.fragment.json",
  "renderers\minimax.mcp.json",
  "renderers\android-studio.mcp.json",
  "validators\validate-control-plane.ps1"
)

$requiredFiles = @(
  "AGENTS.md",
  "SECURITY.md",
  "rules\global-mcp-routing.md",
  "rules\environment-and-secrets.md",
  "registry\tool-registry.json",
  "registry\tool-registry.schema.json"
)
$missing = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $rootPath $_)) })
Add-Result $results "core governance files" ($missing.Count -eq 0) ("missing=" + (($missing -join ", ") -replace "^$", "none"))

$jsonFiles = @(
  "supervisor\servers.json",
  "registry\tool-registry.json",
  "registry\tool-registry.schema.json",
  "renderers\cursor-global.mcp.json",
  "renderers\open-interpreter.config.fragment.json",
  "renderers\openclaw.openclaw.fragment.json",
  "renderers\minimax.mcp.json",
  "renderers\android-studio.mcp.json"
)
$jsonErrors = [System.Collections.Generic.List[string]]::new()
foreach ($rel in $jsonFiles) {
  try { $null = Read-Json (Join-Path $rootPath $rel) }
  catch { $jsonErrors.Add("$rel`: $($_.Exception.Message)") | Out-Null }
}
Add-Result $results "json parse" ($jsonErrors.Count -eq 0) (($jsonErrors -join "; ") -replace "^$", "all json parsed")

$secretFindings = [System.Collections.Generic.List[string]]::new()
$secretPatterns = @(
  "sk-[A-Za-z0-9_-]{20,}",
  "gh[pousr]_[A-Za-z0-9_]{20,}",
  "xox[baprs]-[A-Za-z0-9-]{20,}",
  "AIza[0-9A-Za-z_-]{20,}",
  "Bearer\s+(?!\$\{)[A-Za-z0-9._~+/=-]{20,}",
  "pat=(?!\$\{)[A-Za-z0-9._~+/=-]{10,}"
)
$scanFiles = Get-ChildItem -LiteralPath $rootPath -Recurse -File |
  Where-Object {
    $_.FullName -notmatch "\\artifacts\\backups\\" -and
    $_.FullName -notmatch "\\__pycache__\\" -and
    $_.Extension -notin @(".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip")
  }
foreach ($file in $scanFiles) {
  $text = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction SilentlyContinue
  foreach ($pattern in $secretPatterns) {
    if ($text -match $pattern) {
      $secretFindings.Add($file.FullName.Substring($rootPath.Length + 1)) | Out-Null
      break
    }
  }
}
Add-Result $results "no hard-coded secrets" ($secretFindings.Count -eq 0) (($secretFindings | Sort-Object -Unique) -join ", " -replace "^$", "no secret-like literals found")

$allowedEnv = @(
  "ARTIFORGE_PAT",
  "OPENAI_API_KEY",
  "GITHUB_PERSONAL_ACCESS_TOKEN",
  "MEM0_API_KEY",
  "MEM0_DEFAULT_USER_ID",
  "COMPOSIO_API_KEY",
  "DISABLE_THOUGHT_LOGGING",
  "CURSOR_API_KEY",
  "CURSOR_API_URL",
  "OBSIDIAN_API_KEY",
  "OBSIDIAN_LOCAL_REST_API",
  "OBSIDIAN_BASE_URL",
  "OBSIDIAN_VERIFY_SSL",
  "MEMORY_GATEWAY_BACKEND",
  "AGENT_CORE_PGHOST",
  "AGENT_CORE_PGPORT",
  "AGENT_CORE_PGDATABASE",
  "AGENT_CORE_PGUSER",
  "AGENT_CORE_PGPASSWORD",
  "AGENT_CORE_AGENT_ADMIN_PASSWORD",
  "AGENT_CORE_AGENT_INGEST_PASSWORD",
  "AGENT_CORE_AGENT_READ_PASSWORD",
  "AGENT_CORE_POSTGRES_PASSWORD",
  "MEMORY_GATEWAY_EMBEDDING_PROVIDER",
  "OPENAI_EMBEDDING_MODEL",
  "MEMORY_GATEWAY_EMBEDDING_DIMENSIONS"
)
$envFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @("supervisor\servers.json", "registry\tool-registry.json", "renderers\cursor-global.mcp.json", "renderers\open-interpreter.config.fragment.json", "renderers\openclaw.openclaw.fragment.json", "renderers\minimax.mcp.json", "renderers\android-studio.mcp.json")) {
  $text = Get-Content -LiteralPath (Join-Path $rootPath $rel) -Raw
  foreach ($match in [regex]::Matches($text, "\$\{(?:env|ENV):([A-Z0-9_]+)\}")) {
    if ($allowedEnv -notcontains $match.Groups[1].Value) {
      $envFindings.Add("$rel -> $($match.Value)") | Out-Null
    }
  }
}
Add-Result $results "correct env references only" ($envFindings.Count -eq 0) (($envFindings -join "; ") -replace "^$", "all placeholder env vars are allowlisted")

$retiredFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @("supervisor\servers.json", "renderers\cursor-global.mcp.json", "renderers\open-interpreter.config.fragment.json", "renderers\openclaw.openclaw.fragment.json", "renderers\minimax.mcp.json")) {
  $json = Read-Json (Join-Path $rootPath $rel)
  if ($rel -eq "supervisor\servers.json" -and $json.servers.context7) {
    $retiredFindings.Add("$rel active context7 server") | Out-Null
  }
  if ($rel -ne "supervisor\servers.json") {
    $servers = Get-ServerContainer $json
    if ($servers -and $servers.context7) { $retiredFindings.Add("$rel emits context7") | Out-Null }
  }
}
Add-Result $results "Context7 retired from managed routing" ($retiredFindings.Count -eq 0) (($retiredFindings -join "; ") -replace "^$", "context7 is not active or emitted")

$namingFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @("supervisor\servers.json", "registry\tool-registry.json", "renderers\cursor-global.mcp.json", "renderers\open-interpreter.config.fragment.json", "renderers\openclaw.openclaw.fragment.json", "renderers\minimax.mcp.json")) {
  $text = Get-Content -LiteralPath (Join-Path $rootPath $rel) -Raw
  if ($text.Contains("artiforge__codebase_scanner")) { $namingFindings.Add($rel) | Out-Null }
}
Add-Result $results "correct Artiforge naming" ($namingFindings.Count -eq 0) (($namingFindings -join ", ") -replace "^$", "artiforge is the only current managed name")

$supervisor = Read-Json (Join-Path $rootPath "supervisor\servers.json")
$registry = Read-Json (Join-Path $rootPath "registry\tool-registry.json")
$composioRegistry = @($registry.tools | Where-Object { $_.id -eq "composio" })[0]
$composioOk = $supervisor.servers.composio.lifecycle -eq "quarantined" -and $composioRegistry.lifecycle -eq "quarantined"
foreach ($rel in @("renderers\cursor-global.mcp.json", "renderers\open-interpreter.config.fragment.json", "renderers\openclaw.openclaw.fragment.json", "renderers\minimax.mcp.json", "renderers\android-studio.mcp.json")) {
  $text = Get-Content -LiteralPath (Join-Path $rootPath $rel) -Raw
  if ($text.Contains('"composio"')) { $composioOk = $false }
}
Add-Result $results "Composio quarantined" $composioOk "supervisor and registry lifecycle are quarantined; renderers do not emit composio"

$gatewayRegistry = @($registry.tools | Where-Object { $_.id -eq "global-memory-gateway" })[0]
$rawMem0Registry = @($registry.tools | Where-Object { $_.id -eq "mem0_mcp_server" })[0]
$gatewayOk = $supervisor.servers."global-memory-gateway".criticality -eq "critical" -and $gatewayRegistry.lifecycle -eq "active" -and $rawMem0Registry.lifecycle -eq "quarantined"
Add-Result $results "global-memory-gateway primary" $gatewayOk "gateway is critical/active and raw Mem0 is quarantined"

$criticalMissing = @($critical | Where-Object { -not $supervisor.servers.$_ })
Add-Result $results "critical tool set" ($criticalMissing.Count -eq 0) ("missing=" + (($criticalMissing -join ", ") -replace "^$", "none"))

$docsPath = "C:\Users\ynotf\.cursor\vendor\arabold-docs-mcp\node_modules\@arabold\docs-mcp-server\dist\index.js"
$fabricPath = "C:\Users\ynotf\.cursor\vendor\context-fabric-mcp\node_modules\context-fabric\dist\index.js"
$installMissing = @()
if (-not (Test-Path -LiteralPath $docsPath)) { $installMissing += "arabold-docs entrypoint missing" }
if (-not (Test-Path -LiteralPath $fabricPath)) { $installMissing += "context-fabric entrypoint missing" }
Add-Result $results "vendored MCP installs" ($installMissing.Count -eq 0) (($installMissing -join "; ") -replace "^$", "arabold-docs and context-fabric entrypoints exist")

$readOnlyMissing = [System.Collections.Generic.List[string]]::new()
foreach ($rel in $managedRelative) {
  $path = Join-Path $rootPath $rel
  if (Test-Path -LiteralPath $path) {
    $item = Get-Item -LiteralPath $path
    if (-not $item.IsReadOnly) { $readOnlyMissing.Add($rel) | Out-Null }
  }
}
Add-Result $results "managed files re-locked" ($readOnlyMissing.Count -eq 0) (($readOnlyMissing -join ", ") -replace "^$", "all managed files are read-only")

$allPassed = -not ($results | Where-Object { -not $_.passed })
$report = [pscustomobject]@{
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  root = $rootPath
  passed = [bool]$allPassed
  results = $results
}

$artifactDir = Join-Path $rootPath "artifacts"
$docsDir = Join-Path $rootPath "docs"
New-Item -ItemType Directory -Force -Path $artifactDir, $docsDir | Out-Null
$jsonPath = Join-Path $artifactDir "repo-validation-report.json"
$mdPath = Join-Path $docsDir "repo-validation-report.md"
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding utf8

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("# Repo Validation Report") | Out-Null
$lines.Add("") | Out-Null
$lines.Add("Generated: $($report.generated_at)") | Out-Null
$lines.Add("Root: ``$rootPath``") | Out-Null
if ($allPassed) { $overall = "PASS" } else { $overall = "FAIL" }
$lines.Add("Overall: $overall") | Out-Null
$lines.Add("") | Out-Null
foreach ($result in $results) {
  if ($result.passed) { $status = "PASS" } else { $status = "FAIL" }
  $lines.Add("- $status - $($result.name): $($result.detail)") | Out-Null
}
$lines | Set-Content -LiteralPath $mdPath -Encoding utf8

if ($allPassed) {
  Write-Output "PASS: Repo validation succeeded. Report: $mdPath"
  exit 0
}

Write-Output "FAIL: Repo validation failed. Report: $mdPath"
exit 1
