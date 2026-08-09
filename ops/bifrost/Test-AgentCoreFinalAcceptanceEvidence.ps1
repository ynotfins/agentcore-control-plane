<#
.SYNOPSIS
  Read-only preflight for final AgentCore/Swarm runtime restore-point evidence.

.DESCRIPTION
  Verifies that the three closeout evidence files exist before generating the
  final restore-point report. Sally's full Swarm acceptance report is also
  checked with Test-SallyAcceptanceEvidence.ps1.

  This script does not mutate services, scheduled tasks, IDE configs, databases,
  repositories, Swarm roots, or evidence files.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [Parameter(Mandatory = $true)]
  [string]$SallyAcceptancePath,
  [Parameter(Mandatory = $true)]
  [string]$LangGraphCanaryPath,
  [Parameter(Mandatory = $true)]
  [string]$SwarmClawCanaryPath,
  [switch]$Json
)

$ErrorActionPreference = 'Stop'

$results = [System.Collections.Generic.List[object]]::new()

function Add-FinalEvidenceResult {
  param(
    [ValidateSet('PASS', 'FAIL')]
    [string]$Status,
    [string]$Name,
    [string]$Detail
  )
  $results.Add([pscustomobject]@{
    status = $Status
    name = $Name
    detail = $Detail
  }) | Out-Null
}

function Test-EvidenceFile {
  param(
    [string]$Name,
    [string]$Path
  )
  if ([string]::IsNullOrWhiteSpace($Path)) {
    Add-FinalEvidenceResult 'FAIL' $Name 'path not provided'
    return
  }
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    Add-FinalEvidenceResult 'FAIL' $Name "missing file: $Path"
    return
  }
  $item = Get-Item -LiteralPath $Path
  if ($item.Length -le 0) {
    Add-FinalEvidenceResult 'FAIL' $Name "empty file: $Path"
    return
  }
  Add-FinalEvidenceResult 'PASS' $Name ("present; bytes={0}; path={1}" -f $item.Length, $Path)
}

function Test-EvidenceSecretScan {
  param(
    [string]$Name,
    [string]$Path
  )
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    return
  }
  $content = Get-Content -Raw -LiteralPath $Path
  $secretPatterns = @(
    'sk-[A-Za-z0-9_-]{20,}',
    '(?i)\b(BIFROST_MCP_VIRTUAL_KEY|MEILI_MASTER_KEY|SWARMRECALL_API_KEY|AGENTCORE_RECALL_API_KEY|POSTGRES_PASSWORD)\b\s*[:=]\s*\S+',
    '(?i)\bBearer\s+[A-Za-z0-9._~+/-]{20,}'
  )
  foreach ($pattern in $secretPatterns) {
    if ($content -match $pattern) {
      Add-FinalEvidenceResult 'FAIL' "${Name}_secret_scan" 'obvious secret/token literal pattern present'
      return
    }
  }
  Add-FinalEvidenceResult 'PASS' "${Name}_secret_scan" 'no obvious secret/token literal pattern'
}

function Invoke-SallyStructuralGate {
  param([string]$Path)
  $validator = Join-Path $RepoRoot 'ops\bifrost\Test-SallyAcceptanceEvidence.ps1'
  if (-not (Test-Path -LiteralPath $validator -PathType Leaf)) {
    Add-FinalEvidenceResult 'FAIL' 'sally_structural_gate' "missing validator: $validator"
    return
  }
  $pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
  if (-not $pwsh) {
    $pwsh = (Get-Command powershell -ErrorAction SilentlyContinue).Source
  }
  if (-not $pwsh) {
    Add-FinalEvidenceResult 'FAIL' 'sally_structural_gate' 'PowerShell executable not found'
    return
  }
  $output = & $pwsh -NoProfile -File $validator -Path $Path -Json 2>&1
  $exit = $LASTEXITCODE
  $text = ($output | Out-String).Trim()
  if ($exit -ne 0) {
    Add-FinalEvidenceResult 'FAIL' 'sally_structural_gate' $text
    return
  }
  try {
    $parsed = $text | ConvertFrom-Json -ErrorAction Stop
    if ($parsed.status -eq 'READY') {
      Add-FinalEvidenceResult 'PASS' 'sally_structural_gate' 'READY'
    } else {
      Add-FinalEvidenceResult 'FAIL' 'sally_structural_gate' $text
    }
  } catch {
    Add-FinalEvidenceResult 'FAIL' 'sally_structural_gate' "validator JSON parse failed: $($_.Exception.Message)"
  }
}

Test-EvidenceFile 'sally_acceptance_file' $SallyAcceptancePath
Test-EvidenceFile 'langgraph_canary_file' $LangGraphCanaryPath
Test-EvidenceFile 'swarmclaw_canary_file' $SwarmClawCanaryPath

Test-EvidenceSecretScan 'sally_acceptance_file' $SallyAcceptancePath
Test-EvidenceSecretScan 'langgraph_canary_file' $LangGraphCanaryPath
Test-EvidenceSecretScan 'swarmclaw_canary_file' $SwarmClawCanaryPath

if (Test-Path -LiteralPath $SallyAcceptancePath -PathType Leaf) {
  Invoke-SallyStructuralGate $SallyAcceptancePath
}

$failCount = @($results | Where-Object { $_.status -eq 'FAIL' }).Count
$passCount = @($results | Where-Object { $_.status -eq 'PASS' }).Count

if ($Json) {
  [pscustomobject]@{
    status = if ($failCount -eq 0) { 'READY' } else { 'NOT_READY' }
    pass = $passCount
    fail = $failCount
    results = @($results)
  } | ConvertTo-Json -Depth 6
} else {
  foreach ($result in $results) {
    Write-Host ("{0}  {1}: {2}" -f $result.status.PadRight(4), $result.name, $result.detail)
  }
  Write-Host ("SUMMARY status={0} pass={1} fail={2}" -f $(if ($failCount -eq 0) { 'READY' } else { 'NOT_READY' }), $passCount, $failCount)
}
if ($failCount -gt 0) {
  exit 1
}
