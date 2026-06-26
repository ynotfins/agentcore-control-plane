param(
  [string]$ConfigPath = "F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json"
)

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

function Get-Config {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "SwarmRecall config not found: $Path"
  }
  return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

$results = [System.Collections.Generic.List[object]]::new()
$config = Get-Config -Path $ConfigPath

Add-Result $results "config file" $true $ConfigPath
Add-Result $results "repo root" (Test-Path -LiteralPath $config.source.repoRoot) $config.source.repoRoot
Add-Result $results "api dist" (Test-Path -LiteralPath $config.source.apiDist) $config.source.apiDist
Add-Result $results "cli dist" (Test-Path -LiteralPath $config.source.cliDist) $config.source.cliDist
Add-Result $results "runtime root" (Test-Path -LiteralPath $config.runtime.root) $config.runtime.root
Add-Result $results "meilisearch binary" (Test-Path -LiteralPath $config.search.binaryPath) $config.search.binaryPath
Add-Result $results "meilisearch data path" (Test-Path -LiteralPath $config.search.dataPath) $config.search.dataPath
Add-Result $results "hf cache path" (Test-Path -LiteralPath $config.runtime.hfHome) $config.runtime.hfHome
Add-Result $results "local api url" ($config.api.url -eq "http://127.0.0.1:3300") $config.api.url
Add-Result $results "hosted api forbidden" ([bool]$config.auth.hostedApiForbidden) ([string]$config.auth.hostedApiForbidden)
Add-Result $results "firebase dashboard disabled" (-not [bool]$config.auth.firebaseDashboardAuth) ([string]$config.auth.firebaseDashboardAuth)
Add-Result $results "upstash disabled" (-not [bool]$config.auth.upstashRedis) ([string]$config.auth.upstashRedis)

$envFiles = @(
  Get-ChildItem -LiteralPath $config.runtime.root -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^\.env(\..+)?$' } |
    Select-Object -ExpandProperty FullName
)
Add-Result $results "no env files in runtime root" ($envFiles.Count -eq 0) ($(if ($envFiles.Count) { $envFiles -join ", " } else { "none found" }))

$apiKeyPresent = -not [string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($config.auth.apiKeyEnv, "User"))
$dbPassPresent = -not [string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($config.database.passwordEnv, "User"))
$meiliKeyPresent = -not [string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($config.search.masterKeyEnv, "User"))
Add-Result $results "api key env present" $apiKeyPresent $config.auth.apiKeyEnv
Add-Result $results "db password env present" $dbPassPresent $config.database.passwordEnv
Add-Result $results "meilisearch key env present" $meiliKeyPresent $config.search.masterKeyEnv

$netstatLines = @(netstat -ano)
$apiNetstat = @($netstatLines | Where-Object { $_ -match "LISTENING" -and $_ -match (":{0}\s" -f $config.api.port) })
$apiLoopbackOnly = $apiNetstat.Count -eq 1 -and $apiNetstat[0] -match "127\.0\.0\.1:$($config.api.port)"
Add-Result $results "api loopback listener only" $apiLoopbackOnly ($(if ($apiNetstat.Count) { $apiNetstat -join " | " } else { "none" }))

$meiliPort = [uri]$config.search.url
$meiliNetstat = @($netstatLines | Where-Object { $_ -match "LISTENING" -and $_ -match (":{0}\s" -f $meiliPort.Port) })
$meiliLoopbackOnly = $meiliNetstat.Count -eq 1 -and $meiliNetstat[0] -match "127\.0\.0\.1:$($meiliPort.Port)"
Add-Result $results "single meilisearch loopback listener" $meiliLoopbackOnly ($(if ($meiliNetstat.Count) { $meiliNetstat -join " | " } else { "none" }))

$meiliKey = [Environment]::GetEnvironmentVariable($config.search.masterKeyEnv, "User")
$processes = Get-CimInstance Win32_Process | Where-Object {
  ($_.Name -ieq 'meilisearch.exe') -or ($_.Name -match '^node(\\.exe)?$' -and $_.CommandLine -match 'swarmrecall')
}
$meiliProcesses = @($processes | Where-Object { $_.Name -ieq 'meilisearch.exe' })
$masterKeyArgFound = $false
$rawSecretFound = $false
foreach ($procInfo in $processes) {
  if ($procInfo.CommandLine -match '--master-key') {
    $masterKeyArgFound = $true
  }
  if ($meiliKey -and $procInfo.CommandLine -like "*$meiliKey*") {
    $rawSecretFound = $true
  }
}
Add-Result $results "no master-key arg in meilisearch process" (-not $masterKeyArgFound) ($(if ($masterKeyArgFound) { "detected in process args" } else { "not detected" }))
Add-Result $results "no raw secret in process command lines" (-not $rawSecretFound) ($(if ($rawSecretFound) { "detected raw secret in process args" } else { "not detected" }))

$meiliHealth = Invoke-WebRequest -UseBasicParsing -Uri ($config.search.url + '/health') -Headers @{ Authorization = "Bearer " + [Environment]::GetEnvironmentVariable($config.search.masterKeyEnv, "User") } -ErrorAction SilentlyContinue
Add-Result $results "meilisearch health endpoint" ($null -ne $meiliHealth -and $meiliHealth.StatusCode -eq 200) ($(if ($meiliHealth) { $meiliHealth.StatusCode } else { "unreachable" }))

$apiHealthRaw = (Invoke-WebRequest -UseBasicParsing -Uri ($config.api.url + '/api/v1/health')).Content
$apiHealth = $apiHealthRaw | ConvertFrom-Json
$apiOk = $apiHealth.status -eq 'ok'
Add-Result $results "api health endpoint" $apiOk $apiHealthRaw

$env:SWARMRECALL_API_KEY = [Environment]::GetEnvironmentVariable($config.auth.apiKeyEnv, "User")
$env:SWARMRECALL_API_URL = $config.api.url
$memoryList = & node $config.source.cliDist memory list 2>&1
Add-Result $results "cli local api call" ($LASTEXITCODE -eq 0) (($memoryList -join "`n").Trim())

$env:SWARMRECALL_API_KEY = [Environment]::GetEnvironmentVariable($config.auth.apiKeyEnv, "User")
$env:SWARMRECALL_API_URL = $config.api.url
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = "node"
$psi.Arguments = ('"{0}" mcp' -f $config.source.cliDist)
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.Environment["SWARMRECALL_API_KEY"] = $env:SWARMRECALL_API_KEY
$psi.Environment["SWARMRECALL_API_URL"] = $env:SWARMRECALL_API_URL
$probeOk = $false
$probeDetail = ""
$proc = [System.Diagnostics.Process]::new()
$proc.StartInfo = $psi
try {
  $null = $proc.Start()
  $initialize = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"agentcore-validator","version":"0.1.0"}}}'
  $initialized = '{"jsonrpc":"2.0","method":"notifications/initialized"}'
  $tools = '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
  $proc.StandardInput.WriteLine($initialize)
  $initLine = $proc.StandardOutput.ReadLine()
  $proc.StandardInput.WriteLine($initialized)
  $proc.StandardInput.WriteLine($tools)
  $proc.StandardInput.Flush()
  $toolsLine = $proc.StandardOutput.ReadLine()
  $probeOk = (-not [string]::IsNullOrEmpty($initLine)) -and (-not [string]::IsNullOrEmpty($toolsLine))
  $probeDetail = ($initLine + "`n" + $toolsLine).Trim()
} catch {
  $probeDetail = $_.Exception.Message
} finally {
  if (-not $proc.HasExited) {
    $proc.Kill()
  }
}
Add-Result $results "mcp local api probe" $probeOk $probeDetail

$allPassed = -not ($results | Where-Object { -not $_.passed })
$results | ConvertTo-Json -Depth 6
if (-not $allPassed) { exit 1 }
