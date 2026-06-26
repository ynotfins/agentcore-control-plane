param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("Meilisearch", "Api")]
  [string]$Component,
  [string]$ConfigPath = "F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json"
)

$ErrorActionPreference = "Stop"

function Get-AgentCoreSwarmRecallConfig {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "SwarmRecall config not found: $Path"
  }
  Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Test-AgentCoreTcpListener {
  param(
    [string]$Address,
    [int]$Port
  )
  $matches = @(netstat -ano | Where-Object {
    $_ -match "LISTENING" -and $_ -match [regex]::Escape("$Address`:$Port")
  })
  return ($matches.Count -gt 0)
}

function Test-AgentCoreApiHealth {
  param([string]$Url)
  try {
    $raw = (Invoke-WebRequest -UseBasicParsing -Uri ($Url.TrimEnd("/") + "/api/v1/health") -TimeoutSec 10).Content
    $health = $raw | ConvertFrom-Json
    return ($health.status -eq "ok" -and [bool]$health.services.database)
  } catch {
    return $false
  }
}

$config = Get-AgentCoreSwarmRecallConfig -Path $ConfigPath
$logDir = $config.runtime.logsDir
if (-not (Test-Path -LiteralPath $logDir)) {
  New-Item -ItemType Directory -Path $logDir | Out-Null
}
$logPath = Join-Path $logDir ("swarmrecall-{0}-task.log" -f $Component.ToLowerInvariant())
Start-Transcript -Path $logPath -Append | Out-Null
$repoOps = Split-Path -Parent $PSCommandPath
$invokeScript = Join-Path $repoOps "Invoke-AgentCoreSwarmRecall.ps1"

try {
  if (-not (Test-Path -LiteralPath $invokeScript)) {
    throw "SwarmRecall invoke script not found: $invokeScript"
  }

  switch ($Component) {
    "Meilisearch" {
      $meiliUri = [uri]$config.search.url
      if (Test-AgentCoreTcpListener -Address $meiliUri.Host -Port $meiliUri.Port) {
        Write-Host "SwarmRecall Meilisearch already listening on $($config.search.url)."
        exit 0
      }
      & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $invokeScript -Mode StartMeilisearch -ConfigPath $ConfigPath
      exit $LASTEXITCODE
    }
    "Api" {
      if ((Test-AgentCoreTcpListener -Address $config.api.host -Port ([int]$config.api.port)) -and (Test-AgentCoreApiHealth -Url $config.api.url)) {
        Write-Host "SwarmRecall API already healthy on $($config.api.url)."
        exit 0
      }
      & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $invokeScript -Mode StartApi -ConfigPath $ConfigPath
      exit $LASTEXITCODE
    }
  }
} catch {
  Write-Error $_
  exit 1
} finally {
  Stop-Transcript | Out-Null
}
