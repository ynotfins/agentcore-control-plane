param(
  [ValidateSet("ShowConfig", "StartMeilisearch", "StartApi", "Register", "Health", "Mcp", "CliHelp", "MemoryList")]
  [string]$Mode = "ShowConfig",
  [string]$ConfigPath = "F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json",
  [switch]$PersistApiKey
)

$ErrorActionPreference = "Stop"

function Get-Config {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "SwarmRecall config not found: $Path"
  }
  return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Set-LocalEnv {
  param($Config, [switch]$RequireApiKey)

  $dbPassword = [Environment]::GetEnvironmentVariable($Config.database.passwordEnv, "User")
  if ([string]::IsNullOrEmpty($dbPassword)) {
    throw "Missing required Windows environment variable: $($Config.database.passwordEnv)"
  }

  $meiliKey = [Environment]::GetEnvironmentVariable($Config.search.masterKeyEnv, "User")
  if ([string]::IsNullOrEmpty($meiliKey)) {
    throw "Missing required Windows environment variable: $($Config.search.masterKeyEnv)"
  }

  $env:NODE_EXTRA_CA_CERTS = $Config.database.caPath
  $env:DATABASE_URL = "postgresql://$($Config.database.role):$dbPassword@$($Config.database.host):$($Config.database.port)/$($Config.database.database)?sslmode=$($Config.database.sslmode)"
  $env:MEILISEARCH_URL = $Config.search.url
  $env:MEILISEARCH_API_KEY = $meiliKey
  $env:MEILI_MASTER_KEY = $meiliKey
  $env:MEILI_NO_ANALYTICS = "true"
  $env:PORT = [string]$Config.api.port
  $env:HOST = $Config.api.host
  $env:SWARMRECALL_HOST = $Config.api.host
  $env:CORS_ORIGINS = ($Config.api.corsOrigins -join ",")
  $env:HF_HOME = $Config.runtime.hfHome
  $env:DASHBOARD_URL = $Config.api.dashboardUrl
  $env:SWARMRECALL_API_URL = $Config.api.url

  Remove-Item Env:UPSTASH_REDIS_REST_URL -ErrorAction SilentlyContinue
  Remove-Item Env:UPSTASH_REDIS_REST_TOKEN -ErrorAction SilentlyContinue
  Remove-Item Env:FIREBASE_PROJECT_ID -ErrorAction SilentlyContinue
  Remove-Item Env:FIREBASE_CLIENT_EMAIL -ErrorAction SilentlyContinue
  Remove-Item Env:FIREBASE_PRIVATE_KEY -ErrorAction SilentlyContinue

  if ($RequireApiKey) {
    $apiKey = [Environment]::GetEnvironmentVariable($Config.auth.apiKeyEnv, "User")
    if ([string]::IsNullOrEmpty($apiKey)) {
      throw "Missing required Windows environment variable: $($Config.auth.apiKeyEnv)"
    }
    $env:SWARMRECALL_API_KEY = $apiKey
  }
}

$config = Get-Config -Path $ConfigPath

switch ($Mode) {
  "ShowConfig" {
    [pscustomobject]@{
      mode = $config.mode
      repoRoot = $config.source.repoRoot
      runtimeRoot = $config.runtime.root
      apiUrl = $config.api.url
      database = $config.database.database
      databaseRole = $config.database.role
      meilisearchUrl = $config.search.url
      analytics = $config.search.analytics
      firebaseDashboardAuth = $config.auth.firebaseDashboardAuth
      upstashRedis = $config.auth.upstashRedis
    } | ConvertTo-Json -Depth 5
  }
  "StartMeilisearch" {
    $meiliKey = [Environment]::GetEnvironmentVariable($config.search.masterKeyEnv, "User")
    if ([string]::IsNullOrEmpty($meiliKey)) {
      throw "Missing required Windows environment variable: $($config.search.masterKeyEnv)"
    }
    if (-not (Test-Path -LiteralPath $config.search.binaryPath)) {
      throw "Meilisearch binary not found: $($config.search.binaryPath)"
    }
    if (-not (Test-Path -LiteralPath $config.search.dataPath)) {
      New-Item -ItemType Directory -Path $config.search.dataPath | Out-Null
    }
    $env:MEILI_MASTER_KEY = $meiliKey
    $env:MEILI_NO_ANALYTICS = "true"
    & $config.search.binaryPath --http-addr ($config.api.host + ':7700') --db-path $config.search.dataPath --no-analytics
    exit $LASTEXITCODE
  }
  "StartApi" {
    Set-LocalEnv -Config $config
    if (-not (Test-Path -LiteralPath $config.runtime.hfHome)) {
      New-Item -ItemType Directory -Path $config.runtime.hfHome | Out-Null
    }
    & node $config.source.apiDist
    exit $LASTEXITCODE
  }
  "Register" {
    Set-LocalEnv -Config $config
    $body = '{"name":"agentcore-local"}'
    $resp = Invoke-RestMethod -Method Post -Uri ($config.api.url + '/api/v1/register') -ContentType 'application/json' -Body $body
    if ($PersistApiKey -and -not [string]::IsNullOrEmpty($resp.apiKey)) {
      [Environment]::SetEnvironmentVariable($config.auth.apiKeyEnv, $resp.apiKey, "User")
      [Environment]::SetEnvironmentVariable($config.auth.apiKeyEnv, $resp.apiKey, "Process")
    }
    [pscustomobject]@{
      apiKeyStored = (-not [string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($config.auth.apiKeyEnv, "User")))
      agentIdPresent = (-not [string]::IsNullOrEmpty($resp.agentId))
      ownerIdPresent = (-not [string]::IsNullOrEmpty($resp.ownerId))
      claimTokenPresent = (-not [string]::IsNullOrEmpty($resp.claimToken))
      claimUrlIsLocal = ($resp.claimUrl -like ($config.api.dashboardUrl + '*'))
    } | ConvertTo-Json -Depth 5
  }
  "Health" {
    (Invoke-WebRequest -UseBasicParsing -Uri ($config.api.url + '/api/v1/health')).Content
  }
  "Mcp" {
    Set-LocalEnv -Config $config -RequireApiKey
    & node $config.source.cliDist mcp
    exit $LASTEXITCODE
  }
  "CliHelp" {
    & node $config.source.cliDist --help
    exit $LASTEXITCODE
  }
  "MemoryList" {
    Set-LocalEnv -Config $config -RequireApiKey
    & node $config.source.cliDist memory list
    exit $LASTEXITCODE
  }
}
