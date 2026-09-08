<#
.SYNOPSIS
  Reconcile the bounded Trust Class A client MCP configurations.

.DESCRIPTION
  Dry-run is the default. Apply performs same-directory atomic replacements and
  creates one per-file Phase 2 rollback copy. Secret values are never emitted.
#>
[CmdletBinding(DefaultParameterSetName = 'DryRun')]
param(
  [Parameter(ParameterSetName = 'DryRun')]
  [switch]$DryRun,

  [Parameter(ParameterSetName = 'Apply')]
  [switch]$Apply,

  [switch]$TestMode,

  [string]$FixtureRoot = '',

  [int]$TestFailAfterWrites = 0
)

$ErrorActionPreference = 'Stop'
$GatewayUrl = 'http://127.0.0.1:8080/mcp'
$CompatGatewayUrl = 'http://127.0.0.1:18082/mcp'
$GatewayEnvironmentVariable = 'BIFROST_MCP_VIRTUAL_KEY'

function Get-Sha256([string]$Text) {
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
  return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
}

function Get-JsonText($Value) {
  return (($Value | ConvertTo-Json -Depth 100) + "`n")
}

function Read-JsonFile([string]$Path) {
  try {
    return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable -Depth 100)
  } catch {
    throw "Invalid JSON in required client configuration: $Path"
  }
}

function Resolve-TomlPython {
  $repoPython = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\scripts\.venv\Scripts\python.exe'))
  if (Test-Path -LiteralPath $repoPython -PathType Leaf) {
    return $repoPython
  }
  $command = Get-Command python.exe -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }
  throw 'A Python 3.11+ interpreter is required for fail-closed TOML validation.'
}

function Assert-ValidToml([string]$Text, [string]$Path, [string]$PythonPath) {
  $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
  $startInfo.FileName = $PythonPath
  $startInfo.UseShellExecute = $false
  $startInfo.RedirectStandardInput = $true
  $startInfo.RedirectStandardOutput = $true
  $startInfo.RedirectStandardError = $true
  [void]$startInfo.ArgumentList.Add('-c')
  [void]$startInfo.ArgumentList.Add('import sys,tomllib; tomllib.loads(sys.stdin.read())')
  $process = [System.Diagnostics.Process]::new()
  $process.StartInfo = $startInfo
  [void]$process.Start()
  $process.StandardInput.Write($Text)
  $process.StandardInput.Close()
  $process.StandardOutput.ReadToEnd() | Out-Null
  $process.StandardError.ReadToEnd() | Out-Null
  $process.WaitForExit()
  if ($process.ExitCode -ne 0) {
    throw "Invalid TOML in required client configuration: $Path"
  }
}

function Edit-TomlMcpTables(
  [string]$Text,
  [string[]]$RemoveRoots,
  [string]$GatewayReplacement
) {
  $newline = if ($Text.Contains("`r`n")) { "`r`n" } else { "`n" }
  $hadFinalNewline = $Text.EndsWith("`n")
  $lines = @($Text -split "`r?`n")
  if ($hadFinalNewline -and $lines.Count -gt 0 -and $lines[-1] -eq '') {
    $lines = @($lines[0..($lines.Count - 2)])
  }

  $output = [System.Collections.Generic.List[string]]::new()
  $skip = $false
  $gatewaySeen = $false
  foreach ($line in $lines) {
    $match = [regex]::Match($line, '^\s*\[([^\[\]]+)\]\s*(?:#.*)?$')
    if ($match.Success) {
      $section = $match.Groups[1].Value.Trim()
      if ($section -eq 'mcp_servers.agentcore-gateway') {
        if ($gatewaySeen) {
          throw 'Duplicate agentcore-gateway TOML table.'
        }
        $gatewaySeen = $true
        $skip = $true
        foreach ($replacementLine in @($GatewayReplacement -split "`r?`n")) {
          $output.Add($replacementLine)
        }
        continue
      }

      $remove = $false
      foreach ($root in $RemoveRoots) {
        if ($section -eq $root -or $section.StartsWith("$root.", [StringComparison]::Ordinal)) {
          $remove = $true
          break
        }
      }
      $skip = $remove
    }
    if (-not $skip) {
      $output.Add($line)
    }
  }

  if (-not $gatewaySeen) {
    if ($output.Count -gt 0 -and $output[-1] -ne '') {
      $output.Add('')
    }
    foreach ($replacementLine in @($GatewayReplacement -split "`r?`n")) {
      $output.Add($replacementLine)
    }
  }

  $result = [string]::Join($newline, $output)
  if ($hadFinalNewline) {
    $result += $newline
  }
  return $result
}

function Assert-Hashtable($Value, [string]$Description) {
  if ($Value -isnot [System.Collections.IDictionary]) {
    throw "Required object is missing or invalid: $Description"
  }
}

function Assert-GatewayUrl($Gateway, [string]$PropertyName, [string]$Client) {
  Assert-Hashtable $Gateway "$Client agentcore-gateway"
  if ([string]$Gateway[$PropertyName] -ne $GatewayUrl) {
    throw "$Client agentcore-gateway has an unexpected URL schema."
  }
}

function New-Target([string]$Client, [string]$Path, [ValidateSet('json', 'toml')] [string]$Format) {
  return [ordered]@{ client = $Client; path = $Path; format = $Format }
}

function Get-Targets {
  if ($TestMode) {
    if ([string]::IsNullOrWhiteSpace($FixtureRoot)) {
      throw '-FixtureRoot is required with -TestMode.'
    }
    $root = [System.IO.Path]::GetFullPath($FixtureRoot)
    if (-not (Test-Path -LiteralPath $root -PathType Container)) {
      throw "Fixture root does not exist: $root"
    }
    $relative = [ordered]@{
      cursor = 'cursor\mcp.json'
      codex = 'codex\config.toml'
      devin = 'devin\mcp_config.json'
      'antigravity-primary' = 'gemini\mcp_config.json'
      'antigravity-alternate' = 'antigravity\mcp.json'
      zcode = 'zcode\config.json'
      minimax = 'minimax\mcp.json'
      'open-interpreter-desktop' = 'open-interpreter-desktop\config.json'
      'open-interpreter-cli' = 'open-interpreter-cli\config.toml'
    }
    $formats = @{ codex = 'toml'; 'open-interpreter-cli' = 'toml' }
    $targets = @()
    foreach ($client in $relative.Keys) {
      $path = [System.IO.Path]::GetFullPath((Join-Path $root $relative[$client]))
      if (-not $path.StartsWith($root + [System.IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Fixture target escaped the fixture root: $client"
      }
      $format = if ($formats.ContainsKey($client)) { $formats[$client] } else { 'json' }
      $targets += New-Target $client $path $format
    }
    return $targets
  }

  if (-not [string]::IsNullOrWhiteSpace($FixtureRoot)) {
    throw '-FixtureRoot is available only with -TestMode.'
  }
  return @(
    (New-Target 'cursor' 'C:\Users\ynotf\.cursor\mcp.json' 'json'),
    (New-Target 'codex' 'C:\Users\ynotf\.codex\config.toml' 'toml'),
    (New-Target 'devin' 'C:\Users\ynotf\AppData\Roaming\devin\mcp_config.json' 'json'),
    (New-Target 'antigravity-primary' 'C:\Users\ynotf\.gemini\config\mcp_config.json' 'json'),
    (New-Target 'antigravity-alternate' 'C:\Users\ynotf\AppData\Roaming\Antigravity IDE\User\mcp.json' 'json'),
    (New-Target 'zcode' 'C:\Users\ynotf\.zcode\cli\config.json' 'json'),
    (New-Target 'minimax' 'C:\Users\ynotf\.minimax\mcp\mcp.json' 'json'),
    (New-Target 'open-interpreter-desktop' 'C:\Users\ynotf\AppData\Roaming\interpreter\config.json' 'json'),
    (New-Target 'open-interpreter-cli' 'C:\Users\ynotf\.openinterpreter\config.toml' 'toml')
  )
}

function Get-VirtualKey {
  $scope = if ($TestMode) { [EnvironmentVariableTarget]::Process } else { [EnvironmentVariableTarget]::User }
  $value = [Environment]::GetEnvironmentVariable($GatewayEnvironmentVariable, $scope)
  if ([string]::IsNullOrWhiteSpace($value)) {
    throw "$GatewayEnvironmentVariable is unavailable in the required environment scope."
  }
  return $value
}

function Get-ReconciledJson([string]$Client, $Config, [string]$Original, [string]$VirtualKey) {
  Assert-Hashtable $Config "$Client root"
  switch ($Client) {
    'cursor' {
      Assert-Hashtable $Config.mcpServers 'cursor mcpServers'
      if ($Config.mcpServers.Count -ne 1 -or -not $Config.mcpServers.Contains('agentcore-gateway')) {
        throw 'Cursor must contain exactly one agentcore-gateway MCP server.'
      }
      $gateway = $Config.mcpServers['agentcore-gateway']
      Assert-GatewayUrl $gateway 'url' 'Cursor'
      if ([string]$gateway.headers.Authorization -ne 'Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}') {
        throw 'Cursor agentcore-gateway must use the approved environment reference.'
      }
      return $Original
    }
    'devin' {
      Assert-Hashtable $Config.mcpServers 'Devin mcpServers'
      $gateway = $Config.mcpServers['agentcore-gateway']
      foreach ($name in @('devin/mcp-playwright', 'github-mcp-server', 'vercel')) {
        [void]$Config.mcpServers.Remove($name)
      }
      $gateway.url = $CompatGatewayUrl
      [void]$gateway.Remove('headers')
      return Get-JsonText $Config
    }
    { $_ -in @('antigravity-primary', 'antigravity-alternate') } {
      Assert-Hashtable $Config.mcpServers "$Client mcpServers"
      $gateway = $Config.mcpServers['agentcore-gateway']
      $gateway.serverUrl = $CompatGatewayUrl
      [void]$gateway.Remove('headers')
      return Get-JsonText $Config
    }
    'zcode' {
      Assert-Hashtable $Config.mcp 'ZCode mcp'
      Assert-Hashtable $Config.mcp.servers 'ZCode mcp.servers'
      $existingClaude = $Config.mcp.servers['claude-context']
      $servers = [ordered]@{
        'agentcore-gateway' = [ordered]@{
          type = 'http'
          url = $CompatGatewayUrl
          timeoutMs = 300000
          enabled = $true
        }
      }
      if ($null -ne $existingClaude) {
        $servers['claude-context'] = $existingClaude
      }
      $Config.mcp.servers = $servers
      return Get-JsonText $Config
    }
    'minimax' {
      Assert-Hashtable $Config.mcpServers 'MiniMax mcpServers'
      foreach ($name in @('matrix', 'cu', 'trash', 'agentcore-gateway')) {
        if (-not $Config.mcpServers.Contains($name)) {
          throw "MiniMax is missing required MCP server: $name"
        }
      }
      $gateway = $Config.mcpServers['agentcore-gateway']
      $gateway.url = $CompatGatewayUrl
      [void]$gateway.Remove('headers')
      return Get-JsonText $Config
    }
    'open-interpreter-desktop' {
      Assert-Hashtable $Config.mcpServers 'Open Interpreter desktop mcpServers'
      if ($Config.mcpServers.Count -ne 1 -or -not $Config.mcpServers.Contains('agentcore-gateway')) {
        throw 'Open Interpreter desktop must contain exactly one agentcore-gateway MCP server.'
      }
      $gateway = $Config.mcpServers['agentcore-gateway']
      $gateway.url = $CompatGatewayUrl
      [void]$gateway.Remove('headers')
      return Get-JsonText $Config
    }
    default { throw "Unsupported JSON client: $Client" }
  }
}

function Get-ReconciledToml([string]$Client, [string]$Original) {
  if ($Client -eq 'codex') {
    $gateway = @(
      '[mcp_servers.agentcore-gateway]'
      "url = `"$GatewayUrl`""
      'bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"'
      'startup_timeout_sec = 300.0'
      'tool_timeout_sec = 300.0'
    ) -join "`n"
    return Edit-TomlMcpTables $Original @('mcp_servers.morph-mcp') $gateway
  }
  if ($Client -eq 'open-interpreter-cli') {
    $gateway = @(
      '[mcp_servers.agentcore-gateway]'
      "url = `"$GatewayUrl`""
      'bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"'
      'default_tools_approval_mode = "prompt"'
      'enabled = true'
      'startup_timeout_sec = 300.0'
      'tool_timeout_sec = 300.0'
    ) -join "`n"
    return Edit-TomlMcpTables $Original @(
      'mcp_servers.morph-mcp',
      'mcp_servers.openrouter',
      'mcp_servers.github'
    ) $gateway
  }
  throw "Unsupported TOML client: $Client"
}

function Write-AtomicReplacement([string]$Path, [string]$Text, [string]$BackupPath) {
  $directory = Split-Path -Parent $Path
  $tempPath = Join-Path $directory ('.' + [System.IO.Path]::GetFileName($Path) + '.phase2-' + [Guid]::NewGuid().ToString('N') + '.tmp')
  try {
    [System.IO.File]::WriteAllText($tempPath, $Text, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::Replace($tempPath, $Path, $BackupPath, $true)
  } catch {
    if (Test-Path -LiteralPath $tempPath -PathType Leaf) {
      Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
    }
    throw "Atomic replacement failed for required client configuration: $Path"
  }
}

$targets = @(Get-Targets)
foreach ($target in $targets) {
  if (-not (Test-Path -LiteralPath $target.path -PathType Leaf)) {
    throw "Required client configuration is missing: $($target.path)"
  }
  $item = Get-Item -LiteralPath $target.path -Force
  if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw "Required client configuration cannot be a reparse point: $($target.path)"
  }
}

$virtualKey = Get-VirtualKey
$tomlPython = Resolve-TomlPython
$plans = [System.Collections.Generic.List[object]]::new()

# Preflight and transform every file before any write.
foreach ($target in $targets) {
  $original = Get-Content -LiteralPath $target.path -Raw -Encoding UTF8
  if ($target.format -eq 'json') {
    $config = Read-JsonFile $target.path
    $updated = Get-ReconciledJson $target.client $config $original $virtualKey
    try {
      $null = $updated | ConvertFrom-Json -AsHashtable -Depth 100
    } catch {
      throw "Reconciled JSON failed validation for client: $($target.client)"
    }
  } else {
    Assert-ValidToml $original $target.path $tomlPython
    $updated = Get-ReconciledToml $target.client $original
    Assert-ValidToml $updated $target.path $tomlPython
  }
  $plans.Add([ordered]@{
    client = $target.client
    path = $target.path
    original = $original
    updated = $updated
    before_sha256 = Get-Sha256 $original
    after_sha256 = Get-Sha256 $updated
    changed = ($original -cne $updated)
    backup_path = $null
  })
}

$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
if ($Apply) {
  foreach ($plan in @($plans | Where-Object changed)) {
    $backupPath = "$($plan.path).phase2-$stamp.bak"
    if (Test-Path -LiteralPath $backupPath) {
      throw "Refusing to overwrite an existing Phase 2 rollback copy: $backupPath"
    }
    $plan.backup_path = $backupPath
  }
  $applied = [System.Collections.Generic.List[object]]::new()
  try {
    foreach ($plan in @($plans | Where-Object changed)) {
      Write-AtomicReplacement $plan.path $plan.updated $plan.backup_path
      $applied.Add($plan)
      if ($TestMode -and $TestFailAfterWrites -gt 0 -and $applied.Count -eq $TestFailAfterWrites) {
        throw 'Injected Trust Class A batch failure.'
      }
    }
  } catch {
    $originalFailure = $_
    $rollbackFailures = [System.Collections.Generic.List[string]]::new()
    for ($rollbackIndex = $applied.Count - 1; $rollbackIndex -ge 0; $rollbackIndex--) {
      $plan = $applied[$rollbackIndex]
      try {
        [IO.File]::Copy($plan.backup_path, $plan.path, $true)
        $restoredHash = (Get-FileHash -LiteralPath $plan.path -Algorithm SHA256).Hash
        $backupHash = (Get-FileHash -LiteralPath $plan.backup_path -Algorithm SHA256).Hash
        if ($restoredHash -ne $backupHash) { throw 'restored hash mismatch' }
      } catch {
        $rollbackFailures.Add([string]$plan.path)
      }
    }
    if ($rollbackFailures.Count -gt 0) {
      throw "Trust Class A batch failed and rollback verification failed for $($rollbackFailures.Count) file(s)."
    }
    throw $originalFailure
  }
}

$fileReport = @($plans | ForEach-Object {
  [ordered]@{
    client = $_.client
    path = $_.path
    changed = $_.changed
    before_sha256 = $_.before_sha256
    after_sha256 = $_.after_sha256
    backup_path = $_.backup_path
  }
})
$report = [ordered]@{
  schema_version = 1
  mode = if ($Apply) { 'Apply' } else { 'DryRun' }
  changed_count = @($plans | Where-Object changed).Count
  files = $fileReport
}
$report | ConvertTo-Json -Depth 8
