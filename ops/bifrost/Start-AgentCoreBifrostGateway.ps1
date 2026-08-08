<#
.SYNOPSIS
  Start the AgentCore Bifrost MCP Gateway process (or scheduled task).
#>
[CmdletBinding()]
param(
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$TaskName = 'AgentCore-Bifrost-Gateway',
  [string]$TaskPath = '\AgentCore\',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 8080,
  [string]$VirtualKeyEnvName = 'BIFROST_MCP_VIRTUAL_KEY',
  [switch]$Direct,
  [switch]$ProbeOnly,
  [switch]$TestMode,
  [switch]$TestUseHttpReadiness,
  [ValidateSet('Authenticated', 'Unauthenticated')]
  [string]$TestReadiness = 'Authenticated'
)

$ErrorActionPreference = 'Stop'
$exePath = Join-Path $RuntimeRoot 'bin\bifrost-http.exe'
$maintenanceMarker = Join-Path $RuntimeRoot 'state\bifrost-maintenance.marker'
$supportedProtocolVersions = @('2024-11-05', '2025-03-26', '2025-06-18')

function Test-JsonObjectMap($Value) {
  return ($null -ne $Value) -and (
    ($Value -is [System.Management.Automation.PSCustomObject]) -or
    ($Value -is [System.Collections.IDictionary])
  )
}

function Test-NonEmptyJsonString($Value) {
  return ($Value -is [string]) -and -not [string]::IsNullOrWhiteSpace($Value)
}

function Get-McpJsonRpcResponse($Response, [int]$ExpectedId) {
  $content = ([string]$Response.Content).Trim()
  $candidates = [System.Collections.Generic.List[string]]::new()
  if ($content -match '(?m)^(?:event|data):') {
    foreach ($event in ($content -split '(?:\r?\n){2,}')) {
      $dataLines = [System.Collections.Generic.List[string]]::new()
      foreach ($line in ($event -split '\r?\n')) {
        if ($line -match '^data:\s?(.*)$') { $dataLines.Add($Matches[1]) }
      }
      if ($dataLines.Count -gt 0) { $candidates.Add(($dataLines -join "`n")) }
    }
  } elseif (-not [string]::IsNullOrWhiteSpace($content)) {
    $candidates.Add($content)
  }

  foreach ($candidate in $candidates) {
    try { $payload = $candidate | ConvertFrom-Json -ErrorAction Stop } catch { continue }
    if (($payload.jsonrpc -eq '2.0') -and ($payload.id -eq $ExpectedId) -and
        ($null -eq $payload.error) -and (Test-JsonObjectMap $payload.result)) {
      return $payload
    }
  }
  return $null
}

function Test-AuthenticatedGatewayReadiness {
  if ($TestMode -and -not $TestUseHttpReadiness) { return $TestReadiness -eq 'Authenticated' }
  $readinessStage = 'health'
  try {
    $health = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    if ($health.StatusCode -ne 200) {
      if ($TestMode) { Write-Host 'READINESS_TEST_REJECT stage=health' }
      return $false
    }
    $vk = [Environment]::GetEnvironmentVariable($VirtualKeyEnvName, 'Process')
    if (-not $vk) { $vk = [Environment]::GetEnvironmentVariable($VirtualKeyEnvName, 'User') }
    if (-not $vk) { return $false }
    $headers = @{ Authorization = "Bearer $vk"; 'Content-Type' = 'application/json'; Accept = 'application/json, text/event-stream' }
    $body = @{ jsonrpc = '2.0'; id = 1; method = 'initialize'; params = @{ protocolVersion = '2025-06-18'; capabilities = @{}; clientInfo = @{ name = 'agentcore-bifrost-start'; version = '1.0.0' } } } | ConvertTo-Json -Depth 6 -Compress
    $readinessStage = 'initialize'
    $response = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/mcp" -Method POST -Headers $headers -Body $body -TimeoutSec 15 -ErrorAction Stop
    if ($response.StatusCode -ne 200) {
      if ($TestMode) { Write-Host 'READINESS_TEST_REJECT stage=initialize_status' }
      return $false
    }
    $initializePayload = Get-McpJsonRpcResponse $response 1
    if ($null -eq $initializePayload) {
      if ($TestMode) { Write-Host 'READINESS_TEST_REJECT stage=initialize_rpc' }
      return $false
    }
    $result = $initializePayload.result
    $shapeChecks = [ordered]@{
      protocol_string = Test-NonEmptyJsonString $result.protocolVersion
      protocol_supported = $supportedProtocolVersions -contains $result.protocolVersion
      capabilities_object = Test-JsonObjectMap $result.capabilities
      server_info_object = Test-JsonObjectMap $result.serverInfo
      server_name = Test-NonEmptyJsonString $result.serverInfo.name
      server_version = Test-NonEmptyJsonString $result.serverInfo.version
    }
    if ($shapeChecks.Values -contains $false) {
      if ($TestMode) { Write-Host ('READINESS_TEST_REJECT stage=initialize_shape checks=' + ($shapeChecks | ConvertTo-Json -Compress)) }
      return $false
    }

    $negotiatedProtocolVersion = [string]$result.protocolVersion
    $sessionId = ''
    $sessionHeader = $response.Headers.GetEnumerator() |
      Where-Object { $_.Key -ieq 'Mcp-Session-Id' } |
      Select-Object -First 1
    if ($null -ne $sessionHeader) {
      $sessionId = [string]($sessionHeader.Value | Select-Object -First 1)
    }
    $sessionHeaders = @{
      Authorization = "Bearer $vk"
      'Content-Type' = 'application/json'
      Accept = 'application/json, text/event-stream'
      'MCP-Protocol-Version' = $negotiatedProtocolVersion
    }
    if (-not [string]::IsNullOrWhiteSpace($sessionId)) {
      $sessionHeaders['Mcp-Session-Id'] = $sessionId
    }

    $initializedBody = @{ jsonrpc = '2.0'; method = 'notifications/initialized' } | ConvertTo-Json -Compress
    $readinessStage = 'notifications_initialized'
    $initializedResponse = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/mcp" -Method POST -Headers $sessionHeaders -Body $initializedBody -TimeoutSec 15 -ErrorAction Stop
    if ($initializedResponse.StatusCode -ne 202) { return $false }

    $toolsListBody = @{ jsonrpc = '2.0'; id = 2; method = 'tools/list'; params = @{} } | ConvertTo-Json -Depth 4 -Compress
    $readinessStage = 'tools_list'
    $toolsListResponse = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/mcp" -Method POST -Headers $sessionHeaders -Body $toolsListBody -TimeoutSec 15 -ErrorAction Stop
    if ($toolsListResponse.StatusCode -ne 200) { return $false }
    $toolsListPayload = Get-McpJsonRpcResponse $toolsListResponse 2
    if ($null -eq $toolsListPayload) { return $false }
    $toolsProperty = $toolsListPayload.result.PSObject.Properties['tools']
    if (($null -eq $toolsProperty) -or -not ($toolsProperty.Value -is [System.Array])) { return $false }
    return $true
  } catch {
    if ($TestMode) { Write-Host "READINESS_TEST_FAILURE stage=$readinessStage type=$($_.Exception.GetType().Name)" }
    return $false
  }
}

function Complete-StartWhenReady {
  if (-not (Test-AuthenticatedGatewayReadiness)) { return $false }
  Remove-Item -LiteralPath $maintenanceMarker -Force -ErrorAction SilentlyContinue
  Write-Host "[Start] Authenticated gateway readiness confirmed on ${HostAddress}:${Port}"
  return $true
}

function Wait-ForGatewayReadiness {
  param([switch]$CheckScheduledTask)

  for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 2
    if (Complete-StartWhenReady) { return }
    if ($CheckScheduledTask) {
      $task = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction SilentlyContinue
      if ($task -and $task.State -notin @('Running', 'Ready')) {
        $info = Get-ScheduledTaskInfo -TaskPath $TaskPath -TaskName $TaskName -ErrorAction SilentlyContinue
        throw "Scheduled task entered state $($task.State); last result $($info.LastTaskResult)"
      }
    }
  }
  throw "Gateway did not reach authenticated readiness on ${HostAddress}:${Port}"
}

if (-not $TestMode -and -not (Test-Path -LiteralPath $exePath)) {
  throw "Missing binary: $exePath"
}

if ($ProbeOnly) {
  if (-not (Test-AuthenticatedGatewayReadiness)) { throw "Gateway did not reach authenticated readiness on ${HostAddress}:${Port}" }
  Write-Host "[Start] Authenticated gateway readiness confirmed on ${HostAddress}:${Port}"
  exit 0
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $maintenanceMarker) | Out-Null
Set-Content -LiteralPath $maintenanceMarker -Value 'start_requested' -Encoding utf8

if ($TestMode) {
  if (-not (Complete-StartWhenReady)) { throw 'Authenticated gateway readiness test failed.' }
  exit 0
}

$existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalAddress -in @('127.0.0.1', '::1', '0.0.0.0') }
if ($existing) {
  if (Complete-StartWhenReady) { return }
  throw "Existing listener on ${HostAddress}:${Port} did not pass authenticated gateway readiness."
}

if (-not $Direct) {
  Start-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
  Write-Host "[Start] Started scheduled task $TaskPath$TaskName"
  Wait-ForGatewayReadiness -CheckScheduledTask
  return
}

$launchScript = Join-Path $PSScriptRoot 'Launch-AgentCoreBifrostGateway.ps1'
Start-Process -FilePath 'pwsh.exe' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $launchScript, '-RuntimeRoot', $RuntimeRoot, '-HostAddress', $HostAddress, '-Port', [string]$Port) -WorkingDirectory $RuntimeRoot -WindowStyle Hidden | Out-Null
Write-Host '[Start] Launched Bifrost via foreground launcher directly'
Wait-ForGatewayReadiness
