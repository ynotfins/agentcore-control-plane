# Test-AgentCoreDepwireIntegration.ps1
# Read-only validation for the governed DepWire CLI/MCP integration.
# Never reads or prints the DepWire Pro license value. The Pro license belongs to
# the VS Code/Cursor extension setting `depwire.licenseKey`; depwire-cli MCP does
# not consume a DepWire API/license environment variable.
param(
  [string]$Root = "D:\github\agentcore-control-plane",
  [switch]$IncludeLiveCodex
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$failures = [System.Collections.Generic.List[string]]::new()
$passes = [System.Collections.Generic.List[string]]::new()

function Add-Check {
  param([string]$Name, [bool]$Passed, [string]$Detail)
  if ($Passed) {
    $passes.Add(("{0}: {1}" -f $Name, $Detail)) | Out-Null
  } else {
    $failures.Add(("{0}: {1}" -f $Name, $Detail)) | Out-Null
  }
}

function Read-JsonFile {
  param([string]$RelativePath)
  $path = Join-Path $rootPath $RelativePath
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  return Get-Content -Raw -LiteralPath $path | ConvertFrom-Json
}

$expectedCommand = "C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd"
$expectedVersion = "1.8.2"

$supervisor = Read-JsonFile "supervisor\servers.json"
$supervisorServer = $supervisor.servers.depwire
Add-Check "Supervisor catalog" ($null -ne $supervisorServer) "depwire server is defined"
if ($null -ne $supervisorServer) {
  Add-Check "Supervisor launcher" ($supervisorServer.launch_contract.command -eq $expectedCommand -and (@($supervisorServer.launch_contract.args) -join "|") -eq "mcp") "absolute global launcher + mcp argument"
  Add-Check "Supervisor privacy" ($supervisorServer.env_expectations.DEPWIRE_NO_TELEMETRY -eq "1") "telemetry disabled"
  Add-Check "Supervisor lifecycle" ($supervisorServer.lifecycle -eq "active" -and $supervisorServer.render_by_default -eq $true) "active and rendered by default"
}

$supervisorYamlPath = Join-Path $rootPath "supervisor\servers.yaml"
$supervisorYaml = if (Test-Path -LiteralPath $supervisorYamlPath) { Get-Content -Raw -LiteralPath $supervisorYamlPath } else { "" }
Add-Check "Supervisor YAML" ($supervisorYaml.Contains("  depwire:") -and $supervisorYaml.Contains($expectedCommand.Replace("\", "\\")) -and $supervisorYaml.Contains('DEPWIRE_NO_TELEMETRY: "1"')) "DepWire definition mirrors the JSON supervisor"

$contract = Read-JsonFile "contracts\master-mcp-server-config.json"
$contractServer = $contract.server_catalog.depwire
Add-Check "Master contract catalog" ($null -ne $contractServer) "depwire server is defined"
if ($null -ne $contractServer) {
  Add-Check "Master contract version" ($contractServer.package_version -eq $expectedVersion) "package version pinned to $expectedVersion"
  Add-Check "Master contract credential model" ($contractServer.mcp_requires_api_key -eq $false -and $contractServer.pro_license_scope -eq "vscode_cursor_extension_only") "MCP has no API key; Pro license is extension-only"
}
$profileNames = @("codex", "cursor", "openclaw", "open-interpreter", "minimax-code", "mavis", "antigravity")
$missingProfileBindings = @($profileNames | Where-Object { @($contract.client_profiles.$_.expected_default_servers) -notcontains "depwire" })
Add-Check "Client profile bindings" ($missingProfileBindings.Count -eq 0) ("missing=" + (($missingProfileBindings -join ",") -replace "^$", "none"))

$registry = Read-JsonFile "registry\tool-registry.json"
$registryServer = @($registry.tools | Where-Object { $_.id -eq "depwire" })[0]
Add-Check "Tool registry" ($null -ne $registryServer -and $registryServer.lifecycle -eq "active" -and $registryServer.health -eq "healthy" -and @($registryServer.env_expectations) -contains "DEPWIRE_NO_TELEMETRY") "active, healthy, telemetry-off DepWire record"

$rendererFiles = @(
  "renderers\cursor-global.mcp.json",
  "renderers\open-interpreter.config.fragment.json",
  "renderers\openclaw.openclaw.fragment.json",
  "renderers\minimax.mcp.json",
  "renderers\antigravity.mcp_config.json",
  "renderers\android-studio.mcp.json"
)
foreach ($relativePath in $rendererFiles) {
  $renderer = Read-JsonFile $relativePath
  if ($null -eq $renderer) {
    Add-Check "Renderer $relativePath" $false "missing or invalid JSON"
    continue
  }
  $container = if ($null -ne $renderer.mcpServers) { $renderer.mcpServers } else { $renderer.mcp.servers }
  $server = $container.depwire
  Add-Check "Renderer $relativePath" ($null -ne $server -and $server.command -eq $expectedCommand -and (@($server.args) -join "|") -eq "mcp" -and $server.env.DEPWIRE_NO_TELEMETRY -eq "1") "governed DepWire stdio definition"
}

$generatorPath = Join-Path $rootPath "scripts\mcp_control_plane.py"
$generatorText = if (Test-Path -LiteralPath $generatorPath) { Get-Content -Raw -LiteralPath $generatorPath } else { "" }
Add-Check "Generator source" ($generatorText.Contains("DEPWIRE_SERVER") -and $generatorText.Contains("[mcp_servers.depwire]")) "renderer and Codex generation know DepWire"

$masterPath = Join-Path $rootPath "MASTER_CONFIG_AND_PROMPT.md"
$masterText = if (Test-Path -LiteralPath $masterPath) { Get-Content -Raw -LiteralPath $masterPath } else { "" }
Add-Check "Master documentation" ($masterText.Contains("### DepWire") -and $masterText.Contains("depwire.licenseKey")) "launcher, routing, and Pro license scope documented"

$promptPath = Join-Path $rootPath "docs\prompts\depwire-global-setup-prompt.md"
Add-Check "Universal IDE prompt" (Test-Path -LiteralPath $promptPath) "single cross-client setup prompt exists"

if ($IncludeLiveCodex) {
  Add-Check "Global CLI shim" (Test-Path -LiteralPath $expectedCommand) $expectedCommand

  $versionOutput = ""
  if (Test-Path -LiteralPath $expectedCommand) {
    $versionOutput = (& $expectedCommand --version 2>$null | Select-Object -First 1).Trim()
  }
  Add-Check "Global CLI version" ($versionOutput -match [regex]::Escape($expectedVersion)) "reported version $versionOutput"

  $telemetry = [Environment]::GetEnvironmentVariable("DEPWIRE_NO_TELEMETRY", "User")
  Add-Check "User privacy variable" ($telemetry -eq "1") "DEPWIRE_NO_TELEMETRY=1 at User scope"

  $globalIgnorePath = (& git config --global --get core.excludesfile 2>$null | Select-Object -First 1)
  $globalIgnoreText = if ($globalIgnorePath -and (Test-Path -LiteralPath $globalIgnorePath)) { Get-Content -Raw -LiteralPath $globalIgnorePath } else { "" }
  $globalIgnoreOk = $globalIgnoreText -match '(?m)^\.depwire/\s*$' -and $globalIgnoreText -match '(?m)^depwire-output\.json\s*$'
  Add-Check "Global Git excludes" $globalIgnoreOk ".depwire/ and depwire-output.json are globally ignored"

  $runtimeArtifacts = @(".depwire", "depwire-output.json") | Where-Object { Test-Path -LiteralPath (Join-Path $rootPath $_) }
  Add-Check "Repo runtime cleanup" ($runtimeArtifacts.Count -eq 0) ("present=" + (($runtimeArtifacts -join ",") -replace "^$", "none"))

  $codexConfig = Join-Path $HOME ".codex\config.toml"
  $codexText = if (Test-Path -LiteralPath $codexConfig) { Get-Content -Raw -LiteralPath $codexConfig } else { "" }
  $telemetryConfigured = $codexText.Contains('DEPWIRE_NO_TELEMETRY = "1"') -or $codexText.Contains("DEPWIRE_NO_TELEMETRY = '1'")
  Add-Check "Live Codex MCP config" ($codexText.Contains("[mcp_servers.depwire]") -and $codexText.Contains($expectedCommand.Replace("\", "\\")) -and $telemetryConfigured) "DepWire configured without a credential literal"

  $codexRules = Join-Path $HOME ".codex\AGENTS.md"
  $rulesText = if (Test-Path -LiteralPath $codexRules) { Get-Content -Raw -LiteralPath $codexRules } else { "" }
  Add-Check "Live Codex rules" ($rulesText.Contains("## DepWire") -and $rulesText.Contains("simulate_change") -and $rulesText.Contains("verify_change")) "impact/simulation/verification policy installed"

  $codexRegistered = $false
  try {
    $codexItems = (& codex mcp list --json 2>$null) | ConvertFrom-Json
    $codexDepwire = @($codexItems | Where-Object { $_.name -eq "depwire" -and $_.enabled })[0]
    $codexRegistered = $null -ne $codexDepwire -and $codexDepwire.transport.command -eq $expectedCommand -and (@($codexDepwire.transport.args) -join "|") -eq "mcp"
  } catch {
    $codexRegistered = $false
  }
  Add-Check "Codex registration" $codexRegistered "codex mcp list resolves enabled depwire stdio launcher"

  $probePath = Join-Path $rootPath "probes\probe_stdio.py"
  $handshakeOk = $false
  $toolCount = 0
  $requiredTools = @("connect_repo", "get_architecture_summary", "impact_analysis", "simulate_change", "security_scan", "verify_change")
  $specPath = Join-Path ([System.IO.Path]::GetTempPath()) ("agentcore-depwire-probe-{0}.json" -f [guid]::NewGuid().ToString("N"))
  try {
    $spec = @{ command = $expectedCommand; args = @("mcp"); env = @{ DEPWIRE_NO_TELEMETRY = "1" }; cwd = $env:TEMP } | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($specPath, $spec, [System.Text.UTF8Encoding]::new($false))
    $probe = (& python $probePath ("@" + $specPath) 2>$null) | ConvertFrom-Json
    $toolNames = @($probe.tools.result.tools | ForEach-Object { $_.name })
    $toolCount = $toolNames.Count
    $handshakeOk = $probe.status -eq "healthy" -and $toolCount -eq 23 -and @($requiredTools | Where-Object { $_ -notin $toolNames }).Count -eq 0
  } catch {
    $handshakeOk = $false
  } finally {
    Remove-Item -LiteralPath $specPath -Force -ErrorAction SilentlyContinue
  }
  Add-Check "MCP handshake" $handshakeOk "initialize + tools/list; count=$toolCount; required tools present"

  $postHandshakeArtifacts = @(".depwire", "depwire-output.json") | Where-Object { Test-Path -LiteralPath (Join-Path $rootPath $_) }
  Add-Check "Post-handshake repo cleanup" ($postHandshakeArtifacts.Count -eq 0) ("present=" + (($postHandshakeArtifacts -join ",") -replace "^$", "none"))
}

$passes | ForEach-Object { Write-Output ("PASS: " + $_) }
if ($failures.Count -gt 0) {
  $failures | ForEach-Object { Write-Output ("FAIL: " + $_) }
  exit 1
}

Write-Output ("PASS: DepWire integration validated ({0} checks)." -f $passes.Count)
exit 0
