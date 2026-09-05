<#
.SYNOPSIS
  Health-test the AgentCore Bifrost MCP Gateway without printing secrets.
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$BaseUrl = 'http://127.0.0.1:8080',
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$CursorMcpPath = 'C:\Users\ynotf\.cursor\mcp.json',
  [string]$ExpectedVersion = 'v2.0.0',
  [string]$TaskPath = '\AgentCore\',
  [string]$GatewayTaskName = 'AgentCore-Bifrost-Gateway',
  [string]$WatchdogTaskName = 'AgentCore-Bifrost-Watchdog',
  [long]$MaxActiveLogBytes = 52428800,
  [switch]$RequireWatchdogEnabled,
  [switch]$RequireOpenRouterMcpHealthy,
  [switch]$RequireSemanticCacheHealthy,
  [switch]$TestMode,
  [switch]$TestScheduledTasksOnly,
  [string]$TestScheduledTaskStatePath = ''
)

$ErrorActionPreference = 'Stop'
$failed = $false

function Assert-True([bool]$Condition, [string]$Label) {
  if ($Condition) {
    Write-Host "PASS  $Label"
  } else {
    Write-Host "FAIL  $Label"
    $script:failed = $true
  }
}

function Assert-OrWarn([bool]$Condition, [string]$Label, [bool]$Required) {
  if ($Condition) {
    Write-Host "PASS  $Label"
  } elseif ($Required) {
    Write-Host "FAIL  $Label"
    $script:failed = $true
  } else {
    Write-Host "WARN  $Label"
  }
}

function Invoke-McpJson([string]$Method, [hashtable]$Params, [int]$Id, [hashtable]$Headers) {
  $body = @{
    jsonrpc = '2.0'
    id      = $Id
    method  = $Method
    params  = $Params
  } | ConvertTo-Json -Depth 30 -Compress
  $response = Invoke-WebRequest -Uri "$BaseUrl/mcp" -Method POST -Headers $Headers -Body $body -UseBasicParsing -TimeoutSec 60
  $raw = [string]$response.Content
  $chunks = @()
  foreach ($line in ($raw -split "`n")) {
    if ($line.StartsWith('data: ')) {
      $chunks += $line.Substring(6).Trim()
    }
  }
  if ($chunks.Count -gt 0) {
    return $chunks[-1] | ConvertFrom-Json -Depth 50
  }
  return $raw | ConvertFrom-Json -Depth 50
}

function Get-McpTextContent($Payload) {
  if ($null -eq $Payload.result -or $null -eq $Payload.result.content) { return '' }
  return (@($Payload.result.content | Where-Object { $_.type -eq 'text' } | ForEach-Object { [string]$_.text }) -join "`n")
}

function Get-ValidatorScheduledTask([string]$Name) {
  if ($TestMode) {
    if ([string]::IsNullOrWhiteSpace($TestScheduledTaskStatePath) -or
        -not (Test-Path -LiteralPath $TestScheduledTaskStatePath -PathType Leaf)) {
      throw 'VALIDATOR_TEST_SCHEDULED_TASK_STATE_REQUIRED'
    }
    $state = Get-Content -Raw -LiteralPath $TestScheduledTaskStatePath | ConvertFrom-Json -Depth 20 -ErrorAction Stop
    $key = if ($Name -eq $GatewayTaskName) { 'gateway' } else { 'watchdog' }
    $task = $state.$key
    if ($null -eq $task) {
      throw "scheduled task model missing: $TaskPath$Name"
    }
    return $task
  }
  return Get-ScheduledTask -TaskPath $TaskPath -TaskName $Name -ErrorAction Stop
}

function Convert-TaskDurationToSeconds($Value) {
  if ($null -eq $Value) { return $null }
  if ($Value -is [timespan]) { return [int][math]::Round($Value.TotalSeconds) }
  $text = [string]$Value
  if ([string]::IsNullOrWhiteSpace($text)) { return $null }
  if ($text -match '^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$') {
    $hours = if ($Matches[1]) { [int]$Matches[1] } else { 0 }
    $minutes = if ($Matches[2]) { [int]$Matches[2] } else { 0 }
    $seconds = if ($Matches[3]) { [int]$Matches[3] } else { 0 }
    return [int]([timespan]::new($hours, $minutes, $seconds)).TotalSeconds
  }
  try { return [int][math]::Round(([timespan]::Parse($text)).TotalSeconds) } catch { return $null }
}

function Get-TaskRepetitionIntervalSeconds($Task) {
  foreach ($trigger in @($Task.Triggers)) {
    if ($null -eq $trigger -or $null -eq $trigger.Repetition) { continue }
    if ($null -ne $trigger.Repetition.IntervalSeconds) {
      return [int]$trigger.Repetition.IntervalSeconds
    }
    $seconds = Convert-TaskDurationToSeconds $trigger.Repetition.Interval
    if ($null -ne $seconds) { return $seconds }
  }
  return $null
}

function Test-GatewayScheduledTask {
  try {
    $gatewayTask = Get-ValidatorScheduledTask $GatewayTaskName
    Assert-True $true "gateway scheduled task registered: $TaskPath$GatewayTaskName"
    Assert-True ([bool]$gatewayTask.Settings.Enabled) 'gateway scheduled task enabled'
    Assert-True ([bool]$gatewayTask.Settings.Hidden) 'gateway scheduled task Hidden setting is true; rerun the installer elevated to replace stale visible tasks'
    $gatewayArguments = [string]$gatewayTask.Actions.Arguments
    Assert-True ($gatewayArguments -match '-WindowStyle\s+Hidden') 'gateway scheduled task uses hidden PowerShell'
    Assert-True ($gatewayArguments -match '-NonInteractive') 'gateway scheduled task is non-interactive'
  } catch {
    Write-Host "FAIL  gateway scheduled task validation: $($_.Exception.Message)"
    $script:failed = $true
  }
}

function Test-WatchdogScheduledTask {
  try {
    $watchdogTask = Get-ValidatorScheduledTask $WatchdogTaskName
    Assert-OrWarn $true "watchdog scheduled task registered: $TaskPath$WatchdogTaskName" $RequireWatchdogEnabled.IsPresent
    Assert-OrWarn ([bool]$watchdogTask.Settings.Enabled) 'watchdog scheduled task enabled; rerun the installer elevated to replace stale disabled tasks' $RequireWatchdogEnabled.IsPresent
    Assert-OrWarn ([bool]$watchdogTask.Settings.Hidden) 'watchdog scheduled task Hidden setting is true; rerun the installer elevated to replace stale visible tasks' $RequireWatchdogEnabled.IsPresent
    $watchdogArguments = [string]$watchdogTask.Actions.Arguments
    Assert-OrWarn ($watchdogArguments -match '-WindowStyle\s+Hidden') 'watchdog scheduled task uses hidden PowerShell' $RequireWatchdogEnabled.IsPresent
    Assert-OrWarn ($watchdogArguments -match '-NonInteractive') 'watchdog scheduled task is non-interactive' $RequireWatchdogEnabled.IsPresent
    Assert-OrWarn ($watchdogArguments -match '-FailureThreshold\s+2') 'watchdog uses debounced failure threshold 2; rerun the installer elevated to replace stale task arguments' $RequireWatchdogEnabled.IsPresent
    Assert-OrWarn ([string]$watchdogTask.Settings.MultipleInstances -eq 'IgnoreNew') 'watchdog multiple-instance policy is IgnoreNew; rerun the installer elevated to replace stale overlap-prone settings' $RequireWatchdogEnabled.IsPresent
    Assert-OrWarn ((Convert-TaskDurationToSeconds $watchdogTask.Settings.ExecutionTimeLimit) -eq 60) 'watchdog execution time limit is 60 seconds; rerun the installer elevated to replace stale unbounded settings' $RequireWatchdogEnabled.IsPresent
    Assert-OrWarn ((Get-TaskRepetitionIntervalSeconds $watchdogTask) -eq 60) 'watchdog repetition interval is 60 seconds; rerun the installer elevated to replace stale trigger cadence' $RequireWatchdogEnabled.IsPresent
    $watchdogUser = [string]$watchdogTask.Principal.UserId
    Assert-OrWarn ($watchdogUser -in @('SYSTEM', 'NT AUTHORITY\SYSTEM')) 'watchdog runs under SYSTEM/service context; rerun the installer elevated to replace stale user-bound tasks' $RequireWatchdogEnabled.IsPresent
    Assert-OrWarn ([string]$watchdogTask.Principal.LogonType -eq 'ServiceAccount') 'watchdog logon type is ServiceAccount; rerun the installer elevated to replace stale interactive tasks' $RequireWatchdogEnabled.IsPresent
    Assert-OrWarn ([string]$watchdogTask.Principal.RunLevel -eq 'Highest') 'watchdog run level is Highest; rerun the installer elevated to replace stale limited tasks' $RequireWatchdogEnabled.IsPresent
  } catch {
    Assert-OrWarn $false "watchdog scheduled task validation: $($_.Exception.Message); rerun the installer elevated to register the managed watchdog task" $RequireWatchdogEnabled.IsPresent
  }
}

if ($TestScheduledTasksOnly) {
  Test-GatewayScheduledTask
  Test-WatchdogScheduledTask
  if ($failed) {
    Write-Host 'RESULT: FAILED'
    exit 1
  }
  Write-Host 'RESULT: PASSED'
  exit 0
}

$configPath = Join-Path $RuntimeRoot 'config.json'
Assert-True (Test-Path -LiteralPath $configPath) "config.json exists at $configPath"
Assert-True (Test-Path -LiteralPath (Join-Path $RuntimeRoot 'bin\bifrost-http.exe')) 'bifrost-http.exe present'

if (Test-Path -LiteralPath $configPath) {
  $raw = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8
  Assert-True ($raw -notmatch 'sk-proj-|sk-ant-|ghp_') 'config.json has no obvious secret literals'
  Assert-True ($raw -match 'env\.BIFROST_MCP_VIRTUAL_KEY') 'builder VK uses env.BIFROST_MCP_VIRTUAL_KEY'
  Assert-True ($raw -match '"mcp_disable_auto_tool_inject"\s*:\s*true') 'mcp_disable_auto_tool_inject true'
}

try {
  $versionResponse = Invoke-RestMethod -Uri "$BaseUrl/api/version" -TimeoutSec 5
  $versionText = if ($versionResponse -is [string]) { $versionResponse } else { [string]$versionResponse.version }
  Assert-True ($versionText -eq $ExpectedVersion) "Bifrost version is $ExpectedVersion"
} catch {
  Write-Host "FAIL  Bifrost version check: $($_.Exception.Message)"
  $failed = $true
}

$activeLog = Join-Path $RuntimeRoot 'logs\bifrost-gateway.stdout.log'
if (Test-Path -LiteralPath $activeLog) {
  $activeLogLength = (Get-Item -LiteralPath $activeLog).Length
  Assert-True ($activeLogLength -le $MaxActiveLogBytes) "active stdout log is bounded ($activeLogLength bytes)"
}

Test-GatewayScheduledTask
Test-WatchdogScheduledTask

$validate = Join-Path $RepoRoot 'scripts\bifrost\validate_contracts.py'
if (Test-Path -LiteralPath $validate) {
  $pythonCmd = $null
  $repoPython = Join-Path $RepoRoot 'scripts\.venv\Scripts\python.exe'
  if (Test-Path -LiteralPath $repoPython) {
    $pythonCmd = $repoPython
  } else {
    foreach ($c in @('py', 'python', 'python3')) {
      $cmd = Get-Command $c -ErrorAction SilentlyContinue
      if ($cmd) { $pythonCmd = $cmd.Source; break }
    }
  }
  if (-not $pythonCmd -and (Test-Path 'C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe')) {
    $pythonCmd = 'C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe'
  }
  if (-not $pythonCmd) { throw 'Python interpreter not found for validate_contracts.py' }
  & $pythonCmd $validate | Out-Host
  Assert-True ($LASTEXITCODE -eq 0) 'validate_contracts.py'
}

$listening = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
$netstatListening = $false
try {
  $netstatListening = $null -ne (netstat -ano | Select-String -Pattern '127\.0\.0\.1:8080\s+0\.0\.0\.0:0\s+LISTENING')
} catch {
  $netstatListening = $false
}
Assert-True (($null -ne $listening) -or $netstatListening) 'TCP 127.0.0.1:8080 listening (Get-NetTCPConnection or netstat)'

try {
  $health = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -TimeoutSec 5
  Assert-True ($health.StatusCode -ge 200 -and $health.StatusCode -lt 500) "/health HTTP $($health.StatusCode)"
} catch {
  Write-Host "FAIL  /health request: $($_.Exception.Message)"
  $failed = $true
}

# Confirm VK env exists without printing value
$vk = [Environment]::GetEnvironmentVariable('BIFROST_MCP_VIRTUAL_KEY', 'User')
if (-not $vk) { $vk = [Environment]::GetEnvironmentVariable('BIFROST_MCP_VIRTUAL_KEY', 'Process') }
Assert-True (-not [string]::IsNullOrWhiteSpace($vk)) 'BIFROST_MCP_VIRTUAL_KEY is set (value not shown)'

if (-not [string]::IsNullOrWhiteSpace($vk)) {
  try {
    $headers = @{
      'x-bf-vk'      = $vk
      'Content-Type' = 'application/json'
      Accept         = 'application/json, text/event-stream'
    }
    $init = Invoke-McpJson -Method 'initialize' -Params @{
      protocolVersion = '2025-06-18'
      capabilities    = @{}
      clientInfo      = @{ name = 'agentcore-gateway-validator'; version = '1.0' }
    } -Id 1001 -Headers $headers
    Assert-True ($null -ne $init.result.serverInfo) 'authenticated MCP initialize'

    try {
      Invoke-WebRequest -Uri "$BaseUrl/mcp" -Method POST -Headers $headers -Body '{"jsonrpc":"2.0","method":"notifications/initialized"}' -UseBasicParsing -TimeoutSec 30 | Out-Null
    } catch {
      # Some streamable HTTP implementations do not require the notification for stateless requests.
    }

    $tools = Invoke-McpJson -Method 'tools/list' -Params @{} -Id 1002 -Headers $headers
    $toolNames = @($tools.result.tools | ForEach-Object { $_.name })
    Assert-True ($toolNames.Count -gt 0) "authenticated MCP tools/list returned $($toolNames.Count) tools"

    $registryPath = Join-Path $RepoRoot 'contracts\bifrost-upstream-mcp-registry.json'
    if (-not (Test-Path -LiteralPath $registryPath)) {
      throw "Missing MCP registry: $registryPath"
    }
    $registry = Get-Content -LiteralPath $registryPath -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100
    $builderServerIds = @($registry.capability_profiles.builder.allowed_server_ids)
    $activeBuilderServers = @(
      $registry.servers.PSObject.Properties |
        Where-Object {
          $_.Name -in $builderServerIds -and
          $_.Value.enabled -eq $true -and
          $_.Value.status -eq 'active'
        }
    )
    Assert-True ($activeBuilderServers.Count -gt 0) 'builder profile resolves at least one active MCP server'
    $codeModeServers = @($activeBuilderServers | Where-Object { $_.Value.is_code_mode_client -eq $true })
    if ($codeModeServers.Count -gt 0) {
      foreach ($metaTool in @('listToolFiles', 'readToolFile', 'getToolDocs', 'executeToolCode')) {
        Assert-True ($toolNames -contains $metaTool) "Code Mode meta-tool present: $metaTool"
      }
      $toolFiles = Invoke-McpJson -Method 'tools/call' -Params @{
        name      = 'listToolFiles'
        arguments = @{}
      } -Id 1003 -Headers $headers
      $toolFileText = Get-McpTextContent $toolFiles
      Assert-True ($toolFileText -match 'morph_mcp\.pyi') 'Code Mode exposes Morph tool file'
      Assert-True ($toolFileText -match 'playwright\.pyi') 'Code Mode exposes Playwright tool file'
      $morphToolFile = Invoke-McpJson -Method 'tools/call' -Params @{
        name      = 'readToolFile'
        arguments = @{ fileName = 'servers/morph_mcp.pyi' }
      } -Id 1004 -Headers $headers
      Assert-True ((Get-McpTextContent $morphToolFile) -match 'def edit_file\(') 'Code Mode Morph edit_file signature readable'
      $playwrightToolFile = Invoke-McpJson -Method 'tools/call' -Params @{
        name      = 'readToolFile'
        arguments = @{ fileName = 'servers/playwright.pyi' }
      } -Id 1005 -Headers $headers
      Assert-True ((Get-McpTextContent $playwrightToolFile) -match 'def browser_') 'Code Mode Playwright signatures readable'
    }
    foreach ($serverProp in $activeBuilderServers) {
      if ($serverProp.Value.is_code_mode_client -eq $true) {
        Write-Host "PASS  contract-active builder MCP client is Code Mode hidden: $($serverProp.Value.bifrost_client_name)"
        continue
      }
      $prefix = ([string]$serverProp.Value.bifrost_client_name) + '-'
      Assert-True (@($toolNames | Where-Object { $_ -like "$prefix*" }).Count -gt 0) "contract-active builder MCP tool prefix present: $prefix"
    }
    foreach ($pattern in @('swarm', 'postgres', 'psql', 'whole_drive', 'bifrost_admin')) {
      Assert-True (@($toolNames | Where-Object { $_ -match $pattern }).Count -eq 0) "forbidden MCP tool pattern absent: $pattern"
    }
  } catch {
    Write-Host "FAIL  authenticated MCP protocol validation: $($_.Exception.Message)"
    $failed = $true
  }
}

if (Test-Path -LiteralPath $CursorMcpPath) {
  try {
    $cursorRaw = Get-Content -LiteralPath $CursorMcpPath -Raw -Encoding UTF8
    $cursorJson = $cursorRaw | ConvertFrom-Json -Depth 20
    $serverNames = @($cursorJson.mcpServers.PSObject.Properties.Name)
    Assert-True ($serverNames.Count -eq 1) 'Cursor global MCP has exactly one server entry'
    Assert-True ($serverNames -contains 'agentcore-gateway') 'Cursor global MCP contains agentcore-gateway'
    Assert-True ($serverNames -notcontains 'MCP_DOCKER') 'Cursor global MCP does not contain MCP_DOCKER'
    Assert-True ($cursorJson.mcpServers.'agentcore-gateway'.url -eq "$BaseUrl/mcp") 'Cursor global MCP endpoint matches gateway'
    Assert-True ($cursorRaw -match '\$\{env:BIFROST_MCP_VIRTUAL_KEY\}') 'Cursor global MCP uses env placeholder'
    Assert-True ($cursorRaw -notmatch 'sk-[A-Za-z0-9_-]{20,}') 'Cursor global MCP has no obvious secret literal'
  } catch {
    Write-Host "FAIL  Cursor MCP config validation: $($_.Exception.Message)"
    $failed = $true
  }
} else {
  Write-Host "FAIL  Cursor MCP config missing: $CursorMcpPath"
  $failed = $true
}

$adminKey = [Environment]::GetEnvironmentVariable('BIFROST_ADMIN_KEY', 'Process')
if (-not $adminKey) { $adminKey = [Environment]::GetEnvironmentVariable('BIFROST_ADMIN_KEY', 'User') }
if ($adminKey) {
  $adminHeaders = @{ Authorization = "Bearer $adminKey" }
  try {
    $clients = Invoke-RestMethod -Uri "$BaseUrl/api/mcp/clients" -Headers $adminHeaders -TimeoutSec 10
    $openrouterClients = @($clients.clients | Where-Object { $_.config.name -eq 'openrouter' })
    Assert-OrWarn ($openrouterClients.Count -eq 1) 'OpenRouter MCP client registered exactly once' $RequireOpenRouterMcpHealthy.IsPresent
    if ($openrouterClients.Count -eq 1) {
      $openrouterState = [string]$openrouterClients[0].state
      Assert-OrWarn ($openrouterState -notin @('unstable', 'error', 'failed')) "OpenRouter MCP not degraded (state=$openrouterState)" $RequireOpenRouterMcpHealthy.IsPresent
    }
  } catch {
    Assert-OrWarn $false "OpenRouter MCP admin check: $($_.Exception.Message)" $RequireOpenRouterMcpHealthy.IsPresent
  }

  try {
    $plugins = Invoke-RestMethod -Uri "$BaseUrl/api/plugins" -Headers $adminHeaders -TimeoutSec 10
    $semanticCache = @($plugins.plugins | Where-Object { $_.name -eq 'semantic_cache' -or $_.actualName -eq 'semantic_cache' })
    Assert-OrWarn ($semanticCache.Count -eq 1) 'semantic_cache plugin registered exactly once' $RequireSemanticCacheHealthy.IsPresent
    if ($semanticCache.Count -eq 1) {
      $semanticStatus = [string]$semanticCache[0].status.status
      Assert-OrWarn ($semanticStatus -notin @('error', 'failed')) "semantic_cache plugin not degraded (status=$semanticStatus)" $RequireSemanticCacheHealthy.IsPresent
    }
  } catch {
    Assert-OrWarn $false "semantic_cache admin check: $($_.Exception.Message)" $RequireSemanticCacheHealthy.IsPresent
  }
} else {
  Assert-OrWarn $false 'BIFROST_ADMIN_KEY is set for admin health checks (value not shown)' ($RequireOpenRouterMcpHealthy.IsPresent -or $RequireSemanticCacheHealthy.IsPresent)
}

if ($failed) {
  Write-Host 'RESULT: FAILED'
  exit 1
}
Write-Host 'RESULT: PASSED'
exit 0
