[CmdletBinding()]
param(
  [string]$Root = "I:\LocalApps\ZooCode\qdrant",
  [switch]$SkipMutation
)

$ErrorActionPreference = "Stop"

function New-Check([string]$Name, [bool]$Passed, [object]$Evidence = $null) {
  [PSCustomObject]@{
    name = $Name
    passed = $Passed
    evidence = $Evidence
  }
}

$checks = [System.Collections.Generic.List[object]]::new()
$baseUrl = "http://127.0.0.1:6333"
$manifestPath = Join-Path $Root "ZOO_CODE_QDRANT_MANIFEST.json"
$manifest = if (Test-Path -LiteralPath $manifestPath) { Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json } else { $null }

$checks.Add((New-Check "manifest_present" ([bool]$manifest) $manifestPath))
$checks.Add((New-Check "executable_present" (Test-Path -LiteralPath (Join-Path $Root "current\qdrant.exe")) (Join-Path $Root "current\qdrant.exe")))
$checks.Add((New-Check "config_present" (Test-Path -LiteralPath (Join-Path $Root "config\zoo-code-qdrant.yaml")) (Join-Path $Root "config\zoo-code-qdrant.yaml")))

$versionResponse = $null
try {
  $versionResponse = Invoke-RestMethod -Uri $baseUrl -TimeoutSec 5
  $checks.Add((New-Check "http_root_reachable" $true $versionResponse.version))
} catch {
  $checks.Add((New-Check "http_root_reachable" $false $_.Exception.Message))
}

try {
  $health = Invoke-RestMethod -Uri "$baseUrl/healthz" -TimeoutSec 5
  $checks.Add((New-Check "healthz_reachable" $true $health.title))
} catch {
  $checks.Add((New-Check "healthz_reachable" $false $_.Exception.Message))
}

function Get-NetstatTcpListeners([int]$Port) {
  $pattern = "^\s*TCP\s+(.+?):$Port\s+\S+\s+LISTENING\s+(\d+)\s*$"
  foreach ($line in @(netstat -ano)) {
    if ($line -match $pattern) {
      [PSCustomObject]@{
        LocalAddress = $Matches[1]
        OwningProcess = [int]$Matches[2]
      }
    }
  }
}

$ports = foreach ($port in @(6333, 6334, 6335)) {
  $listeners = @(Get-NetstatTcpListeners -Port $port)
  [PSCustomObject]@{
    port = $port
    listening = $listeners.Count -gt 0
    local_addresses = @($listeners.LocalAddress | Sort-Object -Unique)
    owning_pids = @($listeners.OwningProcess | Sort-Object -Unique)
  }
}
$httpPort = $ports | Where-Object port -eq 6333
$grpcPort = $ports | Where-Object port -eq 6334
$distributedPort = $ports | Where-Object port -eq 6335
$httpLoopbackOnly = @($httpPort.local_addresses).Count -eq 1 -and @($httpPort.local_addresses)[0] -eq "127.0.0.1"
$grpcLoopbackOnly = @($grpcPort.local_addresses).Count -eq 1 -and @($grpcPort.local_addresses)[0] -eq "127.0.0.1"
$checks.Add((New-Check "http_loopback_only" $httpLoopbackOnly $httpPort))
$checks.Add((New-Check "grpc_loopback_only" $grpcLoopbackOnly $grpcPort))
$checks.Add((New-Check "distributed_port_closed" ([bool](-not $distributedPort.listening)) $distributedPort))

$procEvidence = Get-CimInstance Win32_Process -Filter "Name = 'qdrant.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.ExecutablePath -and $_.ExecutablePath -like "$Root*" } |
  Select-Object ProcessId, ExecutablePath, CommandLine
$checks.Add((New-Check "no_api_key_in_command_line" (-not (($procEvidence.CommandLine -join " ") -match "api[_-]?key|QDRANT__SERVICE__API_KEY")) ($procEvidence | ForEach-Object { [PSCustomObject]@{ ProcessId=$_.ProcessId; ExecutablePath=$_.ExecutablePath; CommandLine=($_.CommandLine -replace 'Bearer\s+\S+','Bearer [REDACTED]') } })))

if (-not $SkipMutation -and $versionResponse) {
  $collection = "agentcore_zoo_qdrant_smoke"
  try {
    Invoke-RestMethod -Uri "$baseUrl/collections/$collection" -Method Delete -TimeoutSec 5 -ErrorAction SilentlyContinue | Out-Null
  } catch {
  }
  $createBody = @{ vectors = @{ size = 4; distance = "Cosine" } } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Uri "$baseUrl/collections/$collection" -Method Put -ContentType "application/json" -Body $createBody -TimeoutSec 10 | Out-Null
  $upsertBody = @{
    points = @(
      @{ id = 1; vector = @(0.1, 0.2, 0.3, 0.4); payload = @{ purpose = "agentcore-zoo-qdrant-smoke" } }
    )
  } | ConvertTo-Json -Depth 8
  Invoke-RestMethod -Uri "$baseUrl/collections/$collection/points?wait=true" -Method Put -ContentType "application/json" -Body $upsertBody -TimeoutSec 10 | Out-Null
  $queryBody = @{ query = @(0.1, 0.2, 0.3, 0.4); limit = 1; with_payload = $true } | ConvertTo-Json -Depth 8
  $query = Invoke-RestMethod -Uri "$baseUrl/collections/$collection/points/query" -Method Post -ContentType "application/json" -Body $queryBody -TimeoutSec 10
  $checks.Add((New-Check "create_upsert_query_collection" ($query.result.points.Count -ge 1) $query.result.points[0].payload.purpose))
  Invoke-RestMethod -Uri "$baseUrl/collections/$collection" -Method Delete -TimeoutSec 10 | Out-Null
  $deleted = $false
  try {
    Invoke-RestMethod -Uri "$baseUrl/collections/$collection" -TimeoutSec 5 | Out-Null
  } catch {
    $deleted = $true
  }
  $checks.Add((New-Check "delete_disposable_collection" $deleted $collection))
}

$task = Get-ScheduledTask -TaskPath "\AgentCore\" -TaskName "ZooCode-Qdrant" -ErrorAction SilentlyContinue
$checks.Add((New-Check "scheduled_task_registered" ([bool]$task) $(if ($task) { [PSCustomObject]@{ TaskPath=$task.TaskPath; TaskName=$task.TaskName; State=$task.State } } else { $null })))

$result = [PSCustomObject]@{
  checked_at = (Get-Date).ToString("o")
  overall = -not (@($checks | Where-Object { -not $_.passed }).Count)
  checks = @($checks)
}

$reportRoot = Join-Path $Root "reports"
if (-not (Test-Path -LiteralPath $reportRoot)) {
  New-Item -ItemType Directory -Path $reportRoot -Force | Out-Null
}
$reportPath = Join-Path $reportRoot ("zoo-code-qdrant-test-{0}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding ascii
$result | Add-Member -NotePropertyName report_path -NotePropertyValue $reportPath -PassThru
