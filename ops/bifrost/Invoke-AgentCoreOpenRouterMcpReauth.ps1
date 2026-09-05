<#
.SYNOPSIS
  Repair the AgentCore OpenRouter MCP OAuth binding through Bifrost.

.DESCRIPTION
  This script is secret-safe: it checks required environment variable names,
  queries Bifrost management APIs, and stores only OAuth flow metadata. It never
  prints or writes OAuth tokens, Bifrost admin keys, or virtual key values.

  Default mode is read-only preflight/status. Use -Begin to mint a fresh
  Bifrost OAuth consent flow for the existing OpenRouter MCP client. After the
  operator completes browser consent, use -Complete to finalize the flow and
  refresh the runtime oauth-clients.json state file and managed Bifrost configs.
  Use -HardenConfigDbAcl first if status reports broad read ACLs.
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
  [string]$BaseUrl = 'http://127.0.0.1:8080',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$ClientName = 'openrouter',
  [string]$AdminKeyEnvName = 'BIFROST_ADMIN_KEY',
  [string]$EncryptionKeyEnvName = 'BIFROST_ENCRYPTION_KEY',
  [Parameter(ParameterSetName = 'Begin')]
  [switch]$Begin,
  [Parameter(ParameterSetName = 'Complete')]
  [switch]$Complete,
  [Parameter(ParameterSetName = 'Complete')]
  [string]$OAuthConfigId = '',
  [Parameter(ParameterSetName = 'Complete')]
  [switch]$SkipRenderAfterComplete,
  [switch]$HardenConfigDbAcl,
  [switch]$OpenBrowser,
  [switch]$Json
)

$ErrorActionPreference = 'Stop'
$stateDir = Join-Path $RuntimeRoot 'state'
$statePath = Join-Path $stateDir 'oauth-clients.json'
$pendingPath = Join-Path $stateDir 'openrouter-reauth-pending.json'
$configDbPath = Join-Path $RuntimeRoot 'data\config.db'
$backupDir = Join-Path $RuntimeRoot 'backups'

function Get-EnvValue([string]$Name) {
  $value = [Environment]::GetEnvironmentVariable($Name, 'Process')
  if (-not $value) { $value = [Environment]::GetEnvironmentVariable($Name, 'User') }
  if (-not $value) { $value = [Environment]::GetEnvironmentVariable($Name, 'Machine') }
  return $value
}

function Get-AdminHeaders {
  $adminKey = Get-EnvValue $AdminKeyEnvName
  if ([string]::IsNullOrWhiteSpace($adminKey)) {
    throw "$AdminKeyEnvName is not set; cannot call Bifrost management APIs."
  }
  return @{
    Authorization  = "Bearer $adminKey"
    'Content-Type' = 'application/json'
    Accept         = 'application/json'
  }
}

function Join-OrderedPayload($Left, $Right) {
  $merged = [ordered]@{}
  foreach ($payload in @($Left, $Right)) {
    foreach ($property in $payload.GetEnumerator()) {
      $merged[$property.Key] = $property.Value
    }
  }
  return $merged
}

function Invoke-AdminJson([string]$Method, [string]$Path, $Body = $null) {
  $headers = Get-AdminHeaders
  $uri = $BaseUrl.TrimEnd('/') + $Path
  $args = @{
    Uri        = $uri
    Method     = $Method
    Headers    = $headers
    TimeoutSec = 30
  }
  if ($null -ne $Body) {
    $args.Body = ($Body | ConvertTo-Json -Depth 30 -Compress)
  }
  try {
    return Invoke-RestMethod @args
  } catch {
    $statusCode = 0
    try { $statusCode = [int]$_.Exception.Response.StatusCode } catch { $statusCode = 0 }
    $errorBody = [string]$_.ErrorDetails.Message
    if ([string]::IsNullOrWhiteSpace($errorBody)) { $errorBody = [string]$_.Exception.Message }
    $message = $errorBody
    try {
      $parsed = $errorBody | ConvertFrom-Json
      if ($parsed.error -and $parsed.error.message) { $message = [string]$parsed.error.message }
    } catch {
      $message = $errorBody
    }
    throw [System.InvalidOperationException]::new("Bifrost API $Method $Path failed ($statusCode): $message")
  }
}

function Get-OpenRouterClient {
  $response = Invoke-AdminJson -Method 'GET' -Path '/api/mcp/clients?limit=100'
  $clients = @($response.clients | Where-Object { $_.config.name -eq $ClientName })
  if ($clients.Count -ne 1) {
    throw "Expected exactly one $ClientName MCP client; found $($clients.Count)."
  }
  return $clients[0]
}

function Test-ConfigDbAcl {
  if (-not (Test-Path -LiteralPath $configDbPath)) {
    return [pscustomobject]@{ ok = $false; detail = 'config.db missing' }
  }
  $acl = Get-Acl -LiteralPath $configDbPath
  $broad = @($acl.Access | Where-Object {
    ($_.IdentityReference -match 'Everyone|BUILTIN\\Users|NT AUTHORITY\\Authenticated Users') -and
    (($_.FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::Read) -ne 0)
  })
  if ($broad.Count -gt 0) {
    return [pscustomobject]@{ ok = $false; detail = "broad read ACL: $($broad.IdentityReference -join ', ')" }
  }
  return [pscustomobject]@{ ok = $true; detail = 'config.db ACL has no broad read principals' }
}

function Set-ConfigDbAclPrivate {
  if (-not (Test-Path -LiteralPath $configDbPath)) {
    throw "config.db missing: $configDbPath"
  }
  New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $backupPath = Join-Path $backupDir "config-db-acl-$stamp.txt"
  $icaclsOutput = & icacls.exe $configDbPath /save $backupPath /C 2>&1
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to back up config.db ACL: $($icaclsOutput -join [Environment]::NewLine)"
  }

  $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
  $hardenOutput = & icacls.exe $configDbPath `
    /inheritance:r `
    /remove:g 'Everyone' 'BUILTIN\Users' 'NT AUTHORITY\Authenticated Users' `
    /grant:r "$currentUser`:(F)" 'BUILTIN\Administrators:(F)' 'NT AUTHORITY\SYSTEM:(F)' `
    /C 2>&1
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to harden config.db ACL: $($hardenOutput -join [Environment]::NewLine)"
  }

  $result = Test-ConfigDbAcl
  return [ordered]@{
    config_db_acl_hardened = [bool]$result.ok
    config_db_acl_detail = [string]$result.detail
    acl_backup_path = $backupPath
  }
}

function Invoke-Preflight {
  $health = Invoke-WebRequest -Uri ($BaseUrl.TrimEnd('/') + '/health') -UseBasicParsing -TimeoutSec 5
  $encryptionKey = Get-EnvValue $EncryptionKeyEnvName
  $adminKey = Get-EnvValue $AdminKeyEnvName
  $acl = Test-ConfigDbAcl
  $client = Get-OpenRouterClient
  return [ordered]@{
    health_status = [int]$health.StatusCode
    admin_key_present = -not [string]::IsNullOrWhiteSpace($adminKey)
    encryption_key_present = -not [string]::IsNullOrWhiteSpace($encryptionKey)
    config_db_acl_ok = [bool]$acl.ok
    config_db_acl_detail = [string]$acl.detail
    client_id = [string]$client.config.client_id
    client_state = [string]$client.state
    auth_type = [string]$client.config.auth_type
    tool_count = @($client.tools).Count
  }
}

function Invoke-RendererAfterComplete {
  $renderer = Join-Path $RepoRoot 'scripts\bifrost\render_bifrost_config.py'
  if (-not (Test-Path -LiteralPath $renderer)) {
    throw "Bifrost config renderer missing: $renderer"
  }

  $python = Join-Path $RepoRoot 'scripts\.venv\Scripts\python.exe'
  $pythonCommand = if (Test-Path -LiteralPath $python) { $python } else { 'python' }
  $output = & $pythonCommand $renderer 2>&1
  if ($LASTEXITCODE -ne 0) {
    throw "Bifrost config render failed after OAuth completion: $($output -join [Environment]::NewLine)"
  }
  return [string]$renderer
}

function Write-Result($Payload) {
  if ($Json) {
    $Payload | ConvertTo-Json -Depth 20
    return
  }
  foreach ($property in $Payload.GetEnumerator()) {
    Write-Host ("{0}={1}" -f $property.Key, $property.Value)
  }
}

$preflight = Invoke-Preflight
if ($preflight.health_status -ne 200) { throw "Bifrost health check failed: $($preflight.health_status)" }
if (-not $preflight.admin_key_present) { throw "$AdminKeyEnvName is not set." }

if ($HardenConfigDbAcl) {
  $aclResult = Set-ConfigDbAclPrivate
  $preflight = Invoke-Preflight
  if (-not $preflight.config_db_acl_ok) {
    Write-Result (Join-OrderedPayload $aclResult $preflight)
    throw "Unsafe config.db ACL remains after hardening: $($preflight.config_db_acl_detail)"
  }
  if ($PSCmdlet.ParameterSetName -eq 'Status') {
    Write-Result (Join-OrderedPayload $aclResult $preflight)
    exit 0
  }
}

if ($PSCmdlet.ParameterSetName -eq 'Status') {
  Write-Result $preflight
  exit 0
}

if (-not $preflight.encryption_key_present) { throw "$EncryptionKeyEnvName is not set; do not initiate OAuth." }
if (-not $preflight.config_db_acl_ok) { throw "Unsafe config.db ACL: $($preflight.config_db_acl_detail). Re-run with -HardenConfigDbAcl first." }

if ($Begin) {
  $clientId = $preflight.client_id
  $flow = Invoke-AdminJson -Method 'POST' -Path "/api/mcp/client/$clientId/reauthorize"
  New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
  $pending = [ordered]@{
    client_name = $ClientName
    mcp_client_id = [string]$flow.mcp_client_id
    oauth_config_id = [string]$flow.oauth_config_id
    status_url = [string]$flow.status_url
    complete_url = [string]$flow.complete_url
    expires_at = [string]$flow.expires_at
    created_at = (Get-Date).ToUniversalTime().ToString('o')
  }
  $pending | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $pendingPath -Encoding UTF8
  if ($OpenBrowser) {
    Start-Process ([string]$flow.authorize_url) | Out-Null
  }
  Write-Result ([ordered]@{
    status = [string]$flow.status
    mcp_client_id = [string]$flow.mcp_client_id
    oauth_config_id = [string]$flow.oauth_config_id
    status_url = [string]$flow.status_url
    complete_url = [string]$flow.complete_url
    expires_at = [string]$flow.expires_at
    authorize_url = [string]$flow.authorize_url
    pending_state_path = $pendingPath
  })
  exit 0
}

if ($Complete) {
  $pending = $null
  if (Test-Path -LiteralPath $pendingPath) {
    $pending = Get-Content -LiteralPath $pendingPath -Raw -Encoding UTF8 | ConvertFrom-Json
  }
  $flowId = if (-not [string]::IsNullOrWhiteSpace($OAuthConfigId)) { $OAuthConfigId } elseif ($pending) { [string]$pending.oauth_config_id } else { '' }
  if ([string]::IsNullOrWhiteSpace($flowId)) {
    throw 'OAuthConfigId is required when no pending state file exists.'
  }
  $statusUrl = if ($pending -and $pending.status_url) { [string]$pending.status_url } else { "/api/oauth/config/$flowId/status" }
  $flowStatus = Invoke-AdminJson -Method 'GET' -Path $statusUrl
  $pendingCreatedAt = if ($pending -and $pending.created_at) { [datetimeoffset]::Parse([string]$pending.created_at) } else { $null }
  $statusCreatedAt = if ($flowStatus.created_at) { [datetimeoffset]::Parse([string]$flowStatus.created_at) } else { $null }
  $statusIsFresh = $true
  if ($pendingCreatedAt -and $statusCreatedAt -and ($statusCreatedAt -lt $pendingCreatedAt.AddSeconds(-5))) {
    $statusIsFresh = $false
  }
  if (-not $statusIsFresh) {
    Write-Result ([ordered]@{
      status = 'waiting_for_fresh_browser_authorization'
      oauth_config_id = $flowId
      flow_status = [string]$flowStatus.status
      status_url = $statusUrl
      note = 'status row predates the current reauthorization request'
    })
    exit 2
  }
  if ([string]$flowStatus.status -ne 'authorized') {
    Write-Result ([ordered]@{
      status = 'waiting_for_browser_authorization'
      oauth_config_id = $flowId
      flow_status = [string]$flowStatus.status
      status_url = $statusUrl
    })
    exit 2
  }
  $completeUrl = if ($pending -and $pending.complete_url) { [string]$pending.complete_url } else { "/api/mcp/client/$flowId/complete-oauth" }
  try {
    $completeResult = Invoke-AdminJson -Method 'POST' -Path $completeUrl
  } catch {
    $message = [string]$_.Exception.Message
    if ($message -match 'Authorization has not completed yet|already exists') {
      Write-Result ([ordered]@{
        status = 'waiting_for_browser_authorization'
        oauth_config_id = $flowId
        flow_status = [string]$flowStatus.status
        complete_url = $completeUrl
        note = $message
      })
      exit 2
    }
    throw
  }
  $client = Get-OpenRouterClient
  $state = [ordered]@{
    openrouter = [ordered]@{
      oauth_config_id = [string]$client.config.oauth_config_id
      mcp_client_id = [string]$client.config.client_id
    }
  }
  New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
  $state | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $statePath -Encoding UTF8
  $renderedBy = ''
  if (-not $SkipRenderAfterComplete) {
    $renderedBy = Invoke-RendererAfterComplete
  }
  Remove-Item -LiteralPath $pendingPath -Force -ErrorAction SilentlyContinue
  Write-Result ([ordered]@{
    status = [string]$completeResult.status
    message = [string]$completeResult.message
    client_state = [string]$client.state
    tool_count = @($client.tools).Count
    oauth_state_path = $statePath
    runtime_config_rendered = -not $SkipRenderAfterComplete
    renderer = $renderedBy
  })
  exit 0
}
