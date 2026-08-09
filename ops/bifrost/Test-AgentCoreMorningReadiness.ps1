<#
.SYNOPSIS
  Read-only morning readiness gate for AgentCore, Bifrost, LangGraph, and Swarm loopback services.

.DESCRIPTION
  This script does not mutate live IDE configs, scheduled tasks, runtime config,
  databases, Swarm roots, or repositories. It reports the approval gates that
  must be cleared before autonomous production work starts.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$CursorMcpPath = 'C:\Users\ynotf\.cursor\mcp.json',
  [string]$BaseUrl = 'http://127.0.0.1:8080',
  [string]$RecallHealthUrl = 'http://127.0.0.1:3300/api/v1/health',
  [string]$MeiliHealthUrl = 'http://127.0.0.1:7700/health',
  [string]$SwarmClawHealthUrl = 'http://127.0.0.1:3456/api/healthz',
  [string]$RecallWebUrl = 'http://127.0.0.1:3400',
  [switch]$Json
)

$ErrorActionPreference = 'Stop'

$results = [System.Collections.Generic.List[object]]::new()

function Add-ReadinessResult {
  param(
    [ValidateSet('PASS', 'WARN', 'FAIL')]
    [string]$Status,
    [string]$Name,
    [string]$Detail,
    [string]$Remediation = ''
  )
  $results.Add([pscustomobject]@{
    status = $Status
    name = $Name
    detail = $Detail
    remediation = $Remediation
  }) | Out-Null
}

function Test-HttpEndpoint {
  param([string]$Name, [string]$Url)
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
    Add-ReadinessResult 'PASS' $Name ("HTTP {0}" -f [int]$response.StatusCode)
  } catch {
    Add-ReadinessResult 'FAIL' $Name $_.Exception.Message
  }
}

function Test-PathExists {
  param([string]$Name, [string]$Path)
  if (Test-Path -LiteralPath $Path) {
    Add-ReadinessResult 'PASS' $Name "exists: $Path"
  } else {
    Add-ReadinessResult 'FAIL' $Name "missing: $Path"
  }
}

function Get-Sha256OrMissing {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    return $null
  }
  return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Get-PythonCommandOrNull {
  foreach ($candidate in @('py', 'python', 'python3')) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
  }
  $python313 = 'C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe'
  if (Test-Path -LiteralPath $python313 -PathType Leaf) { return $python313 }
  return $null
}

function Test-CursorMcp {
  if (-not (Test-Path -LiteralPath $CursorMcpPath -PathType Leaf)) {
    Add-ReadinessResult 'FAIL' 'cursor_global_mcp' "missing: $CursorMcpPath" 'Phase 2: approve/run cursor-only Invoke-AgentCoreIdeGatewayCutover.ps1 cleanup after restoring or recreating the config.'
    return
  }
  try {
    $raw = Get-Content -Raw -LiteralPath $CursorMcpPath
    $jsonDoc = $raw | ConvertFrom-Json -ErrorAction Stop
    $names = @($jsonDoc.mcpServers.PSObject.Properties.Name)
    if ($names.Count -eq 1 -and $names[0] -eq 'agentcore-gateway') {
      Add-ReadinessResult 'PASS' 'cursor_global_mcp' 'exactly one server: agentcore-gateway'
    } else {
      Add-ReadinessResult 'FAIL' 'cursor_global_mcp' ("expected only agentcore-gateway; found count={0}; names={1}" -f $names.Count, ($names -join ',')) 'Phase 2: approve/run cursor-only Invoke-AgentCoreIdeGatewayCutover.ps1 cleanup, then rerun Test-AgentCoreBifrostGateway.ps1.'
    }
    if ($raw -match 'sk-[A-Za-z0-9_-]{20,}') {
      Add-ReadinessResult 'FAIL' 'cursor_global_mcp_secret_scan' 'obvious secret literal pattern present' 'Security stop: do not proceed; sanitize/rotate the exposed secret with explicit operator approval.'
    } else {
      Add-ReadinessResult 'PASS' 'cursor_global_mcp_secret_scan' 'no obvious secret literal pattern'
    }
  } catch {
    Add-ReadinessResult 'FAIL' 'cursor_global_mcp_parse' $_.Exception.Message 'Phase 2 stop: repair JSON parse error from timestamped backup before cleanup.'
  }
}

function Test-BifrostStatusScript {
  $statusScript = Join-Path $RepoRoot 'ops\bifrost\Get-BifrostStatus.ps1'
  if (-not (Test-Path -LiteralPath $statusScript -PathType Leaf)) {
    Add-ReadinessResult 'FAIL' 'bifrost_status_script' "missing: $statusScript" 'Repo/source stop: restore missing Bifrost status script before live rollout.'
    return
  }
  $pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
  if (-not $pwsh) {
    $pwsh = (Get-Command powershell -ErrorAction SilentlyContinue).Source
  }
  if (-not $pwsh) {
    Add-ReadinessResult 'FAIL' 'bifrost_status_script' 'PowerShell executable not found for child status capture' 'Host stop: install/repair PowerShell before running Bifrost lifecycle checks.'
    return
  }
  $output = & $pwsh -NoProfile -File $statusScript 2>&1
  $exit = $LASTEXITCODE
  if ($exit -eq 0 -and (($output | Out-String) -match 'BIFROST_STATUS_OK')) {
    Add-ReadinessResult 'PASS' 'bifrost_status_script' 'BIFROST_STATUS_OK'
  } else {
    Add-ReadinessResult 'FAIL' 'bifrost_status_script' (($output | Out-String).Trim()) 'Phase 3 stop: repair Bifrost health/status before config or watchdog rollout.'
  }
}

function Test-BifrostConfigDrift {
  $renderScript = Join-Path $RepoRoot 'scripts\bifrost\render_bifrost_config.py'
  $liveConfig = Join-Path $RuntimeRoot 'config.json'
  $liveConfigProjection = Join-Path $RuntimeRoot 'config\config.json'
  $candidateHash = $null
  if (-not (Test-Path -LiteralPath $renderScript -PathType Leaf)) {
    Add-ReadinessResult 'FAIL' 'bifrost_config_hashes' "missing renderer: $renderScript" 'Source stop: restore render_bifrost_config.py before evaluating live config drift.'
    return
  }
  $pythonCmd = Get-PythonCommandOrNull
  if (-not $pythonCmd) {
    Add-ReadinessResult 'FAIL' 'bifrost_config_hashes' 'Python interpreter not found for source-rendered runtime candidate' 'Host stop: install/repair Python before evaluating live config drift.'
    return
  }
  $candidatePath = Join-Path ([IO.Path]::GetTempPath()) ("agentcore-bifrost-candidate-{0}.json" -f ([guid]::NewGuid().ToString('N')))
  try {
    & $pythonCmd $renderScript --out $candidatePath --no-also-config-dir --skip-renderer | Out-Null
    if ($LASTEXITCODE -ne 0) {
      Add-ReadinessResult 'FAIL' 'bifrost_config_hashes' "renderer exit=$LASTEXITCODE" 'Source stop: repair Bifrost renderer/contract errors before live rollout.'
      return
    }
    $candidateHash = Get-Sha256OrMissing $candidatePath
  } catch {
    Add-ReadinessResult 'FAIL' 'bifrost_config_hashes' $_.Exception.Message 'Source stop: repair Bifrost renderer/contract errors before live rollout.'
    return
  } finally {
    if (Test-Path -LiteralPath $candidatePath -PathType Leaf) {
      [IO.File]::Delete($candidatePath)
    }
  }
  $liveHash = Get-Sha256OrMissing $liveConfig
  $projectionHash = Get-Sha256OrMissing $liveConfigProjection
  if (-not $candidateHash -or -not $liveHash -or -not $projectionHash) {
    Add-ReadinessResult 'FAIL' 'bifrost_config_hashes' "candidate=$candidateHash live=$liveHash projection=$projectionHash" 'Phase 3: approve governed Bifrost installer rollout; stop if any config path is unexpectedly missing.'
    return
  }
  if ($candidateHash -eq $liveHash -and $candidateHash -eq $projectionHash) {
    Add-ReadinessResult 'PASS' 'bifrost_config_drift' "source-rendered candidate/live/projection match: $candidateHash"
  } else {
    Add-ReadinessResult 'FAIL' 'bifrost_config_drift' "candidate=$candidateHash live=$liveHash projection=$projectionHash" 'Phase 3: approve/run Install-AgentCoreBifrostGateway.ps1 to activate both config projections, then rerun this checker.'
  }
}

function Test-AgentCoreScheduledTasks {
  foreach ($taskName in @('AgentCore-Bifrost-Gateway', 'AgentCore-Bifrost-Watchdog')) {
    try {
      $task = Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName $taskName -ErrorAction Stop
      $info = Get-ScheduledTaskInfo -TaskPath '\AgentCore\' -TaskName $taskName -ErrorAction Stop
      $status = if ($taskName -eq 'AgentCore-Bifrost-Gateway' -and $task.State -ne 'Running') { 'FAIL' } else { 'PASS' }
      Add-ReadinessResult $status "task_$taskName" ("state={0}; lastResult={1}; lastRun={2}" -f $task.State, $info.LastTaskResult, $info.LastRunTime)
    } catch {
      $remediation = if ($taskName -eq 'AgentCore-Bifrost-Watchdog') {
        'Phase 3: approve/run governed Bifrost installer rollout to install AgentCore-Bifrost-Watchdog.'
      } else {
        'Phase 3 stop: repair or reinstall AgentCore-Bifrost-Gateway scheduled task before production work.'
      }
      Add-ReadinessResult 'FAIL' "task_$taskName" $_.Exception.Message $remediation
    }
  }
}

function Test-LangGraphTopology {
  $scriptsRoot = Join-Path $RepoRoot 'scripts'
  $python = Join-Path $scriptsRoot '.venv\Scripts\python.exe'
  if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    Add-ReadinessResult 'FAIL' 'langgraph_topology' "missing runtime python: $python" 'Runtime stop: repair AgentCore scripts virtualenv with bootstrap-runtime.ps1 before LangGraph canary.'
    return
  }
  Push-Location $scriptsRoot
  try {
    $output = & $python -m agentcore workflow topology --json 2>&1
    $exit = $LASTEXITCODE
    if ($exit -ne 0) {
      Add-ReadinessResult 'FAIL' 'langgraph_topology' (($output | Out-String).Trim()) 'Runtime stop: repair LangGraph topology/runtime before production canary.'
      return
    }
    $topology = ($output | Out-String) | ConvertFrom-Json -ErrorAction Stop
    if ($topology.topology_fingerprint_sha256 -eq 'a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32' -and [int]$topology.node_count -eq 15) {
      Add-ReadinessResult 'PASS' 'langgraph_topology' ("fingerprint={0}; nodes={1}" -f $topology.topology_fingerprint_sha256, $topology.node_count)
    } else {
      Add-ReadinessResult 'FAIL' 'langgraph_topology' ("unexpected fingerprint={0}; nodes={1}" -f $topology.topology_fingerprint_sha256, $topology.node_count) 'Runtime stop: topology drift requires explicit operator approval before production canary.'
    }
  } catch {
    Add-ReadinessResult 'FAIL' 'langgraph_topology' $_.Exception.Message 'Runtime stop: repair LangGraph topology command before production canary.'
  } finally {
    Pop-Location
  }
}

function Test-KeyPorts {
  $netstat = netstat -ano | Out-String
  foreach ($port in @(3300, 3456, 7700, 8080, 55433, 65432)) {
    if ($netstat -match "127\.0\.0\.1:$port\s+") {
      Add-ReadinessResult 'PASS' "port_$port" 'listening on 127.0.0.1'
    } else {
      Add-ReadinessResult 'FAIL' "port_$port" 'not observed listening on 127.0.0.1' 'Service stop: restore the owning service before runtime acceptance; Sally owns Swarm ports, AgentCore owns Bifrost/PG18.'
    }
  }
}

Test-CursorMcp
Test-BifrostStatusScript
Test-HttpEndpoint 'bifrost_health' "$BaseUrl/health"
Test-BifrostConfigDrift
Test-AgentCoreScheduledTasks
Test-HttpEndpoint 'swarmrecall_api_health' $RecallHealthUrl
Test-HttpEndpoint 'meilisearch_health' $MeiliHealthUrl
Test-HttpEndpoint 'swarmclaw_health' $SwarmClawHealthUrl
Test-HttpEndpoint 'swarmrecall_web' $RecallWebUrl
Test-PathExists 'swarm_data_root' 'H:\SwarmData'
Test-PathExists 'swarm_runtime_root' 'H:\SwarmRuntime'
Test-PathExists 'swarm_backup_root' 'E:\SwarmBackups'
Test-PathExists 'agentcore_runtime_root' 'F:\AgentCore'
Test-PathExists 'postgres18_root' 'F:\PostgreSQL18'
Test-KeyPorts
Test-LangGraphTopology

$failCount = @($results | Where-Object { $_.status -eq 'FAIL' }).Count
$warnCount = @($results | Where-Object { $_.status -eq 'WARN' }).Count
$passCount = @($results | Where-Object { $_.status -eq 'PASS' }).Count

if ($Json) {
  [pscustomobject]@{
    status = if ($failCount -eq 0) { 'READY' } else { 'NOT_READY' }
    pass = $passCount
    warn = $warnCount
    fail = $failCount
    results = @($results)
  } | ConvertTo-Json -Depth 6
} else {
  foreach ($result in $results) {
    Write-Host ("{0}  {1}: {2}" -f $result.status.PadRight(4), $result.name, $result.detail)
    if ($result.status -ne 'PASS' -and -not [string]::IsNullOrWhiteSpace([string]$result.remediation)) {
      Write-Host ("      remediation: {0}" -f $result.remediation)
    }
  }
  Write-Host ("SUMMARY status={0} pass={1} warn={2} fail={3}" -f $(if ($failCount -eq 0) { 'READY' } else { 'NOT_READY' }), $passCount, $warnCount, $failCount)
}

if ($failCount -gt 0) {
  exit 1
}
