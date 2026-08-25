#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$LauncherRoot = 'D:\launchers\open-interpreter'
$ExpectedCodexHash = '4F336B55E891F56483801463FEDBD95A4E027EC341ABC20C755369460E0F64E4'
$CodexConfig = Join-Path $env:USERPROFILE '.codex\config.toml'
$DesktopHome = Join-Path $env:USERPROFILE '.openinterpreter'
$CliHome = Join-Path $env:USERPROFILE '.openinterpreter-cli'
$RepoRoot = 'D:\github\agentcore-control-plane'
$GatewayHealthUrl = 'http://127.0.0.1:8080/health'
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$RollbackRoot = Join-Path $LauncherRoot "rollback-$Timestamp"
function Get-Sha256Hex([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}
function Save-Previous([string]$SourcePath, [string]$DestDir) {
  if (-not (Test-Path -LiteralPath $SourcePath)) { return $false }
  [void][System.IO.Directory]::CreateDirectory($DestDir)
  $leaf = Split-Path -Leaf $SourcePath
  $dest = Join-Path $DestDir $leaf
  $bytes = [System.IO.File]::ReadAllBytes($SourcePath)
  [System.IO.File]::WriteAllBytes($dest, $bytes)
  return $true
}
$evidence = [ordered]@{
  applied_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  launcher_root = $LauncherRoot
  rollback_dir = $RollbackRoot
  codex_config_path = $CodexConfig
  codex_hash_before = $null
  codex_hash_after = $null
  codex_hash_expected = $ExpectedCodexHash
  codex_hash_unchanged = $false
  backups = @()
  validations = [ordered]@{}
  success = $false
  exit_code = 1
}
function Deploy-File([string]$Source, [string]$Target) {
  $parent = Split-Path -Parent $Target
  if ($parent) { [void][System.IO.Directory]::CreateDirectory($parent) }
  $bytes = [System.IO.File]::ReadAllBytes($Source)
  [System.IO.File]::WriteAllBytes($Target, $bytes)
}
try {
  if (-not (Test-Path -LiteralPath (Join-Path $LauncherRoot 'desktop-config.toml'))) { throw 'Missing desktop-config.toml' }
  if (-not (Test-Path -LiteralPath (Join-Path $LauncherRoot 'cli-config.toml'))) { throw 'Missing cli-config.toml' }
  $evidence.codex_hash_before = Get-Sha256Hex $CodexConfig
  if ($evidence.codex_hash_before -ne $ExpectedCodexHash) { throw 'Codex config hash mismatch before apply' }
  [void][System.IO.Directory]::CreateDirectory($RollbackRoot)
  $desktopConfig = Join-Path $DesktopHome 'config.toml'
  if (Save-Previous $desktopConfig (Join-Path $RollbackRoot 'desktop')) { $evidence.backups += @{ target = 'desktop'; path = $desktopConfig } }
  $cliConfig = Join-Path $CliHome 'config.toml'
  if (Save-Previous $cliConfig (Join-Path $RollbackRoot 'cli')) { $evidence.backups += @{ target = 'cli'; path = $cliConfig } }
  $cliStart = Join-Path $CliHome 'Start-OpenInterpreter-CLI.ps1'
  if (Save-Previous $cliStart (Join-Path $RollbackRoot 'cli')) { $evidence.backups += @{ target = 'cli-start'; path = $cliStart } }
  Deploy-File (Join-Path $LauncherRoot 'desktop-config.toml') $desktopConfig
  [void][System.IO.Directory]::CreateDirectory((Join-Path $CliHome 'tmp'))
  Deploy-File (Join-Path $LauncherRoot 'cli-config.toml') $cliConfig
  Deploy-File (Join-Path $LauncherRoot 'Start-OpenInterpreter-CLI.ps1') $cliStart
  $evidence.codex_hash_after = Get-Sha256Hex $CodexConfig
  $evidence.codex_hash_unchanged = ($evidence.codex_hash_after -eq $ExpectedCodexHash)
  if (-not $evidence.codex_hash_unchanged) { throw 'Codex config hash changed during apply' }
  $gatewayOk = $false
  try {
    $resp = Invoke-WebRequest -Uri $GatewayHealthUrl -UseBasicParsing -TimeoutSec 15
    $gatewayOk = ($resp.StatusCode -eq 200)
    $evidence.validations.gateway_health = @{ url = $GatewayHealthUrl; status_code = $resp.StatusCode; ok = $gatewayOk }
  } catch {
    $evidence.validations.gateway_health = @{ url = $GatewayHealthUrl; ok = $false; error = $_.Exception.Message }
  }
  if (-not $gatewayOk) { throw 'Gateway health check failed' }
  $prevCodexHome = $env:CODEX_HOME
  $env:CODEX_HOME = $DesktopHome
  $mcpList = & interpreter mcp list 2>&1 | Out-String
  $env:CODEX_HOME = $prevCodexHome
  $hasGateway = $mcpList -match 'agentcore-gateway'
  $hasMorph = $mcpList -match 'morph-mcp'
  $excerpt = $mcpList.Trim()
  if ($excerpt.Length -gt 500) { $excerpt = $excerpt.Substring(0, 500) }
  $evidence.validations.interpreter_mcp_list = @{ codex_home = $DesktopHome; output_excerpt = $excerpt; agentcore_gateway = $hasGateway; morph_mcp = $hasMorph; ok = ($hasGateway -and $hasMorph) }
  if (-not ($hasGateway -and $hasMorph)) { throw 'interpreter mcp list missing required servers' }
  $startScript = Join-Path $CliHome 'Start-OpenInterpreter-CLI.ps1'
  if (-not (Test-Path -LiteralPath $startScript)) { throw 'Start-OpenInterpreter-CLI.ps1 missing from CLI home' }
  $env:CODEX_HOME = $CliHome
  Push-Location $RepoRoot
  try {
    & interpreter sandbox -P coding -C $RepoRoot -- hostname.exe | Out-Null
    $hostnameExit = $LASTEXITCODE
  } finally {
    Pop-Location
    $env:CODEX_HOME = $prevCodexHome
  }
  $evidence.validations.cli_start_script = @{ path = $startScript; ok = (Test-Path -LiteralPath $startScript) }
  $evidence.validations.cli_sandbox_hostname = @{ codex_home = $CliHome; repo_root = $RepoRoot; profile = 'coding'; exit_code = $hostnameExit; ok = ($hostnameExit -eq 0) }
  if ($hostnameExit -ne 0) { throw "CLI sandbox hostname failed: $hostnameExit" }
  $evidence.success = $true
  $evidence.exit_code = 0
} catch {
  $evidence.success = $false
  $evidence.exit_code = 1
  $evidence.error = $_.Exception.Message
  if (-not $evidence.codex_hash_after) {
    $evidence.codex_hash_after = Get-Sha256Hex $CodexConfig
    $evidence.codex_hash_unchanged = ($evidence.codex_hash_after -eq $ExpectedCodexHash)
  }
} finally {
  $json = $evidence | ConvertTo-Json -Depth 6
  [System.IO.File]::WriteAllText((Join-Path $LauncherRoot 'last-apply-evidence.json'), $json)
}
if ($evidence.success) { Write-Host 'Apply completed successfully.'; exit 0 }
Write-Error $evidence.error
exit $evidence.exit_code