param(
  [switch]$RequireConfiguredClients,
  [switch]$RequireRunningClients,
  [switch]$RequireRestartAfterConfig
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$gatewayContractPath = Join-Path $repoRoot "contracts\agentcore-gateway-client.json"
$gatewayContract = Get-Content -LiteralPath $gatewayContractPath -Raw | ConvertFrom-Json
$gatewayName = [string]$gatewayContract.name
$gatewayUrl = [string]$gatewayContract.url

function Get-ClientGatewayExpectation {
  param([string]$ContractKey)
  $hintProperty = $gatewayContract.client_render_hints.PSObject.Properties[$ContractKey]
  if ($null -eq $hintProperty) {
    throw "Missing gateway client render hint for '$ContractKey'."
  }
  $hint = $hintProperty.Value
  $expectedUrl = if ($hint.gateway_url) { [string]$hint.gateway_url } else { $gatewayUrl }
  $authMode = if ($hint.gateway_auth_mode) { [string]$hint.gateway_auth_mode } else { 'bearer_env' }
  return [pscustomobject]@{
    url = $expectedUrl
    auth_mode = $authMode
    require_auth = ($authMode -ne 'process_attested_proxy')
  }
}

function Add-Result {
  param(
    [System.Collections.Generic.List[object]]$Results,
    [string]$Name,
    [bool]$Passed,
    [string]$Detail,
    [string]$Status = $(if ($Passed) { "pass" } else { "fail" })
  )
  $Results.Add([pscustomobject]@{
    name = $Name
    passed = $Passed
    status = $Status
    detail = $Detail
  }) | Out-Null
}

function Read-JsonFile {
  param([string]$Path)
  Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Get-ServerNames {
  param([object]$Config)
  if ($Config.mcpServers) { return @($Config.mcpServers.PSObject.Properties.Name) }
  if ($Config.servers) { return @($Config.servers.PSObject.Properties.Name) }
  if ($Config.context_servers) { return @($Config.context_servers.PSObject.Properties.Name) }
  if ($Config.mcp -and $Config.mcp.servers) { return @($Config.mcp.servers.PSObject.Properties.Name) }
  if ($Config.mcp) {
    $reserved = @("servers", "enabled", "settings")
    return @($Config.mcp.PSObject.Properties.Name | Where-Object { $reserved -notcontains $_ })
  }
  return @()
}

function Get-CodexServerNames {
  param([string]$Path)
  $text = Get-Content -LiteralPath $Path -Raw
  return @(
    [regex]::Matches($text, "(?m)^\[mcp_servers\.([^.\]\r\n]+)\]") |
      ForEach-Object { $_.Groups[1].Value.Trim('"') }
  )
}

function Join-Names {
  param([string[]]$Names)
  if (-not $Names -or $Names.Count -eq 0) { return "none" }
  return ($Names -join ", ")
}

function Test-SecretLiteralPresence {
  param(
    [string]$Name,
    [string]$Path,
    [System.Collections.Generic.List[object]]$Results
  )
  $text = Get-Content -LiteralPath $Path -Raw
  $secretPattern = "Bearer\s+(?!\$\{env:|\$\{|env\.|<)[A-Za-z0-9._~+/=-]{24,}|sk-(proj|or-v1|ant)-[A-Za-z0-9._~+/=-]{12,}|ghp_[A-Za-z0-9_]{20,}|AIza[A-Za-z0-9_\-]{30,}"
  $literalPresent = [bool]($text -match $secretPattern)
  Add-Result $Results "$Name secret literal presence" $true "checked without printing values; literal_present=$literalPresent" $(if ($literalPresent) { "info" } else { "pass" })
}

function Test-ClientConfig {
  param(
    [string]$Name,
    [string]$ContractKey,
    [string]$Path,
    [string]$ProcessPattern,
    [string[]]$AllowedExtraServers = @(),
    [string[]]$ForbiddenServers = @(),
    [switch]$TomlConfig
  )

  $results = [System.Collections.Generic.List[object]]::new()
  $expectation = Get-ClientGatewayExpectation -ContractKey $ContractKey
  $exists = Test-Path -LiteralPath $Path
  if (-not $exists) {
    $required = [bool]$RequireConfiguredClients
    Add-Result $results "$Name config exists" (-not $required) $Path $(if ($required) { "fail" } else { "skipped" })
    return $results
  }

  Add-Result $results "$Name config exists" $true $Path
  $jsonConfig = $null
  $servers = if ($TomlConfig) {
    Get-CodexServerNames -Path $Path
  } else {
    $jsonConfig = Read-JsonFile -Path $Path
    Get-ServerNames -Config $jsonConfig
  }

  if (-not $TomlConfig -and $servers.Count -eq 0) {
    Add-Result $results "$Name MCP config skipped" $true "config file exists but no supported MCP server container was found" "skipped"
    return $results
  }

  $missingGateway = @($gatewayName | Where-Object { $servers -notcontains $_ })
  $allowed = @($gatewayName) + @($AllowedExtraServers)
  $unexpected = @($servers | Where-Object { $allowed -notcontains $_ })
  $forbiddenLower = @($ForbiddenServers | ForEach-Object { $_.ToLowerInvariant() })
  $presentForbidden = @(
    $servers | Where-Object {
      $serverLower = $_.ToLowerInvariant()
      ($forbiddenLower -contains $serverLower) -or
      ($serverLower -match "postgres|postgre|psql|pgvector|database|mcp[_-]?docker|swarmrecall|swarmvault|global.memory.gateway|context7|composio|hostinger|openrouter")
    }
  )

  Add-Result $results "$Name agentcore-gateway present" ($missingGateway.Count -eq 0) ("required=$gatewayName; source_contract=$gatewayContractPath; present=" + (Join-Names $servers))
  if ($missingGateway.Count -eq 0) {
    if ($TomlConfig) {
      $text = Get-Content -LiteralPath $Path -Raw
      $sectionPattern = "(?ms)^\[mcp_servers\.$([regex]::Escape($gatewayName))\]\s*(.*?)(?=^\[|\z)"
      $section = [regex]::Match($text, $sectionPattern).Groups[1].Value
      $urlOk = $section -match "url\s*=\s*`"$([regex]::Escape($expectation.url))`""
      $authOk = $section -match "bearer_token_env_var\s*="
      $authModeOk = if ($expectation.require_auth) { $authOk } else { -not $authOk }
      Add-Result $results "$Name gateway contract" ($urlOk -and $authModeOk) "expected_url=$($expectation.url); auth_mode=$($expectation.auth_mode); bearer_token_env_var_present=$authOk"
    } else {
      $container = if ($jsonConfig.mcpServers) { $jsonConfig.mcpServers } elseif ($jsonConfig.servers) { $jsonConfig.servers } elseif ($jsonConfig.context_servers) { $jsonConfig.context_servers } elseif ($jsonConfig.mcp_servers) { $jsonConfig.mcp_servers } elseif ($jsonConfig.mcp -and $jsonConfig.mcp.servers) { $jsonConfig.mcp.servers } else { $jsonConfig.mcp }
      $entry = $container.PSObject.Properties[$gatewayName].Value
      $url = if ($entry.url) { [string]$entry.url } elseif ($entry.serverUrl) { [string]$entry.serverUrl } elseif ($entry.baseUrl) { [string]$entry.baseUrl } elseif ($entry.httpUrl) { [string]$entry.httpUrl } else { "" }
      $headers = if ($entry.headers) { $entry.headers } elseif ($entry.http_headers) { $entry.http_headers } else { $null }
      $authPresent = [bool]($headers -and ($headers.PSObject.Properties.Name -contains "Authorization" -or $headers.PSObject.Properties.Name -contains "authorization"))
      $authModeOk = if ($expectation.require_auth) { $authPresent } else { -not $authPresent }
      Add-Result $results "$Name gateway contract" ($url -eq $expectation.url -and $authModeOk) "url=$url; expected_url=$($expectation.url); auth_mode=$($expectation.auth_mode); authorization_present=$authPresent; authorization_value=redacted"
    }
  }
  Add-Result $results "$Name forbidden direct servers absent" ($presentForbidden.Count -eq 0) ("present=" + (Join-Names $presentForbidden))
  Add-Result $results "$Name only approved direct extras present" ($unexpected.Count -eq 0) ("allowed_extras=" + (Join-Names $AllowedExtraServers) + "; unexpected=" + (Join-Names $unexpected))
  Test-SecretLiteralPresence -Name $Name -Path $Path -Results $results

  $procs = @(Get-Process | Where-Object { $_.ProcessName -match $ProcessPattern } | Sort-Object StartTime)
  if ($procs.Count -eq 0) {
    $requiredRunning = [bool]$RequireRunningClients
    Add-Result $results "$Name running" (-not $requiredRunning) "not running" $(if ($requiredRunning) { "fail" } else { "skipped" })
    return $results
  }

  $configTime = (Get-Item -LiteralPath $Path).LastWriteTime
  $latestStart = ($procs | Select-Object -Last 1).StartTime
  $restartedAfterConfig = $latestStart -gt $configTime
  Add-Result $results "$Name running" $true ("latest_start=" + $latestStart.ToString("o"))
  Add-Result $results "$Name restarted after config" ($restartedAfterConfig -or -not $RequireRestartAfterConfig) ("latest_start=" + $latestStart.ToString("o") + "; config_mtime=" + $configTime.ToString("o") + "; restarted_after_config=" + $restartedAfterConfig) $(if ($restartedAfterConfig) { "pass" } elseif ($RequireRestartAfterConfig) { "fail" } else { "info" })

  return $results
}

$forbiddenAgentCoreDirect = @(
  "swarmrecall",
  "swarmvault",
  "swarmclaw",
  "global-memory-gateway",
  "context7",
  "mem0",
  "mem0_mcp_server",
  "openmemory",
  "composio",
  "hostinger",
  "Hostinger",
  "openrouter",
  "postgres",
  "postgresql",
  "psql",
  "MCP_DOCKER",
  "mcp_docker",
  "filesystem",
  "whole-drive-filesystem",
  "artiforge",
  "sequential-thinking",
  "serena"
)

$results = [System.Collections.Generic.List[object]]::new()

$jsonClients = @(
  @{ name = "Cursor"; contract_key = "cursor"; path = "C:\Users\ynotf\.cursor\mcp.json"; process = "Cursor"; allowed = @() },
  @{ name = "Zoo Code"; contract_key = "zoo-code"; path = "C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json"; process = "Cursor"; allowed = @("zoo-code") },
  @{ name = "Zed"; contract_key = "zed"; path = "C:\Users\ynotf\AppData\Roaming\Zed\settings.json"; process = "Zed"; allowed = @() },
  @{ name = "Eigent"; contract_key = "eigent"; path = "C:\Users\ynotf\.eigent\mcp.json"; process = "eigent"; allowed = @() },
  @{ name = "MiniMax"; contract_key = "minimax"; path = "C:\Users\ynotf\.minimax\mcp\mcp.json"; process = "MiniMax"; allowed = @("matrix", "cu", "trash") },
  @{ name = "Mavis"; contract_key = "minimax"; path = "C:\Users\ynotf\.mavis\mcp\mcp.json"; process = "Mavis"; allowed = @("matrix", "cu", "trash") },
  @{ name = "Antigravity Gemini"; contract_key = "antigravity"; path = "C:\Users\ynotf\.gemini\config\mcp_config.json"; process = "Antigravity"; allowed = @("notebooks", "visualization", "data-agent-kit") },
  @{ name = "Antigravity IDE Roaming"; contract_key = "antigravity"; path = "C:\Users\ynotf\AppData\Roaming\Antigravity IDE\User\mcp.json"; process = "Antigravity"; allowed = @() },
  @{ name = "ZCode"; contract_key = "zcode"; path = "C:\Users\ynotf\.zcode\cli\config.json"; process = "ZCode"; allowed = @() },
  @{ name = "Open Interpreter"; contract_key = "open-interpreter"; path = "C:\Users\ynotf\AppData\Roaming\interpreter\config.json"; process = "Interpreter|Open Interpreter"; allowed = @() },
  @{ name = "Devin"; contract_key = "devin"; path = "C:\Users\ynotf\AppData\Roaming\devin\mcp_config.json"; process = "Devin"; allowed = @("devin/github-mcp-server", "devin/vercel") },
  @{ name = "Claude Desktop"; contract_key = "claude-desktop"; path = "C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json"; process = "Claude"; allowed = @("GitKraken") }
)

foreach ($client in $jsonClients) {
  $clientResults = Test-ClientConfig -Name $client.name -ContractKey $client.contract_key -Path $client.path -ProcessPattern $client.process -AllowedExtraServers $client.allowed -ForbiddenServers $forbiddenAgentCoreDirect
  foreach ($item in $clientResults) { $results.Add($item) | Out-Null }
}

$codexConfig = "C:\Users\ynotf\.codex\config.toml"
$codexAllowedExtras = @(
  "cheap-workers",
  "cua_repl",
  "morph-mcp",
  "node_repl",
  "github",
  "sites-design-picker",
  "codex-security",
  "devin"
)
$codexForbidden = @($forbiddenAgentCoreDirect | Where-Object { $_ -notin @("MCP_DOCKER", "mcp_docker") })
$codexResults = Test-ClientConfig -Name "Codex" -ContractKey "codex" -Path $codexConfig -ProcessPattern "^codex$" -AllowedExtraServers $codexAllowedExtras -ForbiddenServers $codexForbidden -TomlConfig
foreach ($item in $codexResults) { $results.Add($item) | Out-Null }

if (Test-Path -LiteralPath $codexConfig) {
  $codexList = & codex mcp list 2>&1
  Add-Result $results "Codex CLI mcp list" ($LASTEXITCODE -eq 0) (($codexList | ForEach-Object { [string]$_ }) -join "`n")
}

$proxyUrls = @(
  $gatewayContract.client_render_hints.PSObject.Properties.Value |
    Where-Object { $_.gateway_auth_mode -eq 'process_attested_proxy' } |
    ForEach-Object { [string]$_.gateway_url } |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
    Sort-Object -Unique
)
foreach ($proxyUrl in $proxyUrls) {
  $proxyBase = $proxyUrl.Substring(0, $proxyUrl.Length - '/mcp'.Length)
  $healthStatus = 0
  try {
    $healthStatus = [int](Invoke-WebRequest -Uri "$proxyBase/healthz" -UseBasicParsing -TimeoutSec 5).StatusCode
  } catch {
    if ($_.Exception.Response) { $healthStatus = [int]$_.Exception.Response.StatusCode }
  }
  Add-Result $results "Builder compatibility proxy health" ($healthStatus -eq 200) "url=$proxyBase/healthz; status=$healthStatus"

  $deniedStatus = 0
  try {
    $deniedStatus = [int](Invoke-WebRequest -Uri $proxyUrl -Method Post -ContentType 'application/json' -Body '{}' -UseBasicParsing -TimeoutSec 10).StatusCode
  } catch {
    if ($_.Exception.Response) { $deniedStatus = [int]$_.Exception.Response.StatusCode }
  }
  Add-Result $results "Builder compatibility proxy untrusted caller denied" ($deniedStatus -eq 403) "url=$proxyUrl; headerless_status=$deniedStatus"
}

$results | ConvertTo-Json -Depth 6
if ($results | Where-Object { -not $_.passed }) { exit 1 }
