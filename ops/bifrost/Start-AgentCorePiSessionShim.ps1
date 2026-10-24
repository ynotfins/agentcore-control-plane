# Direct-launch only. Do not register or start a Windows scheduled task.
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\pi-shim',
  [string]$HostAddress = '127.0.0.1',
  [int]$Port = 18091,
  [string]$PythonExe = '',
  [string]$ShimScript = '',
  [switch]$ProbeOnly
)
$ErrorActionPreference = 'Stop'
function ConvertTo-AgentCoreCanonicalPath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return '' }
  try { return [IO.Path]::GetFullPath($Path).TrimEnd('\', '/') } catch { return '' }
}
function Test-JsonObjectMap($Value) {
  return ($null -ne $Value) -and (($Value -is [System.Management.Automation.PSCustomObject]) -or ($Value -is [System.Collections.IDictionary]))
}
function Get-McpJsonRpcResponse($Response, [int]$ExpectedId) {
  $content = ([string]$Response.Content).Trim()
  $candidates = [System.Collections.Generic.List[string]]::new()
  if (-not [string]::IsNullOrWhiteSpace($content)) { $candidates.Add($content) }
  foreach ($candidate in $candidates) {
    try { $payload = $candidate | ConvertFrom-Json -ErrorAction Stop } catch { continue }
    if (($payload.jsonrpc -eq '2.0') -and ($payload.id -eq $ExpectedId) -and ($null -eq $payload.error) -and (Test-JsonObjectMap $payload.result)) { return $payload }
  }
  return $null
}
function Test-PiShimReadiness {
  try {
    $headers = @{ 'Content-Type' = 'application/json'; Accept = 'application/json' }
    $body = (@{ jsonrpc = '2.0'; id = 1; method = 'initialize'; params = @{ protocolVersion = '2025-06-18'; capabilities = @{}; clientInfo = @{ name = 'agentcore-pi-shim-start'; version = '1.0.0' } } } | ConvertTo-Json -Depth 6 -Compress)
    $response = Invoke-WebRequest -Uri ("http://{0}:{1}/mcp" -f $HostAddress, $Port) -Method POST -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ($response.StatusCode -ne 200) { return $false }
    if ($null -eq (Get-McpJsonRpcResponse $response 1)) { return $false }
    $toolsBody = (@{ jsonrpc = '2.0'; id = 2; method = 'tools/list'; params = @{} } | ConvertTo-Json -Compress)
    $toolsResponse = Invoke-WebRequest -Uri ("http://{0}:{1}/mcp" -f $HostAddress, $Port) -Method POST -Headers $headers -Body $toolsBody -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    $toolsPayload = Get-McpJsonRpcResponse $toolsResponse 2
    if ($null -eq $toolsPayload) { return $false }
    $tools = $toolsPayload.result.tools
    return ($tools -is [System.Array]) -and ($tools.Count -ge 4)
  } catch { return $false }
}
$RepoRoot = ConvertTo-AgentCoreCanonicalPath $RepoRoot
$RuntimeRoot = ConvertTo-AgentCoreCanonicalPath $RuntimeRoot
New-Item -ItemType Directory -Force -Path (Join-Path $RuntimeRoot 'state'), (Join-Path $RuntimeRoot 'logs') | Out-Null
if ($ProbeOnly) {
  if (-not (Test-PiShimReadiness)) { throw ("Pi shim did not reach readiness on {0}:{1}" -f $HostAddress, $Port) }
  Write-Host ("[Start] Pi shim readiness confirmed on {0}:{1}" -f $HostAddress, $Port)
  exit 0
}
if (Test-PiShimReadiness) {
  Write-Host ("[Start] Pi shim already ready on {0}:{1}" -f $HostAddress, $Port)
  exit 0
}
if ([string]::IsNullOrWhiteSpace($PythonExe)) { $PythonExe = Join-Path $RepoRoot 'scripts\.venv\Scripts\python.exe' }
if ([string]::IsNullOrWhiteSpace($ShimScript)) { $ShimScript = Join-Path $RepoRoot 'scripts\bifrost\pi_session_shim.py' }
$stdoutLog = Join-Path $RuntimeRoot 'logs\pi-shim.stdout.log'
$stderrLog = Join-Path $RuntimeRoot 'logs\pi-shim.stderr.log'
Start-Process -FilePath $PythonExe -ArgumentList @('-u', $ShimScript, '--host', $HostAddress, '--port', ([string]$Port)) -WorkingDirectory $RuntimeRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog | Out-Null
Write-Host '[Start] Launched Pi shim directly; no scheduled task was created'
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 2
  if (Test-PiShimReadiness) {
    Write-Host ("[Start] Pi shim readiness confirmed on {0}:{1}" -f $HostAddress, $Port)
    exit 0
  }
}
throw ("Pi shim did not reach readiness on {0}:{1}" -f $HostAddress, $Port)
