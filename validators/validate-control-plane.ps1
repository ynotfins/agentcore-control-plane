param(
  [string]$Root = "D:\github\agentcore-control-plane",
  [switch]$WriteReport,
  [switch]$DryRun,
  # Skip live-state checks (Codex CLI, Postgres listener, scheduled tasks, live IDE configs).
  # Use for repo-only/source validation passes.
  [switch]$SourceOnly
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
  if ($Json.mcp_servers) { return $Json.mcp_servers }
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
    $line = @(netstat -ano -p tcp | Select-String '127\.0\.0\.1:55433\s+.*LISTENING\s+\d+$' | Select-Object -First 1)[0]
    if (-not $line) { return @{ ok = $false; detail = "no listener on 127.0.0.1:55433" } }
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
    $_.FullName -notmatch "\\reports\\_raw\\" -and
    $_.FullName -notmatch "\\\.minimax\\" -and
    $_.FullName -notmatch "\\\.git\\" -and
    $_.Extension -notin @(".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip")
  }
# Allowlisted non-secret tokens that pattern-match (env var names, documented placeholders).
$secretFalsePositives = @(
  "Bearer BIFROST_MCP_VIRTUAL_KEY",
  "Bearer vk_your_production_key",
  "Bearer vk_your_development_key",
  "Bearer YOUR_API_KEY"
)
foreach ($file in $scanFiles) {
  $text = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction SilentlyContinue
  if (-not $text) { continue }
  foreach ($fp in $secretFalsePositives) { $text = $text.Replace($fp, "") }
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
Add-Result $results "DepWire governed launcher and credential scope" ($depwireFindings.Count -eq 0) (($depwireFindings -join ", ") -replace "^$", "legacy rollback renderers keep their frozen depwire launcher shape; extension-only Pro license scope enforced (current policy: depwire via agentcore-gateway, telemetry ON)")

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

if (-not $SourceOnly) {
  # Post-Bifrost-cutover: live Codex uses one agentcore-gateway entry; direct servers and Swarm are retired.
  $liveCodex = Get-LiveCodexServers
  if (-not $liveCodex.ok) {
    Add-Result $results "live Codex routing set" $false ("codex mcp list unavailable: " + $liveCodex.error)
    Add-Result $results "live Codex retired servers absent" $false ("codex mcp list unavailable: " + $liveCodex.error)
    Add-Result $results "live Codex server budget" $false ("codex mcp list unavailable: " + $liveCodex.error)
  }
  else {
    $codexGatewayOk = $liveCodex.names -contains "agentcore-gateway"
    Add-Result $results "live Codex routing set" $codexGatewayOk ("gateway-era expectation: single agentcore-gateway entry (+ Codex-managed extras); active=" + ($liveCodex.names -join ", "))

    $retiredLiveCodex = @($liveCodex.names | Where-Object { $_ -in @("context7", "mem0_mcp_server", "artiforge__codebase_scanner", "thinking-patterns", "swarmrecall", "swarmvault", "global-memory-gateway") })
    Add-Result $results "live Codex retired servers absent" ($retiredLiveCodex.Count -eq 0) (($retiredLiveCodex -join ", ") -replace "^$", "no retired/Swarm servers active in live Codex")

    $codexServerBudget = $liveCodex.names.Count -le 18
    Add-Result $results "live Codex server budget" $codexServerBudget ("count=" + $liveCodex.names.Count + " limit=18")
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

# Legacy direct-mode renderers are ROLLBACK-ONLY artifacts (superseded by gateway architecture).
# They are checked for internal preservation, not enforced as current IDE policy.
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
Add-Result $results "legacy rollback renderers preserved" ($swarmBaselineFindings.Count -eq 0) (($swarmBaselineFindings -join "; ") -replace "^$", "legacy direct-mode renderer contents preserved unchanged for rollback (NOT current IDE policy; current = single agentcore-gateway entry)")

# Gateway-era renderers: every gateway-client renderer must contain exactly one agentcore-gateway
# entry and must not contain Swarm or direct per-tool servers.
$gatewayClientFindings = [System.Collections.Generic.List[string]]::new()
$gatewayClientDir = Join-Path $rootPath "renderers\gateway-clients"
if (Test-Path -LiteralPath $gatewayClientDir) {
  foreach ($file in Get-ChildItem -LiteralPath $gatewayClientDir -Filter "*.json") {
    $rel = "renderers\gateway-clients\" + $file.Name
    try {
      $names = @(Get-ServerNames $file.FullName | Where-Object { $_ -ne "_agentcore" })
      if ($names.Count -ne 1 -or $names[0] -ne "agentcore-gateway") {
        $gatewayClientFindings.Add("$rel servers=[$($names -join ", ")]") | Out-Null
      }
      $text = Get-Content -LiteralPath $file.FullName -Raw
      foreach ($banned in @("swarmrecall", "swarmvault", "swarmclaw", "global-memory-gateway")) {
        if ($text -match [regex]::Escape($banned)) { $gatewayClientFindings.Add("$rel contains $banned") | Out-Null }
      }
    }
    catch { $gatewayClientFindings.Add("$rel parse-error: $($_.Exception.Message)") | Out-Null }
  }
}
else { $gatewayClientFindings.Add("renderers\gateway-clients missing") | Out-Null }
Add-Result $results "gateway renderers single-entry no-Swarm" ($gatewayClientFindings.Count -eq 0) (($gatewayClientFindings -join "; ") -replace "^$", "every gateway-client renderer has exactly one agentcore-gateway server and no Swarm/retired entries")

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

# ---------------------------------------------------------------------------
# Authority reconciliation checks (2026-07-14)
# ---------------------------------------------------------------------------

# AuthorityHierarchyComplete: all six hierarchy levels exist and DOC_AUTHORITY names them.
$hierarchyFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in @("PROJECT_ANCHOR.md", "DOC_AUTHORITY.md", "CONTEXT_BLOCK.md", "docs\memory-platform\MEMORY_PLATFORM_EXECUTION_PLAN.md", "contracts\bifrost-upstream-mcp-registry.json", "contracts\agentcore-gateway-client.json", "docs\handoffs\AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md")) {
  if (-not (Test-Path -LiteralPath (Join-Path $rootPath $rel))) { $hierarchyFindings.Add("missing $rel") | Out-Null }
}
$docAuthorityText = Get-Content -LiteralPath (Join-Path $rootPath "DOC_AUTHORITY.md") -Raw -ErrorAction SilentlyContinue
if ($docAuthorityText -notmatch "MEMORY_PLATFORM_EXECUTION_PLAN\.md") { $hierarchyFindings.Add("DOC_AUTHORITY missing execution-plan reference") | Out-Null }
if ($docAuthorityText -notmatch "ChaosCentral-Current-Build") { $hierarchyFindings.Add("DOC_AUTHORITY missing machine-fact authority reference") | Out-Null }
if (-not (Test-Path -LiteralPath "D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md")) { $hierarchyFindings.Add("machine-fact authority file missing on D:") | Out-Null }
Add-Result $results "AuthorityHierarchyComplete" ($hierarchyFindings.Count -eq 0) (($hierarchyFindings -join "; ") -replace "^$", "all six authority levels present and referenced")

# NoDatabasePlanAsCurrent: DOC_AUTHORITY must not classify database-plan.md as authoritative-stable.
$stableSection = ""
if ($docAuthorityText -match "(?s)## Authoritative[^\r\n]{0,20}stable(.*?)## Current-state") { $stableSection = $Matches[1] }
$dbPlanOk = $stableSection -notmatch "database-plan\.md"
Add-Result $results "NoDatabasePlanAsCurrent" $dbPlanOk ("database-plan.md " + $(if ($dbPlanOk) { "is not classified authoritative-stable" } else { "is still classified authoritative-stable in DOC_AUTHORITY.md" }))

# Banner checks on stale executable documents.
$bannerChecks = [ordered]@{
  "AGENT_DATABASE_BOOTSTRAP.md" = "HISTORICAL"
  "database-plan.md" = "HISTORICAL SCHEMA EVIDENCE"
  "CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md" = "HISTORICAL"
  "Global-memory-and-context-system-revised-2.md" = "DO NOT EXECUTE"
  "docs\handoffs\AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md" = "DO NOT EXECUTE"
}
$bannerFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in $bannerChecks.Keys) {
  $path = Join-Path $rootPath $rel
  if (-not (Test-Path -LiteralPath $path)) { continue }
  $head = (Get-Content -LiteralPath $path -TotalCount 15) -join "`n"
  if ($head -notmatch [regex]::Escape($bannerChecks[$rel])) { $bannerFindings.Add($rel) | Out-Null }
}
Add-Result $results "StaleDocumentsBannered" ($bannerFindings.Count -eq 0) (($bannerFindings -join ", ") -replace "^$", "all stale executable documents carry historical banners")

# NoSwarmFirstCurrentRules / NoDepwireTelemetryOff / no retired gateway mandate in current rule files.
$currentRuleFiles = @(
  "AGENTS.md", "CLAUDE.md",
  "rules\canonical\GLOBAL_AGENT_RULES.md", "rules\global-mcp-routing.md", "rules\environment-and-secrets.md",
  ".cursor\rules\agentcore-env-policy.mdc", "docs\GLOBAL_AGENT_RULES.md"
)
$staleRuleFindings = [System.Collections.Generic.List[string]]::new()
foreach ($rel in $currentRuleFiles) {
  $path = Join-Path $rootPath $rel
  if (-not (Test-Path -LiteralPath $path)) { continue }
  $text = Get-Content -LiteralPath $path -Raw
  if ($text -match "DEPWIRE_NO_TELEMETRY\s*=\s*1") { $staleRuleFindings.Add("$rel sets DEPWIRE_NO_TELEMETRY=1") | Out-Null }
  if ($text -match "(?i)use\s+``?global-memory-gateway``?\s+only" -or $text -match "(?i)must\s+use\s+``?global-memory-gateway``?[\.\s]") { $staleRuleFindings.Add("$rel mandates retired global-memory-gateway") | Out-Null }
  if ($text -match "(?i)swarmrecall.*(mandatory|required in every|must be present)" ) { $staleRuleFindings.Add("$rel makes Swarm mandatory") | Out-Null }
}
Add-Result $results "NoSwarmFirstCurrentRules" ($staleRuleFindings.Count -eq 0) (($staleRuleFindings -join "; ") -replace "^$", "no current rule file teaches Swarm-first, telemetry-off, or the retired gateway identity")

# AGENTS.md must stay durable: mutable runtime/service/database/Milestone facts belong
# in generated STATE projections, current handoff/evidence, and classified machine docs.
$agentsText = Get-Content -LiteralPath (Join-Path $rootPath "AGENTS.md") -Raw -ErrorAction SilentlyContinue
$agentsMutableFindings = [System.Collections.Generic.List[string]]::new()
$requiredAuthorityPointer = "Mutable machine, service, database, Milestone, and runtime state belongs in the generated STATE projections"
if ($agentsText -notmatch [regex]::Escape($requiredAuthorityPointer)) {
  $agentsMutableFindings.Add("missing mutable-state authority pointer") | Out-Null
}
$agentsMutablePatterns = @(
  [pscustomobject]@{ label = "localhost/runtime port"; pattern = "127\.0\.0\.1:\d+" },
  [pscustomobject]@{ label = "Bifrost runtime path"; pattern = "H:\\AgentRuntime" },
  [pscustomobject]@{ label = "runtime memory/database path"; pattern = "F:\\(?:AgentCore|PostgreSQL)" },
  [pscustomobject]@{ label = "compatibility/live-ops runtime path"; pattern = "D:\\MCP-Control-Plane" },
  [pscustomobject]@{ label = "PostgreSQL service state"; pattern = "PostgreSQL\s+\d+\s+runs|AgentCore-PostgreSQL\d+" },
  [pscustomobject]@{ label = "database inventory"; pattern = "global_vector_memory_store|cognee_core|swarmrecall\s+DB|agent_core\s+database" },
  [pscustomobject]@{ label = "Milestone completion state"; pattern = "M\d+\s+acceptance|Milestone\s+M?\d+\s+(?:complete|completed|passed)" },
  [pscustomobject]@{ label = "commit-specific fact"; pattern = "commit\s+[0-9a-f]{7,40}|git_commit_hash" }
)
foreach ($check in $agentsMutablePatterns) {
  if ($agentsText -match $check.pattern) {
    $agentsMutableFindings.Add($check.label) | Out-Null
  }
}
Add-Result $results "AGENTS durable authority pointers only" ($agentsMutableFindings.Count -eq 0) (($agentsMutableFindings -join "; ") -replace "^$", "AGENTS.md contains durable rules plus mutable-state authority pointer only")

# Continual-learning transcript index is retrieval-only evidence metadata.
$indexFindings = [System.Collections.Generic.List[string]]::new()
$indexRel = ".cursor\hooks\state\continual-learning-index.json"
$indexPath = Join-Path $rootPath $indexRel
if (-not (Test-Path -LiteralPath $indexPath)) {
  $indexFindings.Add("$indexRel missing") | Out-Null
}
else {
  try {
    $index = Read-Json $indexPath
    if ([int]$index.version -lt 2) { $indexFindings.Add("version must be >= 2") | Out-Null }
    if ($index.retrievalOnly -ne $true) { $indexFindings.Add("retrievalOnly must be true") | Out-Null }
    if ($index.startupContextEligible -ne $false) { $indexFindings.Add("startupContextEligible must be false") | Out-Null }
    $normalStatuses = @($index.normalRetrievalStatuses)
    if ($normalStatuses.Count -ne 1 -or $normalStatuses[0] -ne "active") {
      $indexFindings.Add("normalRetrievalStatuses must contain only active") | Out-Null
    }
    if (-not $index.transcripts) {
      $indexFindings.Add("transcripts missing") | Out-Null
    }
    else {
      $requiredEntryFields = @("sourcePath", "authorityClass", "mtimeUtc", "size", "sha256", "retrievalStatus")
      $validStatuses = @("active", "quarantined", "excluded")
      foreach ($prop in $index.transcripts.PSObject.Properties) {
        $entryName = $prop.Name
        $entry = $prop.Value
        foreach ($field in $requiredEntryFields) {
          if (-not ($entry.PSObject.Properties.Name -contains $field)) {
            $indexFindings.Add("$entryName missing $field") | Out-Null
          }
        }
        if (($entry.PSObject.Properties.Name -contains "authorityClass") -and $entry.authorityClass -ne "evidence_only") {
          $indexFindings.Add("$entryName authorityClass=$($entry.authorityClass)") | Out-Null
        }
        if (($entry.PSObject.Properties.Name -contains "retrievalStatus") -and $entry.retrievalStatus -notin $validStatuses) {
          $indexFindings.Add("$entryName retrievalStatus=$($entry.retrievalStatus)") | Out-Null
        }
        if (($entry.PSObject.Properties.Name -contains "sha256") -and $entry.sha256 -notmatch "^[a-f0-9]{64}$") {
          $indexFindings.Add("$entryName invalid sha256") | Out-Null
        }
      }
    }
  }
  catch {
    $indexFindings.Add("$indexRel parse-error: $($_.Exception.Message)") | Out-Null
  }
}
Add-Result $results "ContinualLearningTranscriptIndex" ($indexFindings.Count -eq 0) (($indexFindings -join "; ") -replace "^$", "transcript index entries are evidence-only, retrieval-only, and active-only for normal retrieval")

$startupReferenceFindings = [System.Collections.Generic.List[string]]::new()
$startupReferenceFiles = Get-ChildItem -LiteralPath $rootPath -Recurse -File -Force |
  Where-Object {
    $_.FullName -notmatch "\\\.git\\" -and
    $_.FullName -notmatch "\\artifacts\\" -and
    $_.FullName -notmatch "\\backups\\" -and
    $_.FullName -notmatch "\\reports\\_raw\\" -and
    $_.FullName -notmatch "\\\.cursor\\hooks\\state\\" -and
    $_.FullName -notmatch "\\validators\\validate-control-plane\.ps1$" -and
    $_.FullName -notmatch "\\\.cursor\\hooks\\update-continual-learning-index\.ps1$" -and
    $_.Extension -notin @(".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip")
  }
foreach ($file in $startupReferenceFiles) {
  $text = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction SilentlyContinue
  if (-not $text) { continue }
  if ($text -match "continual-learning-index\.json" -and $text -match "(?i)automatic\s+startup|startup\s+context|startup_context") {
    $startupReferenceFindings.Add($file.FullName.Substring($rootPath.Length + 1)) | Out-Null
  }
}
Add-Result $results "ContinualLearningNotStartupContext" ($startupReferenceFindings.Count -eq 0) (($startupReferenceFindings -join ", ") -replace "^$", "continual-learning index is not referenced as automatic startup context")

# NoDriveWriteBoundaryConflict: drive rule must not name D:\MCP-Control-Plane as authority.
$driveRule = Get-Content -LiteralPath (Join-Path $rootPath "docs\DRIVE_WRITE_BOUNDARY_RULE.md") -Raw -ErrorAction SilentlyContinue
$driveOk = $driveRule -notmatch "MCP-Control-Plane``?\s+is\s+the\s+authority"
Add-Result $results "NoDriveWriteBoundaryConflict" $driveOk ($(if ($driveOk) { "drive-boundary rule points at PROJECT_ANCHOR drive roles" } else { "docs\DRIVE_WRITE_BOUNDARY_RULE.md still names D:\MCP-Control-Plane as authority" }))

# PolicyDocsExist + PolicyTemplatesExist.
$policyDocs = @(
  "docs\agent-policy\NEW_PROJECT_BOOTSTRAP.md",
  "docs\agent-policy\MILESTONE_EXECUTION_STANDARD.md",
  "docs\agent-policy\CHECKLIST_STANDARD.md",
  "docs\agent-policy\TOOL_LIFECYCLE_POLICY.md",
  "docs\agent-policy\DOCUMENTATION_READ_ORDER.md"
)
$missingPolicy = @($policyDocs | Where-Object { -not (Test-Path -LiteralPath (Join-Path $rootPath $_)) })
Add-Result $results "PolicyDocsExist" ($missingPolicy.Count -eq 0) ("missing=" + (($missingPolicy -join ", ") -replace "^$", "none"))

$templateFiles = @(
  "templates\project-governance\.agentcore\PROJECT_CHARTER.md",
  "templates\project-governance\.agentcore\MILESTONES.md",
  "templates\project-governance\.agentcore\TOOL_MANIFEST.yaml",
  "templates\project-governance\.agentcore\PROJECT_STATE.json",
  "templates\project-governance\.agentcore\RISK_REGISTER.md",
  "templates\project-governance\.agentcore\ACCEPTANCE_TESTS.md",
  "templates\project-governance\.agentcore\milestones\M0-bootstrap.md",
  "templates\project-governance\.agentcore\checklists\state.json"
)
$missingTemplates = @($templateFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $rootPath $_)) })
Add-Result $results "PolicyTemplatesExist" ($missingTemplates.Count -eq 0) ("missing=" + (($missingTemplates -join ", ") -replace "^$", "none"))

# IDEProfileFoldersExist + IDEEditabilityDeclared.
$gatewayClientContract = Read-Json (Join-Path $rootPath "contracts\agentcore-gateway-client.json")
$ideFindings = [System.Collections.Generic.List[string]]::new()
$editabilityUnverified = [System.Collections.Generic.List[string]]::new()
$validModes = @("direct_write", "generated_prompt", "manual_import", "unsupported", "unverified")
foreach ($ideId in $gatewayClientContract.client_render_hints.PSObject.Properties.Name) {
  $profileDir = Join-Path $rootPath ("ide-profiles\" + $ideId)
  if (-not (Test-Path -LiteralPath $profileDir)) { $ideFindings.Add("missing ide-profiles\$ideId") | Out-Null; continue }
  foreach ($required in @("IDE_PROFILE.yaml", "GLOBAL_RULES.md", "INSTALL_OR_UPDATE.md", "VALIDATION.md")) {
    if (-not (Test-Path -LiteralPath (Join-Path $profileDir $required))) { $ideFindings.Add("ide-profiles\$ideId missing $required") | Out-Null }
  }
  if (-not (Get-ChildItem -LiteralPath $profileDir -Filter "MCP_CONFIG_TEMPLATE.*" -ErrorAction SilentlyContinue)) { $ideFindings.Add("ide-profiles\$ideId missing MCP_CONFIG_TEMPLATE") | Out-Null }
  $profileText = Get-Content -LiteralPath (Join-Path $profileDir "IDE_PROFILE.yaml") -Raw -ErrorAction SilentlyContinue
  $declaredModes = @([regex]::Matches($profileText, "(?m)^\s+(global_rules|project_rules|mcp_config):\s*([a-z_]+)") | ForEach-Object { $_.Groups[2].Value })
  if ($declaredModes.Count -lt 3) { $ideFindings.Add("ide-profiles\$ideId editability incomplete") | Out-Null }
  foreach ($mode in $declaredModes) {
    if ($mode -notin $validModes) { $ideFindings.Add("ide-profiles\$ideId invalid editability mode $mode") | Out-Null }
    if ($mode -eq "unverified") { $editabilityUnverified.Add($ideId) | Out-Null }
  }
}
Add-Result $results "IDEProfileFoldersExist" ($ideFindings.Count -eq 0) (($ideFindings -join "; ") -replace "^$", "profile folder with all artifacts exists for every gateway-client IDE")
$unverifiedList = @($editabilityUnverified | Sort-Object -Unique)
Add-Result $results "IDEEditabilityDeclared" $true ($(if ($unverifiedList.Count -gt 0) { "WARN unverified editability (allowed until live verification): " + ($unverifiedList -join ", ") } else { "all editability modes verified" }))

# WildcardGrantsDocumented: permitted_tools ["*"] requires the registry transitional note.
$bifrostRegistry = Read-Json (Join-Path $rootPath "contracts\bifrost-upstream-mcp-registry.json")
$wildcardServers = @($bifrostRegistry.servers.PSObject.Properties | Where-Object { (@($_.Value.permitted_tools) -join ",") -eq "*" } | ForEach-Object { $_.Name })
$wildcardOk = ($wildcardServers.Count -eq 0) -or ($null -ne $bifrostRegistry.tool_lifecycle_note)
Add-Result $results "WildcardGrantsDocumented" $wildcardOk ("wildcard servers=" + $wildcardServers.Count + $(if ($wildcardOk) { " covered by tool_lifecycle_note transitional exception (expires at memory-platform M6)" } else { " WITHOUT documented transitional exception" }))

# NoSecretsInIDEArtifacts: generated IDE artifacts must not contain resolved secret values.
$ideArtifactFindings = [System.Collections.Generic.List[string]]::new()
$ideArtifacts = @(Get-ChildItem -LiteralPath (Join-Path $rootPath "ide-profiles") -Recurse -File -ErrorAction SilentlyContinue) + @(Get-ChildItem -LiteralPath (Join-Path $rootPath "renderers\gateway-clients") -File -ErrorAction SilentlyContinue)
foreach ($file in $ideArtifacts) {
  $text = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction SilentlyContinue
  if (-not $text) { continue }
  foreach ($fp in $secretFalsePositives) { $text = $text.Replace($fp, "") }
  foreach ($pattern in $secretPatterns) {
    if ($text -match $pattern) { $ideArtifactFindings.Add($file.FullName.Substring($rootPath.Length + 1)) | Out-Null; break }
  }
}
Add-Result $results "NoSecretsInIDEArtifacts" ($ideArtifactFindings.Count -eq 0) (($ideArtifactFindings -join ", ") -replace "^$", "no secret-like literals in ide-profiles or gateway-client renderers")

# CanonicalPolicyRenderingsCurrent: derived IDE rule files match the canonical policy.
try {
  $renderCheck = & python (Join-Path $rootPath "scripts\render_ide_rules.py") --check 2>&1
  Add-Result $results "CanonicalPolicyRenderingsCurrent" ($LASTEXITCODE -eq 0) (($renderCheck | Select-Object -Last 1) -join "")
}
catch {
  Add-Result $results "CanonicalPolicyRenderingsCurrent" $false $_.Exception.Message
}

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
