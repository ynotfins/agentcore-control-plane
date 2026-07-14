param(
  [string]$Root = "D:\github\agentcore-control-plane",
  [switch]$WriteReport,
  [switch]$DryRun
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

function Get-ServerNames {
  param([string]$Path)
  $json = Read-Json $Path
  $container = Get-ServerContainer $json
  if (-not $container) { return @() }
  return @($container.PSObject.Properties.Name)
}

function Test-ManagedMcpSecrets {
  param([string]$Path)

  if (-not (Test-Path -LiteralPath $Path)) {
    return @("missing path=$Path")
  }
  $text = Get-Content -LiteralPath $Path -Raw
  $activeText = $text
  try {
    $json = $text | ConvertFrom-Json
    $container = Get-ServerContainer $json
    if ($container) {
      $activeText = ($container | ConvertTo-Json -Depth 20)
    }
  } catch {
    $activeText = $text
  }
  $findings = [System.Collections.Generic.List[string]]::new()
  $patterns = @(
    "sk-[A-Za-z0-9_-]{20,}",
    "gh[pousr]_[A-Za-z0-9_]{20,}",
    "AIza[0-9A-Za-z_-]{20,}",
    "Bearer\s+(?!\$\{env:|\$\{ENV:)[A-Za-z0-9._~+/=-]{20,}",
    "Token\s+(?!\$\{env:|\$\{ENV:)[A-Za-z0-9._~+/=-]{20,}",
    "pat=(?!\$\{env:|\$\{ENV:)[A-Za-z0-9._~+/=-]{10,}"
  )
  foreach ($pattern in $patterns) {
    if ($activeText -match $pattern) {
      $findings.Add("secret-like literal") | Out-Null
      break
    }
  }
  foreach ($retired in @("context7", "mcp.mem0.ai", "connect.composio.dev", "swarmrecall-api.onrender.com")) {
    if ($activeText -match [regex]::Escape($retired)) {
      $findings.Add("retired route: $retired") | Out-Null
    }
  }
  return @($findings | Sort-Object -Unique)
}

function Get-LiveCodexServers {
  try {
    $raw = & codex mcp list --json 2>$null
    if (-not $raw) { return @{ ok = $false; error = "codex mcp list returned no output"; names = @() } }
    $parsed = $raw | ConvertFrom-Json
    $names = @($parsed | Where-Object { $_.enabled } | ForEach-Object { $_.name } | Sort-Object -Unique)
    return @{ ok = $true; error = $null; names = $names }
  }
  catch {
    return @{ ok = $false; error = $_.Exception.Message; names = @() }
  }
}

function Get-AgentCoreListener {
  try {
    $line = @(netstat -ano -p tcp | Select-String '127\.0\.0\.1:55432\s+.*LISTENING\s+\d+$' | Select-Object -First 1)[0]
    if (-not $line) { return @{ ok = $false; detail = "no listener on 127.0.0.1:55432" } }
    $parts = ($line.ToString() -replace "\s+", " ").Trim().Split(" ")
    return @{ ok = $true; detail = ("listener pid=" + $parts[-1] + " endpoint=" + $parts[1]) }
  }
  catch {
    return @{ ok = $false; detail = $_.Exception.Message }
  }
}

$results = [System.Collections.Generic.List[object]]::new()
$rootPath = (Resolve-Path -LiteralPath $Root).Path
if ($DryRun) { $WriteReport = $false }
$critical = @("swarmrecall", "swarmvault", "arabold-docs", "artiforge", "sequential-thinking")
$managedRelative = @(
  "AGENTS.md",
  "SECURITY.md",
  ".cursor\rules\agentcore-env-policy.mdc",
  "rules\global-mcp-routing.md",
  "rules\environment-and-secrets.md",
  "docs\GLOBAL_AGENT_RULES.md",
  "docs\restart_after_env_changes.md",
  "registry\tool-registry.json",
  "registry\tool-registry.schema.json",
  "supervisor\servers.json",
  "supervisor\servers.yaml",
  "renderers\cursor-global.mcp.json",
  "renderers\open-interpreter.config.fragment.json",
  "renderers\openclaw.openclaw.fragment.json",
  "renderers\minimax.mcp.json",
  "renderers\android-studio.mcp.json",
  "renderers\antigravity.mcp_config.json",
  "ops\Test-AgentCoreEnvPolicy.ps1",
  "ops\Test-AgentCoreDepwireIntegration.ps1",
  "automations\env-policy-audit.md",
  "validators\validate-control-plane.ps1"
)

$requiredFiles = @(
  "AGENTS.md",
  "SECURITY.md",
  ".cursor\rules\agentcore-env-policy.mdc",
  "rules\global-mcp-routing.md",
  "rules\environment-and-secrets.md",
  "docs\GLOBAL_AGENT_RULES.md",
  "docs\restart_after_env_changes.md",
  "ops\Test-AgentCoreEnvPolicy.ps1",
  "ops\Test-AgentCoreDepwireIntegration.ps1",
  "contracts\master-mcp-server-config.json",
  "ops\Invoke-AgentCoreMemoryProjector.ps1",
  "ops\Test-AgentCoreMemoryProjection.ps1",
  "ops\Test-AgentCoreContextFabricReadiness.ps1",
  "ops\Repair-AgentCoreContextFabricState.ps1",
  "ops\Install-AgentCoreOperationalScheduledTasks.ps1",
  "ops\Invoke-AgentCoreSwarmVaultIngest.ps1",
  "automations\env-policy-audit.md",
  "registry\tool-registry.json",
  "registry\tool-registry.schema.json"
)
$missing = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $rootPath $_)) })
Add-Result $results "core governance files" ($missing.Count -eq 0) ("missing=" + (($missing -join ", ") -replace "^$", "none"))

$jsonFiles = @(
  "supervisor\servers.json",
  "contracts\master-mcp-server-config.json",
  "registry\tool-registry.json",
  "registry\tool-registry.schema.json",
  "renderers\cursor-global.mcp.json",
  "renderers\open-interpreter.config.fragment.json",
  "renderers\openclaw.openclaw.fragment.json",
  "renderers\minimax.mcp.json",
  "renderers\android-studio.mcp.json",
  "renderers\antigravity.mcp_config.json"
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
    $_.FullName -notmatch "\\backups\\" -and
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
  "DEPWIRE_NO_TELEMETRY",
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
foreach ($rel in @("supervisor\servers.json", "registry\tool-registry.json", "renderers\cursor-global.mcp.json", "renderers\open-interpreter.config.fragment.json", "renderers\openclaw.openclaw.fragment.json", "renderers\minimax.mcp.json", "renderers\android-studio.mcp.json", "renderers\antigravity.mcp_config.json")) {
  $text = Get-Content -LiteralPath (Join-Path $rootPath $rel) -Raw
  foreach ($match in [regex]::Matches($text, "\$\{(?:env|ENV):([A-Z0-9_]+)\}")) {
    if ($allowedEnv -notcontains $match.Groups[1].Value) {
      $envFindings.Add("$rel -> $($match.Value)") | Out-Null
    }
  }
}
Add-Result $results "correct env references only" ($envFindings.Count -eq 0) (($envFindings -join "; ") -replace "^$", "all placeholder env vars are allowlisted")

$retiredFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @("supervisor\servers.json", "renderers\cursor-global.mcp.json", "renderers\open-interpreter.config.fragment.json", "renderers\openclaw.openclaw.fragment.json", "renderers\minimax.mcp.json", "renderers\antigravity.mcp_config.json")) {
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

$serenaLauncherFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @("supervisor\servers.json", "renderers\cursor-global.mcp.json", "renderers\open-interpreter.config.fragment.json", "renderers\openclaw.openclaw.fragment.json", "renderers\minimax.mcp.json", "renderers\antigravity.mcp_config.json")) {
  $text = Get-Content -LiteralPath (Join-Path $rootPath $rel) -Raw
  if ($text.Contains("git+https://github.com/oraios/serena") -or ($text -match '"command"\s*:\s*"[^"]*uvx(?:\.exe)?"')) { $serenaLauncherFindings.Add($rel) | Out-Null }
}
Add-Result $results "Serena installed launcher enforced" ($serenaLauncherFindings.Count -eq 0) (($serenaLauncherFindings -join ", ") -replace "^$", "managed Serena launchers use installed serena.exe")

$depwireLauncher = "C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd"
$depwireFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @("renderers\cursor-global.mcp.json", "renderers\open-interpreter.config.fragment.json", "renderers\openclaw.openclaw.fragment.json", "renderers\minimax.mcp.json", "renderers\android-studio.mcp.json", "renderers\antigravity.mcp_config.json")) {
  $json = Read-Json (Join-Path $rootPath $rel)
  $server = (Get-ServerContainer $json).depwire
  if ($null -eq $server -or $server.command -ne $depwireLauncher -or (@($server.args) -join "|") -ne "mcp" -or $server.env.DEPWIRE_NO_TELEMETRY -ne "1") {
    $depwireFindings.Add($rel) | Out-Null
  }
}
$depwireSupervisor = $null
try { $depwireSupervisor = (Read-Json (Join-Path $rootPath "supervisor\servers.json")).servers.depwire } catch {}
if ($null -eq $depwireSupervisor -or $depwireSupervisor.launch_contract.command -ne $depwireLauncher -or $depwireSupervisor.env_expectations.DEPWIRE_NO_TELEMETRY -ne "1") {
  $depwireFindings.Add("supervisor\servers.json") | Out-Null
}
$depwireContract = $null
try { $depwireContract = (Read-Json (Join-Path $rootPath "contracts\master-mcp-server-config.json")).server_catalog.depwire } catch {}
if ($null -eq $depwireContract -or $depwireContract.mcp_requires_api_key -ne $false -or $depwireContract.pro_license_scope -ne "vscode_cursor_extension_only") {
  $depwireFindings.Add("contracts\master-mcp-server-config.json") | Out-Null
}
Add-Result $results "DepWire governed launcher and credential scope" ($depwireFindings.Count -eq 0) (($depwireFindings -join ", ") -replace "^$", "global depwire-cli launcher, telemetry-off env, and extension-only Pro license scope enforced")

$namingFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @("supervisor\servers.json", "registry\tool-registry.json", "renderers\cursor-global.mcp.json", "renderers\open-interpreter.config.fragment.json", "renderers\openclaw.openclaw.fragment.json", "renderers\minimax.mcp.json", "renderers\antigravity.mcp_config.json")) {
  $text = Get-Content -LiteralPath (Join-Path $rootPath $rel) -Raw
  if ($text.Contains("artiforge__codebase_scanner")) { $namingFindings.Add($rel) | Out-Null }
}
Add-Result $results "correct Artiforge naming" ($namingFindings.Count -eq 0) (($namingFindings -join ", ") -replace "^$", "artiforge is the only current managed name")

$supervisor = Read-Json (Join-Path $rootPath "supervisor\servers.json")
$registry = Read-Json (Join-Path $rootPath "registry\tool-registry.json")
$composioRegistry = @($registry.tools | Where-Object { $_.id -eq "composio" })[0]
$composioOk = $supervisor.servers.composio.lifecycle -eq "quarantined" -and $composioRegistry.lifecycle -eq "quarantined"
foreach ($rel in @("renderers\cursor-global.mcp.json", "renderers\open-interpreter.config.fragment.json", "renderers\openclaw.openclaw.fragment.json", "renderers\minimax.mcp.json", "renderers\android-studio.mcp.json", "renderers\antigravity.mcp_config.json")) {
  $text = Get-Content -LiteralPath (Join-Path $rootPath $rel) -Raw
  if ($text.Contains('"composio"')) { $composioOk = $false }
}
Add-Result $results "Composio quarantined" $composioOk "supervisor and registry lifecycle are quarantined; renderers do not emit composio"

$gatewayRegistry = @($registry.tools | Where-Object { $_.id -eq "global-memory-gateway" })[0]
$rawMem0Registry = @($registry.tools | Where-Object { $_.id -eq "mem0_mcp_server" })[0]
$nativeOk = $gatewayRegistry.lifecycle -eq "retired" -and $rawMem0Registry.lifecycle -eq "quarantined" -and $null -ne $supervisor.servers.swarmrecall -and $null -ne $supervisor.servers.swarmvault
Add-Result $results "native-first memory plane" $nativeOk "SwarmRecall+SwarmVault active, global-memory-gateway retired, raw Mem0 quarantined"

$criticalMissing = @($critical | Where-Object { -not $supervisor.servers.$_ })
Add-Result $results "critical tool set" ($criticalMissing.Count -eq 0) ("missing=" + (($criticalMissing -join ", ") -replace "^$", "none"))

$liveCodex = Get-LiveCodexServers
$codexExpected = @($critical + "serena" + "depwire" | Sort-Object -Unique)
if (-not $liveCodex.ok) {
  Add-Result $results "live Codex routing set" $false ("codex mcp list unavailable: " + $liveCodex.error)
  Add-Result $results "live Codex retired servers absent" $false ("codex mcp list unavailable: " + $liveCodex.error)
  Add-Result $results "live Codex server budget" $false ("codex mcp list unavailable: " + $liveCodex.error)
}
else {
  $codexMissing = @($codexExpected | Where-Object { $liveCodex.names -notcontains $_ })
  Add-Result $results "live Codex routing set" ($codexMissing.Count -eq 0) ("missing=" + (($codexMissing -join ", ") -replace "^$", "none") + "; active=" + ($liveCodex.names -join ", "))

  $retiredLiveCodex = @($liveCodex.names | Where-Object { $_ -in @("context7", "mem0_mcp_server", "artiforge__codebase_scanner", "thinking-patterns") })
  Add-Result $results "live Codex retired servers absent" ($retiredLiveCodex.Count -eq 0) (($retiredLiveCodex -join ", ") -replace "^$", "no retired Codex servers are active")

  $codexServerBudget = $liveCodex.names.Count -le 18
  Add-Result $results "live Codex server budget" $codexServerBudget ("count=" + $liveCodex.names.Count + " limit=18 (includes DepWire plus Codex-managed plugin MCP surfaces while preserving the 1M context window)")
}

$agentCoreListener = Get-AgentCoreListener
Add-Result $results "AgentCore PostgreSQL listener" $agentCoreListener.ok $agentCoreListener.detail

try {
  $postgresTask = Get-ScheduledTask -TaskPath "\AgentCore\" -TaskName "PostgresRuntime" -ErrorAction Stop
  $postgresTaskInfo = Get-ScheduledTaskInfo -TaskPath "\AgentCore\" -TaskName "PostgresRuntime" -ErrorAction Stop
  $postgresActionText = (($postgresTask.Actions | ForEach-Object { $_.Execute + " " + $_.Arguments }) -join " ")
  $postgresTaskOk = $postgresActionText -match "Start-AgentCorePostgres\.ps1" -and $postgresActionText -match "-StartIfStopped"
  Add-Result $results "Postgres startup ownership" $postgresTaskOk ("state=" + [string]$postgresTask.State + "; last_result=" + [string]$postgresTaskInfo.LastTaskResult + "; action=" + $postgresActionText)
}
catch {
  Add-Result $results "Postgres startup ownership" $false $_.Exception.Message
}

$expectedRendererServers = [ordered]@{
  "renderers\cursor-global.mcp.json" = @("arabold-docs", "artiforge", "context-fabric", "cursor-agent-mcp", "depwire", "filesystem", "mcp-debugger", "obsidian-vault", "playwright", "sequential-thinking", "serena", "swarmrecall", "swarmvault")
  "renderers\openclaw.openclaw.fragment.json" = @("arabold-docs", "artiforge", "depwire", "eye2byte", "filesystem", "obsidian-vault", "playwright", "sequential-thinking", "serena", "swarmrecall", "swarmvault")
  "renderers\open-interpreter.config.fragment.json" = @("arabold-docs", "artiforge", "depwire", "serena", "swarmrecall", "swarmvault")
  "renderers\minimax.mcp.json" = @("arabold-docs", "artiforge", "depwire", "filesystem", "obsidian-vault", "playwright", "sequential-thinking", "serena", "swarmrecall", "swarmvault")
  "renderers\antigravity.mcp_config.json" = @("arabold-docs", "artiforge", "depwire", "filesystem", "obsidian-vault", "playwright", "sequential-thinking", "serena", "swarmrecall", "swarmvault")
  "renderers\android-studio.mcp.json" = @("depwire")
}
$surfaceFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in $expectedRendererServers.Keys) {
  $actual = @(Get-ServerNames (Join-Path $rootPath $rel) | Sort-Object)
  $expected = @($expectedRendererServers[$rel] | Sort-Object)
  $missing = @($expected | Where-Object { $_ -notin $actual })
  $extra = @($actual | Where-Object { $_ -notin $expected })
  if ($missing.Count -gt 0 -or $extra.Count -gt 0) {
    $surfaceFindings.Add("$rel missing=[$($missing -join ", ")] extra=[$($extra -join ", ")] count=$($actual.Count)") | Out-Null
  } else {
    $surfaceFindings.Add("$rel count=$($actual.Count)") | Out-Null
  }
}
$surfaceMismatch = @($surfaceFindings | Where-Object { $_ -match "missing=\[|extra=\[" })
Add-Result $results "approved renderer server sets" ($surfaceMismatch.Count -eq 0) (($surfaceFindings -join "; ") -replace "^$", "all renderer server sets match the approved bounded surface")

$managedLiveConfigPaths = [ordered]@{
  "Cursor" = "C:\Users\ynotf\.cursor\mcp.json"
  "OpenClaw" = "C:\Users\ynotf\.openclaw\openclaw.json"
  "Open Interpreter" = "C:\Users\ynotf\AppData\Roaming\interpreter\config.json"
  "MiniMax Code" = "C:\Users\ynotf\.minimax\mcp\mcp.json"
  "MiniMax Code Legacy" = "C:\Users\ynotf\.mavis\mcp\mcp.json"
  "Antigravity" = "C:\Users\ynotf\.gemini\config\mcp_config.json"
  "Antigravity Roaming" = "C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json"
}
$liveConfigReadFindings = [System.Collections.Generic.List[string]]::new()
foreach ($clientName in $managedLiveConfigPaths.Keys) {
  $path = $managedLiveConfigPaths[$clientName]
  if (-not (Test-Path -LiteralPath $path)) {
    $liveConfigReadFindings.Add("$clientName missing path=$path") | Out-Null
    continue
  }
  try {
    $actual = @(Get-ServerNames $path | Sort-Object)
    $liveConfigReadFindings.Add("$clientName count=$($actual.Count)") | Out-Null
  }
  catch {
    $liveConfigReadFindings.Add("$clientName parse-error path=$path detail=$($_.Exception.Message)") | Out-Null
  }
}
$liveConfigReadIssues = @($liveConfigReadFindings | Where-Object { $_ -match "missing path=|parse-error" })
Add-Result $results "managed live client configs readable" ($liveConfigReadIssues.Count -eq 0) (($liveConfigReadFindings -join "; ") -replace "^$", "all managed live client configs are readable")

$gatewayArgFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @(
  "renderers\cursor-global.mcp.json",
  "renderers\open-interpreter.config.fragment.json",
  "renderers\openclaw.openclaw.fragment.json",
  "renderers\minimax.mcp.json",
  "renderers\antigravity.mcp_config.json"
)) {
  $text = Get-Content -LiteralPath (Join-Path $rootPath $rel) -Raw
  if ($text.Contains("global-memory-gateway")) {
    $gatewayArgFindings.Add("$rel still contains retired global-memory-gateway") | Out-Null
  }
}
Add-Result $results "global-memory-gateway retired from renderers" ($gatewayArgFindings.Count -eq 0) (($gatewayArgFindings -join "; ") -replace "^$", "no renderer emits the retired global-memory-gateway")

# Mandatory baseline: swarmrecall + swarmvault must be present (local-only) in every first-class managed renderer.
$swarmBaselineRenderers = @(
  "renderers\cursor-global.mcp.json",
  "renderers\open-interpreter.config.fragment.json",
  "renderers\openclaw.openclaw.fragment.json",
  "renderers\minimax.mcp.json",
  "renderers\antigravity.mcp_config.json"
)
$swarmBaselineFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in $swarmBaselineRenderers) {
  $names = @(Get-ServerNames (Join-Path $rootPath $rel))
  $missing = @(@("swarmrecall", "swarmvault") | Where-Object { $_ -notin $names })
  if ($missing.Count -gt 0) { $swarmBaselineFindings.Add("$rel missing=[$($missing -join ", ")]") | Out-Null }
}
Add-Result $results "swarmrecall + swarmvault baseline present" ($swarmBaselineFindings.Count -eq 0) (($swarmBaselineFindings -join "; ") -replace "^$", "swarmrecall and swarmvault are present in every first-class managed renderer")

# Hosted Swarm routes are forbidden everywhere (local-only posture).
$hostedSwarmFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @(
  "renderers\cursor-global.mcp.json",
  "renderers\open-interpreter.config.fragment.json",
  "renderers\openclaw.openclaw.fragment.json",
  "renderers\minimax.mcp.json",
  "renderers\android-studio.mcp.json",
  "renderers\antigravity.mcp_config.json",
  "supervisor\servers.json"
)) {
  $path = Join-Path $rootPath $rel
  if (-not (Test-Path -LiteralPath $path)) { continue }
  $text = Get-Content -LiteralPath $path -Raw
  if ($text -match 'onrender\.com' -or $text -match 'swarmrecall-api\.onrender' -or $text -match 'swarmvault.*\.onrender') {
    $hostedSwarmFindings.Add($rel) | Out-Null
  }
}
Add-Result $results "no hosted Swarm routes" ($hostedSwarmFindings.Count -eq 0) (($hostedSwarmFindings -join ", ") -replace "^$", "no hosted SwarmRecall/SwarmVault URLs in renderers or supervisor")

# Forbidden runtime port :65432 must not appear in source-controlled MCP config/contracts (archived evidence excepted).
$portFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @(
  "supervisor\servers.json",
  "supervisor\servers.yaml",
  "contracts\master-mcp-server-config.json",
  "renderers\cursor-global.mcp.json",
  "renderers\open-interpreter.config.fragment.json",
  "renderers\openclaw.openclaw.fragment.json",
  "renderers\minimax.mcp.json",
  "renderers\android-studio.mcp.json",
  "renderers\antigravity.mcp_config.json"
)) {
  $path = Join-Path $rootPath $rel
  if (-not (Test-Path -LiteralPath $path)) { continue }
  $text = Get-Content -LiteralPath $path -Raw
  if ($text -match '65432') { $portFindings.Add($rel) | Out-Null }
}
Add-Result $results "no active :65432 route" ($portFindings.Count -eq 0) (($portFindings -join ", ") -replace "^$", "no :65432 route present in managed configs/contracts")

$liveMcpSecretFindings = [System.Collections.Generic.List[string]]::new()
foreach ($livePath in @(
  "C:\Users\ynotf\.cursor\mcp.json",
  "C:\Users\ynotf\.openclaw\openclaw.json",
  "C:\Users\ynotf\.minimax\mcp\mcp.json",
  "C:\Users\ynotf\.mavis\mcp\mcp.json",
  "C:\Users\ynotf\.gemini\config\mcp_config.json",
  "C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json"
)) {
  foreach ($finding in @(Test-ManagedMcpSecrets -Path $livePath)) {
    $liveMcpSecretFindings.Add("$livePath -> $finding") | Out-Null
  }
}
Add-Result $results "live managed MCP configs sanitized" ($liveMcpSecretFindings.Count -eq 0) (($liveMcpSecretFindings -join "; ") -replace "^$", "no raw MCP secrets or retired hosted routes found")

$docsPath = "C:\Users\ynotf\.cursor\vendor\arabold-docs-mcp\node_modules\@arabold\docs-mcp-server\dist\index.js"
$fabricPath = "C:\Users\ynotf\.cursor\vendor\context-fabric-mcp\node_modules\context-fabric\dist\index.js"
$depwirePath = "C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd"
$installMissing = @()
if (-not (Test-Path -LiteralPath $docsPath)) { $installMissing += "arabold-docs entrypoint missing" }
if (-not (Test-Path -LiteralPath $fabricPath)) { $installMissing += "context-fabric entrypoint missing" }
if (-not (Test-Path -LiteralPath $depwirePath)) { $installMissing += "depwire-cli global shim missing" }
Add-Result $results "vendored/global MCP installs" ($installMissing.Count -eq 0) (($installMissing -join "; ") -replace "^$", "arabold-docs, context-fabric, and depwire-cli entrypoints exist")

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

if ($WriteReport) {
  $artifactDir = Join-Path $rootPath "artifacts"
  $docsDir = Join-Path $rootPath "docs"
  New-Item -ItemType Directory -Force -Path $artifactDir, $docsDir | Out-Null
  $jsonPath = Join-Path $artifactDir "repo-validation-report.json"
  $mdPath = Join-Path $docsDir "repo-validation-report.md"
  $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding utf8
  $lines | Set-Content -LiteralPath $mdPath -Encoding utf8
}

$lines | ForEach-Object { Write-Output $_ }

if ($allPassed) {
  if ($WriteReport) {
    Write-Output "PASS: Repo validation succeeded. Report written."
  } else {
    Write-Output "PASS: Repo validation succeeded. Dry-run only; no report files written."
  }
  exit 0
}

if ($WriteReport) {
  Write-Output "FAIL: Repo validation failed. Report written."
} else {
  Write-Output "FAIL: Repo validation failed. Dry-run only; no report files written."
}
exit 1
