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

function Invoke-AgentCoreNative {
  param(
    [string]$Command,
    [string[]]$Arguments,
    [int]$TimeoutSeconds = 30,
    [string]$WorkingDirectory = "",
    [hashtable]$EnvironmentVariables = @{}
  )

  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = $Command
  if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
    $psi.WorkingDirectory = $WorkingDirectory
  }
  if ($psi.ArgumentList) {
    foreach ($argument in $Arguments) {
      [void]$psi.ArgumentList.Add($argument)
    }
  } else {
    $psi.Arguments = (($Arguments | ForEach-Object {
      '"' + ($_ -replace '"', '\"') + '"'
    }) -join ' ')
  }
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  foreach ($name in $EnvironmentVariables.Keys) {
    $psi.Environment[$name] = [string]$EnvironmentVariables[$name]
  }
  $proc = [System.Diagnostics.Process]::new()
  $proc.StartInfo = $psi
  try {
    $null = $proc.Start()
    $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
    $stderrTask = $proc.StandardError.ReadToEndAsync()
    if (-not $proc.WaitForExit($TimeoutSeconds * 1000)) {
      try { $proc.Kill($true) } catch { try { $proc.Kill() } catch {} }
      return [pscustomobject]@{
        ExitCode = 124
        Output = "Timed out after $TimeoutSeconds seconds: $Command $($Arguments -join ' ')"
      }
    }
    [void]$stdoutTask.Wait(5000)
    [void]$stderrTask.Wait(5000)
    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result
    $output = @($stdout, $stderr) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    return [pscustomobject]@{
      ExitCode = $proc.ExitCode
      Output = (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
    }
  } catch {
    return [pscustomobject]@{
      ExitCode = 1
      Output = $_.Exception.Message
    }
  }
}

function Invoke-AgentCoreHttpGet {
  param(
    [string]$Uri,
    [hashtable]$Headers = @{}
  )

  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -Headers $Headers -TimeoutSec 15 -ErrorAction Stop
    return [pscustomobject]@{
      Ok = $true
      StatusCode = [int]$response.StatusCode
      Content = [string]$response.Content
    }
  } catch {
    $statusCode = 0
    $content = $_.Exception.Message
    if ($_.Exception.Response) {
      try {
        $statusCode = [int]$_.Exception.Response.StatusCode
        $stream = $_.Exception.Response.GetResponseStream()
        if ($stream) {
          $reader = [System.IO.StreamReader]::new($stream)
          $content = $reader.ReadToEnd()
          $reader.Dispose()
        }
      } catch {
        $content = $_.Exception.Message
      }
    }
    return [pscustomobject]@{
      Ok = $false
      StatusCode = $statusCode
      Content = $content
    }
  }
}

function Test-AgentCorePostgresReady {
  param([object]$Config)

  $pgIsReady = "F:\AgentCore\postgres_runtime_engine\pgsql\bin\pg_isready.exe"
  if (-not (Test-Path -LiteralPath $pgIsReady)) {
    return [pscustomobject]@{
      Ok = $false
      Detail = "pg_isready.exe not found at $pgIsReady"
    }
  }
  $probe = Invoke-AgentCoreNative -Command $pgIsReady -Arguments @("-h", $Config.database.host, "-p", [string]$Config.database.port) -TimeoutSeconds 10
  return [pscustomobject]@{
    Ok = ($probe.ExitCode -eq 0)
    Detail = $probe.Output
  }
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

$postgresReady = Test-AgentCorePostgresReady -Config $config
Add-Result $results "postgres dependency reachable" $postgresReady.Ok $postgresReady.Detail

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

$meiliHealth = Invoke-AgentCoreHttpGet -Uri ($config.search.url + '/health') -Headers @{ Authorization = "Bearer " + [Environment]::GetEnvironmentVariable($config.search.masterKeyEnv, "User") }
Add-Result $results "meilisearch health endpoint" ($meiliHealth.Ok -and $meiliHealth.StatusCode -eq 200) ($(if ($meiliHealth.Content) { $meiliHealth.Content } else { "status=" + [string]$meiliHealth.StatusCode }))

$apiHealth = Invoke-AgentCoreHttpGet -Uri ($config.api.url + '/api/v1/health')
$apiOk = $false
if ($apiHealth.Ok) {
  try {
    $apiHealthJson = $apiHealth.Content | ConvertFrom-Json
    $apiOk = $apiHealthJson.status -eq 'ok' -and [bool]$apiHealthJson.services.database
  } catch {
    $apiOk = $false
  }
}
Add-Result $results "api health endpoint" $apiOk $apiHealth.Content

$env:SWARMRECALL_API_KEY = [Environment]::GetEnvironmentVariable($config.auth.apiKeyEnv, "User")
$env:SWARMRECALL_API_URL = $config.api.url
if ($postgresReady.Ok) {
  $memoryList = Invoke-AgentCoreNative -Command "node" -Arguments @($config.source.cliDist, "memory", "list", "--limit", "1") -TimeoutSeconds 20
  Add-Result $results "cli local api call" ($memoryList.ExitCode -eq 0) $memoryList.Output
} else {
  Add-Result $results "cli local api call" $false "skipped because PostgreSQL dependency is unavailable: $($postgresReady.Detail)"
}

$env:SWARMRECALL_API_KEY = [Environment]::GetEnvironmentVariable($config.auth.apiKeyEnv, "User")
$env:SWARMRECALL_API_URL = $config.api.url
$probeOk = $false
$probeDetail = ""
try {
  if ($postgresReady.Ok) {
    $mcpProbeScript = @"
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const cliDist = process.env.AGENTCORE_SWARMRECALL_CLI_DIST;
const transport = new StdioClientTransport({
  command: 'node',
  args: [cliDist, 'mcp'],
  env: {
    ...process.env,
    SWARMRECALL_API_KEY: process.env.SWARMRECALL_API_KEY,
    SWARMRECALL_API_URL: process.env.SWARMRECALL_API_URL
  }
});
const client = new Client({ name: 'agentcore-validator', version: '0.1.0' }, {});
const timeout = setTimeout(() => {
  console.error('Timed out waiting for SwarmRecall MCP tools/list response.');
  process.exit(124);
}, 15000);

try {
  await client.connect(transport);
  const result = await client.listTools();
  const names = result.tools.map((tool) => tool.name);
  console.log(JSON.stringify({
    toolCount: names.length,
    requiredPresent: names.includes('memory_search') && names.includes('knowledge_search'),
    sample: names.slice(0, 8)
  }));
  clearTimeout(timeout);
  await client.close();
} catch (error) {
  clearTimeout(timeout);
  try {
    await client.close();
  } catch {}
  console.error(error?.stack || error?.message || String(error));
  process.exit(1);
}
"@
    $mcpPackageRoot = Join-Path $config.source.repoRoot "packages\mcp"
    $mcpProbe = Invoke-AgentCoreNative `
      -Command "node" `
      -Arguments @("--input-type=module", "-e", $mcpProbeScript) `
      -TimeoutSeconds 30 `
      -WorkingDirectory $mcpPackageRoot `
      -EnvironmentVariables @{
        SWARMRECALL_API_KEY = $env:SWARMRECALL_API_KEY
        SWARMRECALL_API_URL = $env:SWARMRECALL_API_URL
        AGENTCORE_SWARMRECALL_CLI_DIST = $config.source.cliDist
      }
    if ($mcpProbe.ExitCode -eq 0) {
      $mcpProbeJson = $mcpProbe.Output | ConvertFrom-Json
      $probeOk = [bool]$mcpProbeJson.requiredPresent -and [int]$mcpProbeJson.toolCount -ge 50
      $probeDetail = $mcpProbe.Output
    } else {
      $probeDetail = $mcpProbe.Output
    }
  } else {
    $probeDetail = "skipped because PostgreSQL dependency is unavailable: $($postgresReady.Detail)"
  }
} catch {
  $probeDetail = $_.Exception.Message
}
Add-Result $results "mcp local api probe" $probeOk $probeDetail

$allPassed = -not ($results | Where-Object { -not $_.passed })
$results | ConvertTo-Json -Depth 6
if (-not $allPassed) { exit 1 }
