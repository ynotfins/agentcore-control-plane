<#
.SYNOPSIS
  Installs the exact AgentCore research MCP dependency set into its governed runtime root.

.DESCRIPTION
  Verifies the pinned Node binary, source package lock, direct package versions, integrity
  metadata, entry points, and absence of native addons. Installation uses a same-volume
  staging directory and atomic rename, with both an external backup and a same-volume
  rollback directory when a prior runtime exists. No provider tool is invoked.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'D:\github\agentcore-control-plane',
  [string]$RuntimeRoot = 'F:\AgentCore\runtime\mcp-processes\research-mcp',
  [string]$BackupRoot = 'E:\AgentCore\Backups\research-mcp',
  [string]$NodePath = 'C:\Users\ynotf\AppData\Local\pnpm\bin\node.exe',
  [string]$NpmCliPath = 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js',
  [string]$ExpectedNodeVersion = 'v24.16.0',
  [string]$ExpectedNodeSha256 = 'b3094d0b49f9ad602262a9921551737bb97637c05dd357a06ae98188d7290aa3',
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$sourceRoot = Join-Path $RepoRoot 'tools\research-mcp'
$packagePath = Join-Path $sourceRoot 'package.json'
$lockPath = Join-Path $sourceRoot 'package-lock.json'
$expectedPackages = [ordered]@{
  '@apify/actors-mcp-server' = [ordered]@{ Version = '0.15.4'; EntryPoint = 'dist\stdio.js' }
  'exa-mcp-server'           = [ordered]@{ Version = '3.4.1'; EntryPoint = 'dist\stdio.cjs' }
  'firecrawl-mcp'            = [ordered]@{ Version = '3.24.0'; EntryPoint = 'dist\index.js' }
  'tavily-mcp'               = [ordered]@{ Version = '0.2.22'; EntryPoint = 'build\index.js' }
}

function Get-PackageNodePath([string]$Root, [string]$PackageName) {
  $segments = $PackageName -split '/'
  $path = Join-Path $Root 'node_modules'
  foreach ($segment in $segments) { $path = Join-Path $path $segment }
  return $path
}

function Assert-PathWithin([string]$Parent, [string]$Child) {
  $parentFull = [IO.Path]::GetFullPath($Parent).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
  $childFull = [IO.Path]::GetFullPath($Child)
  $prefix = $parentFull + [IO.Path]::DirectorySeparatorChar
  if (-not $childFull.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "RESEARCH_MCP_PATH_OUTSIDE_BOUNDARY parent=$parentFull child=$childFull"
  }
}

function Assert-SourceLock {
  foreach ($path in @($packagePath, $lockPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "RESEARCH_MCP_SOURCE_MISSING $path" }
  }
  $package = Get-Content -Raw -LiteralPath $packagePath | ConvertFrom-Json -AsHashtable
  $lock = Get-Content -Raw -LiteralPath $lockPath | ConvertFrom-Json -AsHashtable
  if ([int]$lock.lockfileVersion -ne 3) { throw 'RESEARCH_MCP_LOCKFILE_VERSION_MISMATCH' }
  if ($package.dependencies.Count -ne $expectedPackages.Count) { throw 'RESEARCH_MCP_DIRECT_DEPENDENCY_COUNT_MISMATCH' }
  foreach ($name in $expectedPackages.Keys) {
    $expected = $expectedPackages[$name]
    if ([string]$package.dependencies[$name] -ne [string]$expected.Version) {
      throw "RESEARCH_MCP_PACKAGE_PIN_MISMATCH $name"
    }
    $lockKey = "node_modules/$name"
    $locked = $lock.packages[$lockKey]
    if ($null -eq $locked -or [string]$locked.version -ne [string]$expected.Version) {
      throw "RESEARCH_MCP_LOCK_PIN_MISMATCH $name"
    }
    if ([string]::IsNullOrWhiteSpace([string]$locked.integrity) -or -not ([string]$locked.integrity).StartsWith('sha512-')) {
      throw "RESEARCH_MCP_LOCK_INTEGRITY_MISSING $name"
    }
  }
  if ($package.dependencies.ContainsKey('@brightdata/mcp') -or $lock.packages.ContainsKey('node_modules/@brightdata/mcp')) {
    throw 'RESEARCH_MCP_BRIGHTDATA_MUST_REMAIN_UNINSTALLED'
  }
}

function Assert-NodeRuntime {
  foreach ($path in @($NodePath, $NpmCliPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "RESEARCH_MCP_RUNTIME_DEPENDENCY_MISSING $path" }
  }
  $version = (& $NodePath --version 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0 -or $version -ne $ExpectedNodeVersion) {
    throw "RESEARCH_MCP_NODE_VERSION_MISMATCH expected=$ExpectedNodeVersion actual=$version"
  }
  $hash = (Get-FileHash -LiteralPath $NodePath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hash -ne $ExpectedNodeSha256.ToLowerInvariant()) { throw 'RESEARCH_MCP_NODE_HASH_MISMATCH' }
}

function Assert-InstalledRuntime([string]$Root) {
  foreach ($name in $expectedPackages.Keys) {
    $expected = $expectedPackages[$name]
    $packageRoot = Get-PackageNodePath $Root $name
    $installedPackagePath = Join-Path $packageRoot 'package.json'
    $entryPointPath = Join-Path $packageRoot $expected.EntryPoint
    if (-not (Test-Path -LiteralPath $installedPackagePath -PathType Leaf)) {
      throw "RESEARCH_MCP_INSTALLED_PACKAGE_MISSING $name"
    }
    $installed = Get-Content -Raw -LiteralPath $installedPackagePath | ConvertFrom-Json
    if ([string]$installed.version -ne [string]$expected.Version) {
      throw "RESEARCH_MCP_INSTALLED_VERSION_MISMATCH $name"
    }
    if (-not (Test-Path -LiteralPath $entryPointPath -PathType Leaf)) {
      throw "RESEARCH_MCP_ENTRYPOINT_MISSING $name"
    }
  }
  $nativeArtifacts = @(Get-ChildItem -LiteralPath (Join-Path $Root 'node_modules') -Recurse -File -Filter '*.node' -ErrorAction Stop)
  if ($nativeArtifacts.Count -gt 0) { throw 'RESEARCH_MCP_NATIVE_ARTIFACT_DETECTED' }
}

function Get-ReviewedEnvironmentValue([string]$Name) {
  $value = [Environment]::GetEnvironmentVariable($Name, 'Process')
  if ([string]::IsNullOrWhiteSpace($value)) {
    $value = [Environment]::GetEnvironmentVariable($Name, 'User')
  }
  if ([string]::IsNullOrWhiteSpace($value)) { throw "RESEARCH_MCP_REQUIRED_ENV_MISSING $Name" }
  return $value
}

function Invoke-LocalMcpToolsList(
  [string]$Root,
  [string]$PackageName,
  [string]$EntryPoint,
  [string[]]$Arguments,
  [hashtable]$EnvironmentAliases
) {
  $entryPointPath = Join-Path (Get-PackageNodePath $Root $PackageName) $EntryPoint
  $startInfo = [Diagnostics.ProcessStartInfo]::new()
  $startInfo.FileName = $NodePath
  $startInfo.WorkingDirectory = $Root
  $startInfo.UseShellExecute = $false
  $startInfo.RedirectStandardInput = $true
  $startInfo.RedirectStandardOutput = $true
  $startInfo.RedirectStandardError = $true
  $startInfo.CreateNoWindow = $true
  $startInfo.ArgumentList.Add($entryPointPath)
  foreach ($argument in $Arguments) { $startInfo.ArgumentList.Add($argument) }
  $startInfo.Environment.Clear()
  foreach ($name in @('SystemRoot', 'WINDIR', 'ComSpec', 'TEMP', 'TMP', 'PATH', 'PATHEXT', 'USERPROFILE')) {
    $value = [Environment]::GetEnvironmentVariable($name, 'Process')
    if (-not [string]::IsNullOrWhiteSpace($value)) { $startInfo.Environment[$name] = $value }
  }
  foreach ($childName in $EnvironmentAliases.Keys) {
    $startInfo.Environment[$childName] = Get-ReviewedEnvironmentValue $EnvironmentAliases[$childName]
  }
  if ($PackageName -eq 'exa-mcp-server') { $startInfo.Environment['AGNOST_DISABLE_LOGS'] = 'true' }

  $process = [Diagnostics.Process]::new()
  $process.StartInfo = $startInfo
  try {
    if (-not $process.Start()) { throw "RESEARCH_MCP_INVENTORY_START_FAILED $PackageName" }
    $initialize = [ordered]@{
      jsonrpc = '2.0'
      id = 1
      method = 'initialize'
      params = [ordered]@{
        protocolVersion = '2025-06-18'
        capabilities = @{}
        clientInfo = [ordered]@{ name = 'agentcore-research-installer'; version = '1.0.0' }
      }
    } | ConvertTo-Json -Depth 8 -Compress
    $initialized = @{ jsonrpc = '2.0'; method = 'notifications/initialized'; params = @{} } | ConvertTo-Json -Compress
    $listTools = @{ jsonrpc = '2.0'; id = 2; method = 'tools/list'; params = @{} } | ConvertTo-Json -Compress
    $process.StandardInput.WriteLine($initialize)
    $process.StandardInput.WriteLine($initialized)
    $process.StandardInput.WriteLine($listTools)
    $process.StandardInput.Flush()

    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    while ([DateTime]::UtcNow -lt $deadline) {
      $remaining = [int][Math]::Max(1, ($deadline - [DateTime]::UtcNow).TotalMilliseconds)
      $readTask = $process.StandardOutput.ReadLineAsync()
      if (-not $readTask.Wait($remaining)) { break }
      $line = $readTask.Result
      if ([string]::IsNullOrWhiteSpace($line)) {
        if ($process.HasExited) { break }
        continue
      }
      try { $message = $line | ConvertFrom-Json -ErrorAction Stop } catch { continue }
      if ([int]$message.id -eq 2) {
        if ($null -ne $message.error) { throw "RESEARCH_MCP_INVENTORY_PROTOCOL_ERROR $PackageName" }
        return @($message.result.tools | ForEach-Object { [string]$_.name } | Sort-Object -Unique)
      }
    }
    throw "RESEARCH_MCP_INVENTORY_TIMEOUT $PackageName"
  } finally {
    if (-not $process.HasExited) { $process.Kill($true) }
    $process.Dispose()
  }
}

function Assert-ToolInventories([string]$Root) {
  $inventorySpecs = @(
    [ordered]@{
      Package = 'exa-mcp-server'; EntryPoint = 'dist\stdio.cjs'; Arguments = @()
      Environment = @{ EXA_API_KEY = 'EXA_API_KEY' }
      Expected = @('web_fetch_exa', 'web_search_exa')
    },
    [ordered]@{
      Package = 'tavily-mcp'; EntryPoint = 'build\index.js'; Arguments = @()
      Environment = @{ TAVILY_API_KEY = 'TAVILY_API_KEY' }
      Expected = @('tavily_crawl', 'tavily_extract', 'tavily_map', 'tavily_research', 'tavily_search')
    },
    [ordered]@{
      Package = 'firecrawl-mcp'; EntryPoint = 'dist\index.js'; Arguments = @()
      Environment = @{ FIRECRAWL_API_KEY = 'FIRECRAWL_API_KEY' }
      Expected = @(
        'firecrawl_agent', 'firecrawl_agent_status', 'firecrawl_check_crawl_status', 'firecrawl_crawl',
        'firecrawl_developer_search', 'firecrawl_extract', 'firecrawl_feedback', 'firecrawl_interact',
        'firecrawl_interact_stop', 'firecrawl_map', 'firecrawl_monitor_check', 'firecrawl_monitor_checks',
        'firecrawl_monitor_create', 'firecrawl_monitor_delete', 'firecrawl_monitor_get', 'firecrawl_monitor_list',
        'firecrawl_monitor_run', 'firecrawl_monitor_update', 'firecrawl_parse',
        'firecrawl_research_inspect_paper', 'firecrawl_research_read_paper',
        'firecrawl_research_related_papers', 'firecrawl_research_search_github',
        'firecrawl_research_search_papers', 'firecrawl_scrape', 'firecrawl_search',
        'firecrawl_search_feedback'
      )
    },
    [ordered]@{
      Package = '@apify/actors-mcp-server'; EntryPoint = 'dist\stdio.js'
      Arguments = @(
        '--tools', 'search-actors,fetch-actor-details,call-actor,search-apify-docs,fetch-apify-docs',
        '--telemetry-enabled=false', '--ui=default'
      )
      Environment = @{ APIFY_TOKEN = 'APIFY_API_KEY' }
      Expected = @(
        'abort-actor-run', 'call-actor', 'fetch-actor-details', 'fetch-apify-docs',
        'get-actor-run', 'get-dataset-items', 'get-key-value-store-record',
        'search-actors', 'search-apify-docs'
      )
    }
  )
  $result = [ordered]@{}
  foreach ($spec in $inventorySpecs) {
    $actual = @(Invoke-LocalMcpToolsList $Root $spec.Package $spec.EntryPoint $spec.Arguments $spec.Environment)
    $expected = @($spec.Expected | Sort-Object -Unique)
    if ((Compare-Object -ReferenceObject $expected -DifferenceObject $actual).Count -ne 0) {
      throw "RESEARCH_MCP_TOOL_INVENTORY_MISMATCH $($spec.Package) expected=$($expected.Count) actual=$($actual.Count)"
    }
    $result[$spec.Package] = $actual
  }
  return $result
}

Assert-SourceLock
Assert-NodeRuntime

$sourceHashes = [ordered]@{
  package_json = (Get-FileHash -LiteralPath $packagePath -Algorithm SHA256).Hash.ToLowerInvariant()
  package_lock_json = (Get-FileHash -LiteralPath $lockPath -Algorithm SHA256).Hash.ToLowerInvariant()
}

if ($DryRun) {
  [ordered]@{
    status = 'dry_run_passed'
    runtime_root = $RuntimeRoot
    backup_root = $BackupRoot
    node_version = $ExpectedNodeVersion
    node_sha256 = $ExpectedNodeSha256
    install_command = 'node npm-cli.js ci --omit=dev --ignore-scripts --no-audit --no-fund'
    packages = $expectedPackages
    source_hashes = $sourceHashes
    provider_calls = 0
  } | ConvertTo-Json -Depth 8
  exit 0
}

$runtimeParent = Split-Path -Parent $RuntimeRoot
$runtimeLeaf = Split-Path -Leaf $RuntimeRoot
$transactionId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffffffZ')
$stagingRoot = Join-Path $runtimeParent "$runtimeLeaf.staging-$transactionId"
$rollbackRoot = Join-Path $runtimeParent "$runtimeLeaf.rollback-$transactionId"
$backupDirectory = Join-Path $BackupRoot $transactionId
$priorMoved = $false
$newActivated = $false

Assert-PathWithin $runtimeParent $RuntimeRoot
Assert-PathWithin $runtimeParent $stagingRoot
Assert-PathWithin $runtimeParent $rollbackRoot
Assert-PathWithin $BackupRoot $backupDirectory

try {
  New-Item -ItemType Directory -Path $runtimeParent -Force | Out-Null
  if (Test-Path -LiteralPath $stagingRoot) { throw 'RESEARCH_MCP_STAGING_COLLISION' }
  New-Item -ItemType Directory -Path $stagingRoot | Out-Null
  Copy-Item -LiteralPath $packagePath -Destination (Join-Path $stagingRoot 'package.json')
  Copy-Item -LiteralPath $lockPath -Destination (Join-Path $stagingRoot 'package-lock.json')

  Push-Location $stagingRoot
  try {
    & $NodePath $NpmCliPath ci --omit=dev --ignore-scripts --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "RESEARCH_MCP_NPM_CI_FAILED exit=$LASTEXITCODE" }
  } finally {
    Pop-Location
  }
  Assert-InstalledRuntime $stagingRoot
  $verifiedToolInventories = Assert-ToolInventories $stagingRoot

  New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
  if (Test-Path -LiteralPath $RuntimeRoot) {
    Copy-Item -LiteralPath $RuntimeRoot -Destination (Join-Path $backupDirectory 'runtime-before') -Recurse
    Move-Item -LiteralPath $RuntimeRoot -Destination $rollbackRoot
    $priorMoved = $true
  }
  Move-Item -LiteralPath $stagingRoot -Destination $RuntimeRoot
  $newActivated = $true
  Assert-InstalledRuntime $RuntimeRoot

  $manifest = [ordered]@{
    schema_version = 1
    installed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    runtime_root = $RuntimeRoot
    rollback_root = if ($priorMoved) { $rollbackRoot } else { $null }
    node_path = $NodePath
    node_version = $ExpectedNodeVersion
    node_sha256 = $ExpectedNodeSha256
    source_hashes = $sourceHashes
    packages = $expectedPackages
    tool_inventories = $verifiedToolInventories
    npm_lifecycle_scripts = 'disabled'
    native_artifacts = 0
    provider_calls = 0
  }
  $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $backupDirectory 'INSTALL_MANIFEST.json') -Encoding utf8
  Write-Host "RESEARCH_MCP_INSTALL_PASS runtime=$RuntimeRoot backup=$backupDirectory"
} catch {
  $originalFailure = $_
  if ($newActivated -and (Test-Path -LiteralPath $RuntimeRoot)) {
    Remove-Item -LiteralPath $RuntimeRoot -Recurse -Force
  }
  if ($priorMoved -and (Test-Path -LiteralPath $rollbackRoot)) {
    Move-Item -LiteralPath $rollbackRoot -Destination $RuntimeRoot
  }
  if (Test-Path -LiteralPath $stagingRoot) {
    Remove-Item -LiteralPath $stagingRoot -Recurse -Force
  }
  throw $originalFailure
}
