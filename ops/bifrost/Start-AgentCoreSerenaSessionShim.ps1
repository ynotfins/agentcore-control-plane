<#
.SYNOPSIS
  Start the AgentCore Serena HTTP session shim (scheduled task or direct launch).
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\serena-shim',
  [string]$TaskName = 'AgentCore-Serena-Session-Shim',
  [string]$TaskPath = '\AgentCore\',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 18090,
  [string]$PythonExe = '',
  [string]$ShimScript = '',
  [switch]$Direct,
  [switch]$ProbeOnly,
  [switch]$TestMode,
  [ValidateSet('Ready', 'NotReady')]
  [string]$TestReadiness = 'Ready'
)

$ErrorActionPreference = 'Stop'

function ConvertTo-AgentCoreCanonicalPath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return '' }
  try { return [IO.Path]::GetFullPath($Path).TrimEnd('\', '/') } catch { return '' }
}

function Test-JsonObjectMap($Value) {
  return ($null -ne $Value) -and (
    ($Value -is [System.Management.Automation.PSCustomObject]) -or
    ($Value -is [System.Collections.IDictionary])
  )
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

function Test-SerenaShimReadiness {
  if ($TestMode) { return $TestReadiness -eq 'Ready' }
  try {
    $headers = @{
      'Content-Type' = 'application/json'
      Accept = 'application/json, text/event-stream'
    }
    $body = @{
      jsonrpc = '2.0'
      id = 1
      method = 'initialize'
      params = @{
        protocolVersion = '2025-06-18'
        capabilities = @{}
        clientInfo = @{ name = 'agentcore-serena-shim-start'; version = '1.0.0' }
      }
    } | ConvertTo-Json -Depth 6 -Compress
    $response = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/mcp" -Method POST `
      -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ($response.StatusCode -ne 200) { return $false }
    $payload = Get-McpJsonRpcResponse $response 1
    if ($null -eq $payload) { return $false }
    if (-not (Test-JsonObjectMap $payload.result.serverInfo)) { return $false }

    $toolsBody = @{ jsonrpc = '2.0'; id = 2; method = 'tools/list'; params = @{} } |
      ConvertTo-Json -Compress
    $toolsResponse = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/mcp" -Method POST `
      -Headers $headers -Body $toolsBody -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ($toolsResponse.StatusCode -ne 200) { return $false }
    $toolsPayload = Get-McpJsonRpcResponse $toolsResponse 2
    if ($null -eq $toolsPayload) { return $false }
    $tools = $toolsPayload.result.tools
    return ($tools -is [System.Array]) -and ($tools.Count -ge 1)
  } catch {
    return $false
  }
}

function Complete-StartWhenReady {
  if (-not (Test-SerenaShimReadiness)) { return $false }
  $maintenanceMarker = Join-Path $RuntimeRoot 'state\serena-shim-maintenance.marker'
  Remove-Item -LiteralPath $maintenanceMarker -Force -ErrorAction SilentlyContinue
  Write-Host "[Start] Serena shim readiness confirmed on ${HostAddress}:${Port}"
  return $true
}

function Wait-ForSerenaShimReadiness {
  param([switch]$CheckScheduledTask)
  for ($i = 0; $i -lt 60; $i++) {
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
  throw "Serena shim did not reach readiness on ${HostAddress}:${Port}"
}

$RepoRoot = ConvertTo-AgentCoreCanonicalPath $RepoRoot
$RuntimeRoot = ConvertTo-AgentCoreCanonicalPath $RuntimeRoot
New-Item -ItemType Directory -Force -Path (Join-Path $RuntimeRoot 'state'), (Join-Path $RuntimeRoot 'logs') | Out-Null

if ($ProbeOnly) {
  if (-not (Test-SerenaShimReadiness)) {
    throw "Serena shim did not reach readiness on ${HostAddress}:${Port}"
  }
  Write-Host "[Start] Serena shim readiness confirmed on ${HostAddress}:${Port}"
  exit 0
}

$maintenanceMarker = Join-Path $RuntimeRoot 'state\serena-shim-maintenance.marker'
Set-Content -LiteralPath $maintenanceMarker -Value 'start_requested' -Encoding utf8

if ($TestMode) {
  if (-not (Complete-StartWhenReady)) { throw 'Serena shim readiness test failed.' }
  exit 0
}

$existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalAddress -in @('127.0.0.1', '::1', '0.0.0.0') }
if ($existing) {
  if (Complete-StartWhenReady) { return }
  throw "Existing listener on ${HostAddress}:${Port} did not pass Serena shim readiness."
}

if (-not $Direct) {
  Start-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction Stop
  Write-Host "[Start] Started scheduled task $TaskPath$TaskName"
  Wait-ForSerenaShimReadiness -CheckScheduledTask
  return
}

$launchScript = Join-Path $PSScriptRoot 'Launch-AgentCoreSerenaSessionShim.ps1'
$args = @(
  '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $launchScript,
  '-RepoRoot', $RepoRoot,
  '-RuntimeRoot', $RuntimeRoot,
  '-HostAddress', $HostAddress,
  '-Port', ([string]$Port)
)
if (-not [string]::IsNullOrWhiteSpace($PythonExe)) {
  $args += @('-PythonExe', $PythonExe)
}
if (-not [string]::IsNullOrWhiteSpace($ShimScript)) {
  $args += @('-ShimScript', $ShimScript)
}
Start-Process -FilePath 'pwsh.exe' -ArgumentList $args -WorkingDirectory $RuntimeRoot -WindowStyle Hidden | Out-Null
Write-Host '[Start] Launched Serena shim via foreground launcher directly'
Wait-ForSerenaShimReadiness
