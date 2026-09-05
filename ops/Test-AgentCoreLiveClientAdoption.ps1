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
    [string]$Path,
    [string]$ProcessPattern,
    [string[]]$AllowedExtraServers = @(),
    [string[]]$ForbiddenServers = @(),
    [switch]$TomlConfig
  )

  $results = [System.Collections.Generic.List[object]]::new()
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
      $urlOk = $section -match "url\s*=\s*`"$([regex]::Escape($gatewayUrl))`""
      $authOk = $section -match "bearer_token_env_var\s*="
      Add-Result $results "$Name gateway contract" ($urlOk -and $authOk) "expected_url=$gatewayUrl; bearer_token_env_var_present=$authOk"
    } else {
      $container = if ($jsonConfig.mcpServers) { $jsonConfig.mcpServers } elseif ($jsonConfig.servers) { $jsonConfig.servers } elseif ($jsonConfig.context_servers) { $jsonConfig.context_servers } elseif ($jsonConfig.mcp_servers) { $jsonConfig.mcp_servers } elseif ($jsonConfig.mcp -and $jsonConfig.mcp.servers) { $jsonConfig.mcp.servers } else { $jsonConfig.mcp }
      $entry = $container.PSObject.Properties[$gatewayName].Value
      $url = if ($entry.url) { [string]$entry.url } elseif ($entry.serverUrl) { [string]$entry.serverUrl } elseif ($entry.baseUrl) { [string]$entry.baseUrl } elseif ($entry.httpUrl) { [string]$entry.httpUrl } else { "" }
      $headers = if ($entry.headers) { $entry.headers } elseif ($entry.http_headers) { $entry.http_headers } else { $null }
      $authPresent = [bool]($headers -and ($headers.PSObject.Properties.Name -contains "Authorization" -or $headers.PSObject.Properties.Name -contains "authorization"))
      Add-Result $results "$Name gateway contract" ($url -eq $gatewayUrl -and $authPresent) "url=$url; expected_url=$gatewayUrl; authorization_present=$authPresent; authorization_value=redacted"
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
  @{ name = "Cursor"; path = "C:\Users\ynotf\.cursor\mcp.json"; process = "Cursor"; allowed = @() },
  @{ name = "Zoo Code"; path = "C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json"; process = "Cursor"; allowed = @("zoo-code") },
  @{ name = "Zed"; path = "C:\Users\ynotf\AppData\Roaming\Zed\settings.json"; process = "Zed"; allowed = @() },
  @{ name = "Eigent"; path = "C:\Users\ynotf\.eigent\mcp.json"; process = "eigent"; allowed = @() },
  @{ name = "MiniMax"; path = "C:\Users\ynotf\.minimax\mcp\mcp.json"; process = "MiniMax"; allowed = @("matrix", "cu", "trash") },
  @{ name = "Mavis"; path = "C:\Users\ynotf\.mavis\mcp\mcp.json"; process = "Mavis"; allowed = @("matrix", "cu", "trash") },
  @{ name = "Antigravity Gemini"; path = "C:\Users\ynotf\.gemini\config\mcp_config.json"; process = "Antigravity"; allowed = @("notebooks", "visualization", "data-agent-kit") },
  @{ name = "Antigravity Roaming"; path = "C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json"; process = "Antigravity"; allowed = @() },
  @{ name = "Antigravity IDE Roaming"; path = "C:\Users\ynotf\AppData\Roaming\Antigravity IDE\User\mcp.json"; process = "Antigravity"; allowed = @() },
  @{ name = "Open Interpreter"; path = "C:\Users\ynotf\AppData\Roaming\interpreter\config.json"; process = "Interpreter|Open Interpreter"; allowed = @() },
  @{ name = "Claude Desktop"; path = "C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json"; process = "Claude"; allowed = @() }
)

foreach ($client in $jsonClients) {
  $clientResults = Test-ClientConfig -Name $client.name -Path $client.path -ProcessPattern $client.process -AllowedExtraServers $client.allowed -ForbiddenServers $forbiddenAgentCoreDirect
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
$codexResults = Test-ClientConfig -Name "Codex" -Path $codexConfig -ProcessPattern "^codex$" -AllowedExtraServers $codexAllowedExtras -ForbiddenServers $codexForbidden -TomlConfig
foreach ($item in $codexResults) { $results.Add($item) | Out-Null }

if (Test-Path -LiteralPath $codexConfig) {
  $codexList = & codex mcp list 2>&1
  Add-Result $results "Codex CLI mcp list" ($LASTEXITCODE -eq 0) (($codexList | ForEach-Object { [string]$_ }) -join "`n")
}

$results | ConvertTo-Json -Depth 6
if ($results | Where-Object { -not $_.passed }) { exit 1 }
