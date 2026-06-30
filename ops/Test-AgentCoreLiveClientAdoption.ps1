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
  Add-Result $results "$Name required servers present" (($RequiredServers | Where-Object { $servers -notcontains $_ }).Count -eq 0) ($servers -join ", ")
  Add-Result $results "$Name forbidden servers absent" (($ForbiddenServers | Where-Object { $servers -contains $_ }).Count -eq 0) ($servers -join ", ")
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

$requiredCommon = @("global-memory-gateway", "artiforge", "sequential-thinking")
$forbiddenCommon = @("context7", "mem0", "composio", "swarmrecall")
$results = [System.Collections.Generic.List[object]]::new()

$jsonClients = @(
  @{ name = "Cursor"; path = "C:\Users\ynotf\.cursor\mcp.json"; process = "Cursor"; required = @("global-memory-gateway", "artiforge", "sequential-thinking", "serena"); expected = @("arabold-docs", "artiforge", "filesystem", "global-memory-gateway", "obsidian-vault", "playwright", "sequential-thinking", "serena") },
  @{ name = "Open Interpreter"; path = "C:\Users\ynotf\AppData\Roaming\interpreter\config.json"; process = "Interpreter|Open Interpreter"; required = @("global-memory-gateway"); expected = @("arabold-docs", "artiforge", "global-memory-gateway") },
  @{ name = "OpenClaw"; path = "C:\Users\ynotf\.openclaw\openclaw.json"; process = "ClawX|OpenClaw"; required = @("global-memory-gateway", "artiforge", "sequential-thinking", "serena"); expected = @("arabold-docs", "artiforge", "eye2byte", "filesystem", "global-memory-gateway", "obsidian-vault", "playwright", "sequential-thinking", "serena") },
  @{ name = "MiniMax"; path = "C:\Users\ynotf\.minimax\mcp\mcp.json"; process = "MiniMax"; required = @("global-memory-gateway", "artiforge", "sequential-thinking"); expected = @("arabold-docs", "artiforge", "filesystem", "global-memory-gateway", "obsidian-vault", "playwright", "sequential-thinking") },
  @{ name = "Mavis"; path = "C:\Users\ynotf\.mavis\mcp\mcp.json"; process = "Mavis"; required = @("global-memory-gateway", "artiforge", "sequential-thinking"); expected = @("arabold-docs", "artiforge", "filesystem", "global-memory-gateway", "obsidian-vault", "playwright", "sequential-thinking") },
  @{ name = "Antigravity"; path = "C:\Users\ynotf\.gemini\config\mcp_config.json"; process = "Antigravity"; required = @("global-memory-gateway", "artiforge", "sequential-thinking", "serena"); expected = @("arabold-docs", "artiforge", "filesystem", "global-memory-gateway", "obsidian-vault", "playwright", "sequential-thinking", "serena") },
  @{ name = "Antigravity Roaming"; path = "C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json"; process = "Antigravity"; required = @("global-memory-gateway", "artiforge", "sequential-thinking", "serena"); expected = @("arabold-docs", "artiforge", "filesystem", "global-memory-gateway", "obsidian-vault", "playwright", "sequential-thinking", "serena") }
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
  Add-Result $results "Codex gateway configured" ($codexText -match "\[mcp_servers\.global-memory-gateway\]") "global-memory-gateway stanza"
  Add-Result $results "Codex forbidden servers absent" (-not ($codexText -match "\[mcp_servers\.context7\]" -or $codexText -match "\[mcp_servers\.mem0\]" -or $codexText -match "\[mcp_servers\.composio\]")) "checked context7/mem0/composio"
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
