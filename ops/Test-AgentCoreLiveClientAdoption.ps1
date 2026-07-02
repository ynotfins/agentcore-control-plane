param()

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

function Read-JsonFile {
  param([string]$Path)
  Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Get-ServerNames {
  param([object]$Config)
  if ($Config.mcpServers) { return @($Config.mcpServers.PSObject.Properties.Name) }
  if ($Config.servers) { return @($Config.servers.PSObject.Properties.Name) }
  if ($Config.mcp -and $Config.mcp.servers) { return @($Config.mcp.servers.PSObject.Properties.Name) }
  return @()
}

function Test-ClientConfig {
  param(
    [string]$Name,
    [string]$Path,
    [string[]]$RequiredServers,
    [string[]]$ForbiddenServers,
    [string[]]$ExpectedServers
  )

  $results = New-Object System.Collections.Generic.List[object]
  Add-Result $results "$Name config exists" (Test-Path -LiteralPath $Path) $Path
  if (-not (Test-Path -LiteralPath $Path)) {
    return $results
  }

  $config = Read-JsonFile -Path $Path
  $servers = Get-ServerNames -Config $config
  $missingRequired = @($RequiredServers | Where-Object { $servers -notcontains $_ })
  $presentForbidden = @($ForbiddenServers | Where-Object { $servers -contains $_ })
  Add-Result $results "$Name required servers present" ($missingRequired.Count -eq 0) ("missing=" + (($missingRequired -join ", ") -replace "^$", "none") + "; present=" + ($servers -join ", "))
  Add-Result $results "$Name forbidden servers absent" ($presentForbidden.Count -eq 0) ("present=" + (($presentForbidden -join ", ") -replace "^$", "none"))
  if ($ExpectedServers) {
    $missing = @($ExpectedServers | Where-Object { $servers -notcontains $_ })
    $extra = @($servers | Where-Object { $ExpectedServers -notcontains $_ })
    Add-Result $results "$Name exact managed server set" ($missing.Count -eq 0 -and $extra.Count -eq 0) ("missing=" + (($missing -join ", ") -replace "^$", "none") + "; extra=" + (($extra -join ", ") -replace "^$", "none") + "; count=" + $servers.Count)
  }
  return $results
}

function Get-ClientStartState {
  param(
    [string]$ClientName,
    [string]$ProcessPattern,
    [string]$ConfigPath
  )

  $procs = @(Get-Process | Where-Object { $_.ProcessName -match $ProcessPattern } | Sort-Object StartTime)
  if ($procs.Count -eq 0) {
    return [pscustomobject]@{
      running = $false
      detail = "not running"
    }
  }

  $configTime = (Get-Item -LiteralPath $ConfigPath).LastWriteTime
  $latestStart = ($procs | Select-Object -Last 1).StartTime
  return [pscustomobject]@{
    running = $true
    detail = "latest_start=" + $latestStart.ToString("o") + "; config_mtime=" + $configTime.ToString("o") + "; restarted_after_config=" + ($latestStart -gt $configTime)
  }
}

$requiredCommon = @("swarmrecall", "swarmvault", "artiforge", "sequential-thinking")
$forbiddenCommon = @("global-memory-gateway", "context7", "mem0", "mem0_mcp_server", "openmemory", "composio", "hostinger", "Hostinger", "artiforge__codebase_scanner")
$results = [System.Collections.Generic.List[object]]::new()

$jsonClients = @(
  @{ name = "Cursor"; path = "C:\Users\ynotf\.cursor\mcp.json"; process = "Cursor"; required = @("swarmrecall", "swarmvault", "artiforge", "sequential-thinking", "serena"); expected = @("arabold-docs", "artiforge", "filesystem", "obsidian-vault", "playwright", "sequential-thinking", "serena", "context-fabric", "cursor-agent-mcp", "mcp-debugger", "swarmrecall", "swarmvault") },
  @{ name = "Open Interpreter"; path = "C:\Users\ynotf\AppData\Roaming\interpreter\config.json"; process = "Interpreter|Open Interpreter"; required = @("swarmrecall", "swarmvault"); expected = @("arabold-docs", "artiforge", "swarmrecall", "swarmvault", "serena", "sequential-thinking", "cursor-agent-mcp", "context-fabric", "mcp-debugger", "obsidian-vault") },
  @{ name = "OpenClaw"; path = "C:\Users\ynotf\.openclaw\openclaw.json"; process = "ClawX|OpenClaw"; required = @("swarmrecall", "swarmvault", "artiforge", "sequential-thinking", "serena"); expected = @("arabold-docs", "artiforge", "filesystem", "context-fabric", "cursor-agent-mcp", "eye2byte", "mcp-debugger", "obsidian-vault", "playwright", "sequential-thinking", "serena", "swarmrecall", "swarmvault") },
  @{ name = "MiniMax"; path = "C:\Users\ynotf\.minimax\mcp\mcp.json"; process = "MiniMax"; required = @("swarmrecall", "swarmvault", "artiforge", "sequential-thinking"); expected = @("arabold-docs", "artiforge", "cursor-agent-mcp", "filesystem", "mcp-debugger", "obsidian-vault", "playwright", "serena", "sequential-thinking", "swarmrecall", "swarmvault", "context-fabric") },
  @{ name = "Mavis"; path = "C:\Users\ynotf\.mavis\mcp\mcp.json"; process = "Mavis"; required = @("swarmrecall", "swarmvault", "artiforge", "sequential-thinking"); expected = @("arabold-docs", "artiforge", "cursor-agent-mcp", "filesystem", "mcp-debugger", "obsidian-vault", "playwright", "serena", "sequential-thinking", "swarmrecall", "swarmvault", "context-fabric") },
  @{ name = "Antigravity"; path = "C:\Users\ynotf\.gemini\config\mcp_config.json"; process = "Antigravity"; required = @("swarmrecall", "swarmvault", "artiforge", "sequential-thinking", "serena"); expected = @("arabold-docs", "serena", "sequential-thinking", "cursor-agent-mcp", "context-fabric", "mcp-debugger", "artiforge", "obsidian-vault", "swarmrecall", "swarmvault", "filesystem", "playwright", "notebooks", "visualization") },
  @{ name = "Antigravity Roaming"; path = "C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json"; process = "Antigravity"; required = @("swarmrecall", "swarmvault", "artiforge", "sequential-thinking", "serena"); expected = @("arabold-docs", "serena", "sequential-thinking", "cursor-agent-mcp", "context-fabric", "mcp-debugger", "artiforge", "obsidian-vault", "swarmrecall", "swarmvault", "filesystem", "playwright") }
)

foreach ($client in $jsonClients) {
  $clientResults = Test-ClientConfig -Name $client.name -Path $client.path -RequiredServers $client.required -ForbiddenServers $forbiddenCommon -ExpectedServers $client.expected
  foreach ($item in $clientResults) { $results.Add($item) | Out-Null }
  if (Test-Path -LiteralPath $client.path) {
    $startState = Get-ClientStartState -ClientName $client.name -ProcessPattern $client.process -ConfigPath $client.path
    Add-Result $results ($client.name + " live restart after config") ($startState.running -and $startState.detail -match "restarted_after_config=True") $startState.detail
  }
}

$codexConfig = "C:\Users\ynotf\.codex\config.toml"
Add-Result $results "Codex config exists" (Test-Path -LiteralPath $codexConfig) $codexConfig
if (Test-Path -LiteralPath $codexConfig) {
  $codexText = Get-Content -LiteralPath $codexConfig -Raw
  Add-Result $results "Codex swarm memory configured" (($codexText -match "\[mcp_servers\.swarmrecall\]") -and ($codexText -match "\[mcp_servers\.swarmvault\]")) "swarmrecall + swarmvault stanzas"
  Add-Result $results "Codex forbidden servers absent" (-not ($codexText -match "\[mcp_servers\.context7\]" -or $codexText -match "\[mcp_servers\.mem0\]" -or $codexText -match "\[mcp_servers\.composio\]" -or $codexText -match "\[mcp_servers\.global-memory-gateway\]")) "checked context7/mem0/composio/global-memory-gateway"
  $codexList = & codex mcp list 2>&1
  Add-Result $results "Codex CLI mcp list" ($LASTEXITCODE -eq 0) (($codexList | ForEach-Object { [string]$_ }) -join "`n")
  $codexState = Get-ClientStartState -ClientName "Codex" -ProcessPattern "^Codex$" -ConfigPath $codexConfig
  Add-Result $results "Codex live restart after config" ($codexState.running -and $codexState.detail -match "restarted_after_config=True") $codexState.detail
}

$manifestPaths = @(
  "C:\Users\ynotf\.minimax\mcp\manifest.json",
  "C:\Users\ynotf\.mavis\mcp\manifest.json"
)
foreach ($manifestPath in $manifestPaths) {
  if (-not (Test-Path -LiteralPath $manifestPath)) {
    Add-Result $results ("Manifest exists " + $manifestPath) $false "missing"
    continue
  }
  $text = Get-Content -LiteralPath $manifestPath -Raw
  Add-Result $results ("Manifest banned entries absent " + $manifestPath) (-not ($text -match '"context7"' -or $text -match '"mem0"' -or $text -match '"composio"')) "checked context7/mem0/composio"
}

$results | ConvertTo-Json -Depth 6
if ($results | Where-Object { -not $_.passed }) { exit 1 }
