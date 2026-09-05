#Requires -Version 7.0
<#
.SYNOPSIS
  Report read-only Bifrost feature adoption evidence without printing secrets.

.DESCRIPTION
  Summarizes local rendered config plus optional safe Bifrost admin endpoints.
  Does not call inference endpoints, does not mutate files or runtime state, and
  never emits raw virtual-key values or secret-like fields.
#>
[CmdletBinding()]
param(
  [string]$BaseUrl = 'http://127.0.0.1:8080',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\bifrost',
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [switch]$NoAdminApi,
  [switch]$TestMode,
  [string]$TestHealthPath = '',
  [string]$TestVersionPath = '',
  [string]$TestConfigPath = '',
  [string]$TestPluginsPath = '',
  [string]$TestVirtualKeysPath = '',
  [string]$TestRoutingRulesPath = '',
  [string]$TestSkillsPath = '',
  [string]$TestProvidersPath = '',
  [string]$TestLogsPath = ''
)

$ErrorActionPreference = 'Stop'

function Get-EnvValue([string]$Name) {
  $value = [Environment]::GetEnvironmentVariable($Name, 'Process')
  if (-not $value) { $value = [Environment]::GetEnvironmentVariable($Name, 'User') }
  return $value
}

function Read-JsonFile([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    return $null
  }
  return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100 -ErrorAction Stop
}

function Get-PropertyValue($Object, [string[]]$Names) {
  if ($null -eq $Object) { return $null }
  foreach ($name in $Names) {
    if ($Object -is [System.Collections.IDictionary] -and $Object.Contains($name)) {
      return $Object[$name]
    }
    $property = $Object.PSObject.Properties[$name]
    if ($null -ne $property) { return $property.Value }
  }
  return $null
}

function Get-ArrayValue($Object, [string[]]$Names) {
  $value = Get-PropertyValue $Object $Names
  if ($null -eq $value) { return @() }
  return @($value)
}

function Get-ObjectPropertyNames($Object) {
  if ($null -eq $Object) { return @() }
  if ($Object -is [System.Collections.IDictionary]) { return @($Object.Keys) }
  return @($Object.PSObject.Properties.Name)
}

function ConvertTo-SecretSafeScalar($Value) {
  if ($null -eq $Value) { return $null }
  if ($Value -is [bool] -or $Value -is [int] -or $Value -is [long] -or $Value -is [double] -or $Value -is [decimal]) {
    return $Value
  }
  $text = [string]$Value
  if ($text -match '(?i)(sk-[A-Za-z0-9_-]{12,}|sk-proj-|sk-or-|ghp_|xox[baprs]-|bearer\s+[A-Za-z0-9._-]{12,}|vk-[A-Za-z0-9_-]{12,})') {
    return '[REDACTED]'
  }
  if ($text -match '^env\.[A-Za-z_][A-Za-z0-9_]*$') {
    return '[ENV_REFERENCE]'
  }
  return $text
}

function Invoke-FeatureEndpoint([string]$Name, [string]$Uri, [bool]$Admin, [string]$FixturePath) {
  if ($TestMode) {
    return @{
      available = -not [string]::IsNullOrWhiteSpace($FixturePath) -and (Test-Path -LiteralPath $FixturePath -PathType Leaf)
      payload = Read-JsonFile $FixturePath
      error = $null
    }
  }

  try {
    $headers = @{}
    if ($Admin) {
      $adminKey = Get-EnvValue 'BIFROST_ADMIN_KEY'
      if (-not $adminKey) {
        return @{ available = $false; payload = $null; error = 'BIFROST_ADMIN_KEY unavailable' }
      }
      $headers['Authorization'] = "Bearer $adminKey"
    }
    $payload = Invoke-RestMethod -Uri $Uri -Headers $headers -TimeoutSec 10
    return @{ available = $true; payload = $payload; error = $null }
  } catch {
    return @{ available = $false; payload = $null; error = "$Name unavailable: $($_.Exception.Message)" }
  }
}

function Get-ProviderNames($ProvidersPayload, $Config) {
  $providers = Get-ArrayValue $ProvidersPayload @('providers', 'data', 'items')
  $names = @(
    foreach ($provider in $providers) {
      $name = Get-PropertyValue $provider @('name', 'id', 'provider')
      if ($name) { [string]$name }
    }
  )
  if ($names.Count -eq 0) {
    $configProviders = Get-PropertyValue $Config @('providers')
    $names = Get-ObjectPropertyNames $configProviders
  }
  return @($names | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Sort-Object -Unique)
}

function Get-PluginSummaries($PluginsPayload, $Config) {
  $plugins = Get-ArrayValue $PluginsPayload @('plugins', 'data', 'items')
  if ($plugins.Count -eq 0) {
    $plugins = Get-ArrayValue $Config @('plugins')
  }
  return @(
    foreach ($plugin in $plugins) {
      $name = Get-PropertyValue $plugin @('name', 'actualName', 'id')
      if (-not $name) { continue }
      $statusObject = Get-PropertyValue $plugin @('status')
      $status = if ($statusObject) { Get-PropertyValue $statusObject @('status', 'state', 'name') } else { $null }
      if (-not $status) { $status = Get-PropertyValue $plugin @('state', 'status') }
      [pscustomobject]@{
        name = [string]$name
        enabled = [bool](Get-PropertyValue $plugin @('enabled', 'is_enabled', 'active', 'is_active'))
        status = ConvertTo-SecretSafeScalar $status
      }
    }
  )
}

function Get-SemanticCacheSummary($PluginSummaries, $PluginsPayload, $Config) {
  $configPlugins = Get-ArrayValue $Config @('plugins')
  $configPlugin = @($configPlugins | Where-Object {
      (Get-PropertyValue $_ @('name', 'actualName', 'id')) -eq 'semantic_cache'
    } | Select-Object -First 1)
  $runtimePlugin = @($PluginSummaries | Where-Object { $_.name -eq 'semantic_cache' } | Select-Object -First 1)
  $configured = $configPlugin.Count -gt 0 -and [bool](Get-PropertyValue $configPlugin[0] @('enabled', 'is_enabled', 'active', 'is_active'))
  $runtimeActive = $false
  if ($runtimePlugin.Count -gt 0) {
    $runtimeStatus = [string]$runtimePlugin[0].status
    $runtimeActive = $runtimePlugin[0].enabled -or $runtimeStatus -in @('ok', 'healthy', 'active', 'running', 'enabled', 'ready')
  }
  $config = if ($configPlugin.Count -gt 0) { Get-PropertyValue $configPlugin[0] @('config') } else { $null }
  $summary = [ordered]@{}
  foreach ($key in @('dimension', 'ttl', 'cache_by_model', 'cache_by_provider', 'default_cache_key')) {
    $value = Get-PropertyValue $config @($key)
    if ($null -ne $value) { $summary[$key] = ConvertTo-SecretSafeScalar $value }
  }
  return [pscustomobject]@{
    active = [bool]($configured -or $runtimeActive)
    configured = [bool]$configured
    source = @(
      if ($configured) { 'local_config' }
      if ($runtimePlugin.Count -gt 0) { 'admin_plugins' }
    )
    config_summary = [pscustomobject]$summary
  }
}

function Get-VirtualKeySummaries($VirtualKeysPayload, $Config) {
  $keys = Get-ArrayValue $VirtualKeysPayload @('virtual_keys', 'virtualKeys', 'data', 'items')
  if ($keys.Count -eq 0) {
    $governance = Get-PropertyValue $Config @('governance')
    $keys = Get-ArrayValue $governance @('virtual_keys', 'virtualKeys')
  }
  $names = @()
  $summaries = @()
  foreach ($key in $keys) {
    $name = Get-PropertyValue $key @('name', 'id')
    if (-not $name) { continue }
    $names += [string]$name
    $providerConfigs = Get-ArrayValue $key @('provider_configs', 'providerConfigs')
    $mcpConfigs = Get-ArrayValue $key @('mcp_configs', 'mcpConfigs')
    $providerNames = @(
      foreach ($provider in $providerConfigs) {
        $providerName = Get-PropertyValue $provider @('provider', 'name', 'id')
        if ($providerName) { [string]$providerName }
      }
    ) | Sort-Object -Unique
    $mcpNames = @(
      foreach ($mcp in $mcpConfigs) {
        $clientName = Get-PropertyValue $mcp @('mcp_client_name', 'mcpClientName', 'name', 'client')
        if (-not $clientName) {
          $clientObject = Get-PropertyValue $mcp @('mcp_client', 'mcpClient')
          $clientName = Get-PropertyValue $clientObject @('name', 'id', 'client_id', 'clientId')
        }
        if ($clientName) { [string]$clientName }
      }
    ) | Sort-Object -Unique
    $toolCount = 0
    foreach ($mcp in $mcpConfigs) {
      $toolCount += (Get-ArrayValue $mcp @('tools_to_execute', 'toolsToExecute', 'tools')).Count
    }
    $summaries += [pscustomobject]@{
      name = [string]$name
      active = [bool](Get-PropertyValue $key @('is_active', 'isActive', 'active', 'enabled'))
      provider_config_count = $providerConfigs.Count
      provider_names = @($providerNames)
      mcp_config_count = $mcpConfigs.Count
      mcp_client_names = @($mcpNames)
      mcp_tool_grant_count = $toolCount
    }
  }
  return [pscustomobject]@{
    count = $names.Count
    names = @($names | Sort-Object -Unique)
    provider_config_summary = @($summaries | Select-Object name, active, provider_config_count, provider_names)
    mcp_config_summary = @($summaries | Select-Object name, active, mcp_config_count, mcp_client_names, mcp_tool_grant_count)
  }
}

function Get-CountFromPayload($Payload, [string[]]$ArrayNames, [string[]]$CountNames) {
  foreach ($countName in $CountNames) {
    $value = Get-PropertyValue $Payload @($countName)
    if ($null -ne $value) { return [int]$value }
  }
  return (Get-ArrayValue $Payload $ArrayNames).Count
}

function Test-EnterpriseFeaturePresent($Name, $PluginSummaries, $Config) {
  if (@($PluginSummaries | Where-Object { $_.name -eq $Name -and ($_.enabled -or $_.status -in @('active', 'running', 'enabled', 'ok', 'healthy')) }).Count -gt 0) {
    return $true
  }
  $plugins = Get-ArrayValue $Config @('plugins')
  return @($plugins | Where-Object {
      (Get-PropertyValue $_ @('name', 'actualName', 'id')) -eq $Name -and
      [bool](Get-PropertyValue $_ @('enabled', 'is_enabled', 'active', 'is_active'))
    }).Count -gt 0
}

$localConfigPath = Join-Path $RuntimeRoot 'config.json'
$localConfig = Read-JsonFile $localConfigPath

$healthResult = Invoke-FeatureEndpoint 'health' "$BaseUrl/health" $false $TestHealthPath

$adminApiAvailable = $false
$versionPayload = $null
$adminConfigPayload = $null
$pluginsPayload = $null
$virtualKeysPayload = $null
$routingRulesPayload = $null
$skillsPayload = $null
$providersPayload = $null
$logsPayload = $null
$adminErrors = @()

if (-not $NoAdminApi) {
  $adminKeyAvailable = [bool](Get-EnvValue 'BIFROST_ADMIN_KEY')
  if ($TestMode) { $adminKeyAvailable = $true }
  if ($adminKeyAvailable) {
    $endpoints = @(
      @{ name = 'version'; uri = "$BaseUrl/api/version"; fixture = $TestVersionPath },
      @{ name = 'config'; uri = "$BaseUrl/api/config?from_db=true"; fixture = $TestConfigPath },
      @{ name = 'plugins'; uri = "$BaseUrl/api/plugins"; fixture = $TestPluginsPath },
      @{ name = 'virtual_keys'; uri = "$BaseUrl/api/governance/virtual-keys"; fixture = $TestVirtualKeysPath },
      @{ name = 'routing_rules'; uri = "$BaseUrl/api/governance/routing-rules"; fixture = $TestRoutingRulesPath },
      @{ name = 'skills'; uri = "$BaseUrl/api/skills?limit=1"; fixture = $TestSkillsPath },
      @{ name = 'providers'; uri = "$BaseUrl/api/providers"; fixture = $TestProvidersPath },
      @{ name = 'logs'; uri = "$BaseUrl/api/logs?limit=1"; fixture = $TestLogsPath }
    )
    $responses = @{}
    foreach ($endpoint in $endpoints) {
      $response = Invoke-FeatureEndpoint $endpoint.name $endpoint.uri $true $endpoint.fixture
      $responses[$endpoint.name] = $response
      if (-not $response.available -and $response.error) { $adminErrors += $response.error }
    }
    $adminApiAvailable = @($responses.Values | Where-Object { $_.available }).Count -gt 0
    $versionPayload = $responses.version.payload
    $adminConfigPayload = $responses.config.payload
    $pluginsPayload = $responses.plugins.payload
    $virtualKeysPayload = $responses.virtual_keys.payload
    $routingRulesPayload = $responses.routing_rules.payload
    $skillsPayload = $responses.skills.payload
    $providersPayload = $responses.providers.payload
    $logsPayload = $responses.logs.payload
  } else {
    $adminErrors += 'BIFROST_ADMIN_KEY unavailable'
  }
}

$configFromAdmin = Get-PropertyValue $adminConfigPayload @('config', 'data')
$effectiveConfig = if ($null -ne $configFromAdmin) { $configFromAdmin } else { $localConfig }
$providerNames = Get-ProviderNames $providersPayload $effectiveConfig
$pluginSummaries = Get-PluginSummaries $pluginsPayload $effectiveConfig
$semanticCache = Get-SemanticCacheSummary $pluginSummaries $pluginsPayload $effectiveConfig
$virtualKeySummary = Get-VirtualKeySummaries $virtualKeysPayload $effectiveConfig
$routingRuleCount = Get-CountFromPayload $routingRulesPayload @('routing_rules', 'routingRules', 'rules', 'data', 'items') @('count', 'total')
$skillsRepositoryCount = Get-CountFromPayload $skillsPayload @('repositories', 'skills', 'data', 'items') @('repository_count', 'repositoryCount', 'total_repositories', 'totalRepositories', 'total')
$logsTotalRequests = Get-PropertyValue $logsPayload @('total_requests', 'totalRequests', 'total', 'count')
if ($null -eq $logsTotalRequests) { $logsTotalRequests = 0 }

$mcpConfig = Get-PropertyValue $effectiveConfig @('mcp')
$mcpClients = Get-ArrayValue $mcpConfig @('client_configs', 'clientConfigs')
$clientConfig = Get-PropertyValue $effectiveConfig @('client')
$toolManager = Get-PropertyValue $mcpConfig @('tool_manager_config', 'toolManagerConfig')
$mcpAutoInjectClientDisabled = [bool](Get-PropertyValue $clientConfig @('mcp_disable_auto_tool_inject', 'mcpDisableAutoToolInject'))
$mcpAutoInjectToolDisabled = [bool](Get-PropertyValue $toolManager @('disable_auto_tool_inject', 'disableAutoToolInject'))
$enforceAuth = [bool](Get-PropertyValue $clientConfig @('enforce_auth_on_inference', 'enforceAuthOnInference'))

$versionValue = Get-PropertyValue $versionPayload @('version', 'bifrost_version', 'bifrostVersion')
if (-not $versionValue -and ($versionPayload -is [string])) { $versionValue = $versionPayload }
if (-not $versionValue) { $versionValue = Get-PropertyValue $effectiveConfig @('version') }

$enterpriseOnlyNotEnabled = @()
foreach ($feature in @('guardrails', 'secret_management', 'edge', 'alerting')) {
  if (-not (Test-EnterpriseFeaturePresent $feature $pluginSummaries $effectiveConfig)) {
    $enterpriseOnlyNotEnabled += $feature
  }
}

$report = [ordered]@{
  schema = 'agentcore.bifrost.feature_adoption.v1'
  generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  repo_root = $RepoRoot
  runtime_root = $RuntimeRoot
  base_url = $BaseUrl
  read_only = $true
  admin_api_available = [bool]$adminApiAvailable
  admin_api_skipped = [bool]$NoAdminApi
  admin_errors = @($adminErrors | Sort-Object -Unique)
  version = ConvertTo-SecretSafeScalar $versionValue
  gateway_health = [pscustomobject]@{
    available = [bool]$healthResult.available
    status = ConvertTo-SecretSafeScalar (Get-PropertyValue $healthResult.payload @('status', 'state', 'health'))
  }
  local_config_present = [bool]($null -ne $localConfig)
  provider_count = $providerNames.Count
  provider_names = @($providerNames)
  plugin_names = @($pluginSummaries | ForEach-Object { $_.name } | Sort-Object -Unique)
  plugin_statuses = @($pluginSummaries)
  semantic_cache = $semanticCache
  virtual_key_count = $virtualKeySummary.count
  virtual_key_names = $virtualKeySummary.names
  virtual_key_provider_config_summary = $virtualKeySummary.provider_config_summary
  virtual_key_mcp_config_summary = $virtualKeySummary.mcp_config_summary
  routing_rule_count = $routingRuleCount
  routing_rules_adopted = [bool]($routingRuleCount -gt 0)
  skills_repository_count = $skillsRepositoryCount
  skills_repository_adopted = [bool]($skillsRepositoryCount -gt 0)
  logs_total_requests = [int64]$logsTotalRequests
  inference_traffic_observed = [bool]([int64]$logsTotalRequests -gt 0)
  mcp_client_count = $mcpClients.Count
  mcp_auto_tool_inject_disabled = [bool]($mcpAutoInjectClientDisabled -or $mcpAutoInjectToolDisabled)
  enforce_auth_on_inference = $enforceAuth
  enterprise_only_not_enabled = @($enterpriseOnlyNotEnabled)
}

$report | ConvertTo-Json -Depth 100
