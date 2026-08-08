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
  [ValidateSet('Authenticated', 'Unauthenticated')]
  [string]$TestReadiness = 'Authenticated'
)

$ErrorActionPreference = 'Stop'
$exePath = Join-Path $RuntimeRoot 'bin\bifrost-http.exe'
$maintenanceMarker = Join-Path $RuntimeRoot 'state\bifrost-maintenance.marker'

function Test-AuthenticatedGatewayReadiness {
  if ($TestMode) { return $TestReadiness -eq 'Authenticated' }
  try {
    $health = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    if ($health.StatusCode -ne 200) { return $false }
    $vk = [Environment]::GetEnvironmentVariable($VirtualKeyEnvName, 'Process')
    if (-not $vk) { $vk = [Environment]::GetEnvironmentVariable($VirtualKeyEnvName, 'User') }
    if (-not $vk) { return $false }
    $headers = @{ Authorization = "Bearer $vk"; 'Content-Type' = 'application/json'; Accept = 'application/json, text/event-stream' }
    $body = @{ jsonrpc = '2.0'; id = 1; method = 'initialize'; params = @{ protocolVersion = '2025-06-18'; capabilities = @{}; clientInfo = @{ name = 'agentcore-bifrost-start'; version = '1.0.0' } } } | ConvertTo-Json -Depth 6 -Compress
    $response = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/mcp" -Method POST -Headers $headers -Body $body -TimeoutSec 15 -ErrorAction Stop
    if ($response.StatusCode -ne 200) { return $false }
    $content = $response.Content.Trim()
    $candidates = @()
    if ($content -match '(?m)^(?:event|data):') {
      foreach ($event in ($content -split '(?:\r?\n){2,}')) {
        $data = @($event -split "`r?`n" | Where-Object { $_.StartsWith('data:') } | ForEach-Object { $_.Substring(5).TrimStart() })
        if ($data.Count -gt 0) { $candidates += ($data -join "`n") }
      }
    } else {
      $candidates += $content
    }
    foreach ($candidate in $candidates) {
      $payload = $candidate | ConvertFrom-Json -ErrorAction Stop
      $result = $payload.result
      if (($payload.jsonrpc -eq '2.0') -and ($payload.id -eq 1) -and ($null -eq $payload.error) -and
          ($null -ne $result) -and -not [string]::IsNullOrWhiteSpace([string]$result.protocolVersion) -and
          ($null -ne $result.capabilities) -and ($null -ne $result.serverInfo)) {
        return $true
      }
    }
    return $false
  } catch {
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
