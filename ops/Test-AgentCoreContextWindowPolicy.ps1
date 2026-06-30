[CmdletBinding()]
param(
    [string]$Root = "D:\github\agentcore-control-plane",
    [switch]$WriteReport
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Add-Check {
    param(
        [System.Collections.Generic.List[object]]$Checks,
        [string]$Name,
        [bool]$Passed,
        [string]$Severity,
        [string]$Detail
    )

    $Checks.Add([ordered]@{
        name = $Name
        passed = $Passed
        severity = $Severity
        detail = $Detail
    }) | Out-Null
}

function Read-JsonFile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    try {
        Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    } catch {
        $null
    }
}

function Get-JsonServerNames {
    param([object]$Json)

    if (-not $Json) {
        return @()
    }

    $names = New-Object System.Collections.Generic.HashSet[string]
    $candidates = @()
    if ($Json.PSObject.Properties.Name -contains "mcpServers") {
        $candidates += $Json.mcpServers
    }
    if (($Json.PSObject.Properties.Name -contains "mcp") -and $Json.mcp -and ($Json.mcp.PSObject.Properties.Name -contains "servers")) {
        $candidates += $Json.mcp.servers
    }
    if ($Json.PSObject.Properties.Name -contains "servers") {
        $candidates += $Json.servers
    }

    foreach ($candidate in $candidates) {
        if (-not $candidate) { continue }
        foreach ($property in $candidate.PSObject.Properties) {
            [void]$names.Add([string]$property.Name)
        }
    }

    $names | Sort-Object
}

function Get-TomlMcpServerNames {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return @()
    }

    $text = Get-Content -Raw -LiteralPath $Path
    $matches = [regex]::Matches($text, "(?m)^\s*\[mcp_servers\.([A-Za-z0-9_-]+)\]\s*$")
    $names = New-Object System.Collections.Generic.HashSet[string]
    foreach ($match in $matches) {
        [void]$names.Add($match.Groups[1].Value)
    }
    $names | Sort-Object
}

function Get-TomlEnabledPluginNames {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return @()
    }

    $text = Get-Content -Raw -LiteralPath $Path
    $names = New-Object System.Collections.Generic.HashSet[string]
    $matches = [regex]::Matches($text, "(?m)^\s*\[plugins\.""([^""]+)""\]\s*$")
    foreach ($match in $matches) {
        $pluginId = $match.Groups[1].Value
        $name = ($pluginId -split "@")[0]
        if ($name) {
            [void]$names.Add($name)
        }
    }
    $names | Sort-Object
}

function Get-LiveServerNames {
    param(
        [string]$ClientName,
        [object]$Profile,
        [string[]]$ExpectedNames = @()
    )

    $path = [string]$Profile.live_config
    if (-not $path -or -not (Test-Path -LiteralPath $path)) {
        return [ordered]@{
            exists = $false
            path = $path
            names = @()
            source = "missing"
        }
    }

    if ($path.EndsWith(".toml", [System.StringComparison]::OrdinalIgnoreCase)) {
        $mcpNames = @(Get-TomlMcpServerNames -Path $path)
        $pluginNames = @(Get-TomlEnabledPluginNames -Path $path | Where-Object { $ExpectedNames -contains $_ })
        return [ordered]@{
            exists = $true
            path = $path
            names = @($mcpNames + $pluginNames | Sort-Object -Unique)
            source = "toml"
        }
    }

    $json = Read-JsonFile -Path $path
    return [ordered]@{
        exists = $true
        path = $path
        names = @(Get-JsonServerNames -Json $json)
        source = if ($json) { "json" } else { "unparsed-json" }
    }
}

function Get-LiveCodexServerCatalog {
    try {
        $raw = & codex mcp list --json 2>$null
        if (-not $raw) {
            return @{
                ok = $false
                error = "codex mcp list returned no output"
                servers = @()
            }
        }

        $parsed = $raw | ConvertFrom-Json
        $enabled = @($parsed | Where-Object { $_.enabled })
        return @{
            ok = $true
            error = $null
            servers = $enabled
        }
    } catch {
        return @{
            ok = $false
            error = $_.Exception.Message
            servers = @()
        }
    }
}

function Test-ExactStringArray {
    param(
        [object[]]$Actual,
        [object[]]$Expected
    )

    $actualStrings = @($Actual | ForEach-Object { [string]$_ })
    $expectedStrings = @($Expected | ForEach-Object { [string]$_ })
    $diff = @(Compare-Object -ReferenceObject $expectedStrings -DifferenceObject $actualStrings -SyncWindow 0)
    return ($diff.Count -eq 0)
}

$checks = New-Object System.Collections.Generic.List[object]
$contractPath = Join-Path $Root "contracts\master-mcp-server-config.json"
$contract = Read-JsonFile -Path $contractPath

Add-Check $checks "contract:master-mcp-exists" (Test-Path -LiteralPath $contractPath) "error" $contractPath
Add-Check $checks "contract:master-mcp-parses" ($null -ne $contract) "error" $contractPath

$clientResults = @()
$liveCodexCatalog = $null

if ($contract) {
    $forbidden = @($contract.default_exclusions.must_not_emit | ForEach-Object { [string]$_ })

    Add-Check $checks "policy:normal-memory-gateway" ([string]$contract.normal_memory_rule.normal_write_path -eq "global-memory-gateway") "error" "Normal write path must remain global-memory-gateway."
    Add-Check $checks "policy:swarmrecall-not-default" (-not [bool]$contract.normal_memory_rule.swarmrecall_direct_mcp_default) "error" "Direct SwarmRecall MCP rollout must remain opt-in."
    Add-Check $checks "policy:default-exclusions-present" ($forbidden.Count -gt 0) "error" "Forbidden retired routes must be declared."

    foreach ($clientProperty in $contract.client_profiles.PSObject.Properties) {
        $clientName = $clientProperty.Name
        $profile = $clientProperty.Value
        $expected = @($profile.expected_default_servers | ForEach-Object { [string]$_ })
        $budget = $null
        if (($profile.PSObject.Properties.Name -contains "server_budget") -and $profile.server_budget -and ($profile.server_budget.PSObject.Properties.Name -contains "default_limit")) {
            $budget = [int]$profile.server_budget.default_limit
        }

        Add-Check $checks "client:${clientName}:has-gateway" ($expected -contains "global-memory-gateway") "error" "Expected default server list must include global-memory-gateway."

        $forbiddenInExpected = @($expected | Where-Object { $forbidden -contains $_ })
        Add-Check $checks "client:${clientName}:no-forbidden-expected" ($forbiddenInExpected.Count -eq 0) "error" ("Forbidden expected servers: " + ($forbiddenInExpected -join ", "))

        if ($budget) {
            Add-Check $checks "client:${clientName}:budget" ($expected.Count -le $budget) "error" "Expected $($expected.Count), budget $budget."
        }

        $live = Get-LiveServerNames -ClientName $clientName -Profile $profile -ExpectedNames $expected
        $liveNames = @($live.names)
        $missingExpected = @($expected | Where-Object { $liveNames -notcontains $_ })
        $extraLive = @($liveNames | Where-Object { $expected -notcontains $_ })
        $extraLiveForbidden = @($liveNames | Where-Object { $forbidden -contains $_ })

        Add-Check $checks "client:${clientName}:live-config-exists" ([bool]$live.exists) "warning" ([string]$live.path)
        if ($live.exists -and $live.source -eq "unparsed-json") {
            Add-Check $checks "client:${clientName}:live-config-parses" $false "warning" ([string]$live.path)
        }
        if ($live.exists -and $liveNames.Count -gt 0) {
            Add-Check $checks "client:${clientName}:no-forbidden-live" ($extraLiveForbidden.Count -eq 0) "error" ("Forbidden live servers: " + ($extraLiveForbidden -join ", "))
            Add-Check $checks "client:${clientName}:expected-present-live" ($missingExpected.Count -eq 0) "warning" ("Missing from parseable live config: " + ($missingExpected -join ", "))
            Add-Check $checks "client:${clientName}:no-extra-live" ($extraLive.Count -eq 0) "error" ("Extra in parseable live config: " + ($extraLive -join ", "))
            if ($budget) {
                Add-Check $checks "client:${clientName}:live-budget" ($liveNames.Count -le $budget) "error" "Live $($liveNames.Count), budget $budget."
            }
        }

        if ($clientName -eq "codex") {
            if ($null -eq $liveCodexCatalog) {
                $liveCodexCatalog = Get-LiveCodexServerCatalog
            }

            Add-Check $checks "client:codex:transport-catalog" ([bool]$liveCodexCatalog.ok) "error" (($liveCodexCatalog.error | Out-String).Trim())

            if ($liveCodexCatalog.ok) {
                $filesystemServer = @($liveCodexCatalog.servers | Where-Object { $_.name -eq "filesystem" })[0]
                $filesystemExpectedArgs = @($contract.server_catalog.filesystem.args | ForEach-Object { [string]$_ })
                $filesystemActualArgs = @()
                if ($filesystemServer -and $filesystemServer.transport) {
                    $filesystemActualArgs = @($filesystemServer.transport.args | ForEach-Object { [string]$_ })
                }
                $filesystemShapeOk = ($null -ne $filesystemServer) -and (Test-ExactStringArray -Actual $filesystemActualArgs -Expected $filesystemExpectedArgs)
                Add-Check $checks "client:codex:filesystem-shape" $filesystemShapeOk "error" ("actual=" + ($filesystemActualArgs -join " | ") + "; expected=" + ($filesystemExpectedArgs -join " | "))

                $serenaServer = @($liveCodexCatalog.servers | Where-Object { $_.name -eq "serena" })[0]
                $serenaExpectedArgs = @($contract.server_catalog.serena.args | ForEach-Object { [string]$_ })
                $serenaActualArgs = @()
                if ($serenaServer -and $serenaServer.transport) {
                    $serenaActualArgs = @($serenaServer.transport.args | ForEach-Object { [string]$_ })
                }
                $serenaShapeOk = ($null -ne $serenaServer) -and (Test-ExactStringArray -Actual $serenaActualArgs -Expected $serenaExpectedArgs)
                Add-Check $checks "client:codex:serena-shape" $serenaShapeOk "error" ("actual=" + ($serenaActualArgs -join " | ") + "; expected=" + ($serenaExpectedArgs -join " | "))

                $githubServer = @($liveCodexCatalog.servers | Where-Object { $_.name -eq "github" })[0]
                $githubExpectedUrl = [string]$contract.server_catalog."github-mcp".codex_shape.url
                $githubExpectedBearer = [string]$contract.server_catalog."github-mcp".codex_shape.bearer_token_env_var
                $githubActualUrl = ""
                $githubActualBearer = ""
                if ($githubServer -and $githubServer.transport) {
                    $githubActualUrl = [string]$githubServer.transport.url
                    $githubActualBearer = [string]$githubServer.transport.bearer_token_env_var
                }
                $githubShapeOk = ($null -ne $githubServer) -and ($githubActualUrl -eq $githubExpectedUrl) -and ($githubActualBearer -eq $githubExpectedBearer)
                Add-Check $checks "client:codex:github-shape" $githubShapeOk "error" ("actual_url=" + $githubActualUrl + "; actual_bearer=" + $githubActualBearer + "; expected_url=" + $githubExpectedUrl + "; expected_bearer=" + $githubExpectedBearer)
            }
        }

        $clientResults += [ordered]@{
            client = $clientName
            expected_count = $expected.Count
            budget = $budget
            live_config = $live.path
            live_config_exists = [bool]$live.exists
            live_source = $live.source
            live_server_count = $liveNames.Count
            missing_expected_live = @($missingExpected)
            forbidden_live = @($extraLiveForbidden)
        }
    }
}

$antigravitySecondary = "C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json"
if (Test-Path -LiteralPath $antigravitySecondary) {
    $antigravityExpected = @("arabold-docs", "artiforge", "filesystem", "global-memory-gateway", "obsidian-vault", "playwright", "sequential-thinking", "serena")
    $secondaryJson = Read-JsonFile -Path $antigravitySecondary
    $secondaryNames = @(Get-JsonServerNames -Json $secondaryJson)
    $secondaryMissing = @($antigravityExpected | Where-Object { $secondaryNames -notcontains $_ })
    $secondaryExtra = @($secondaryNames | Where-Object { $antigravityExpected -notcontains $_ })
    Add-Check $checks "client:antigravity-roaming:expected-present-live" ($secondaryMissing.Count -eq 0) "warning" ("Missing from parseable live config: " + ($secondaryMissing -join ", "))
    Add-Check $checks "client:antigravity-roaming:no-extra-live" ($secondaryExtra.Count -eq 0) "error" ("Extra in parseable live config: " + ($secondaryExtra -join ", "))
    Add-Check $checks "client:antigravity-roaming:live-budget" ($secondaryNames.Count -le 8) "error" "Live $($secondaryNames.Count), budget 8."
}

$failed = @($checks | Where-Object { -not $_.passed -and $_.severity -eq "error" })
$warnings = @($checks | Where-Object { -not $_.passed -and $_.severity -eq "warning" })
$status = if ($failed.Count -gt 0) { "fail" } elseif ($warnings.Count -gt 0) { "warn" } else { "pass" }

$result = [ordered]@{
    status = $status
    generated_at = (Get-Date).ToString("o")
    contract_path = $contractPath
    failed = $failed.Count
    warnings = $warnings.Count
    clients = @($clientResults)
    checks = @($checks.ToArray())
}

if ($WriteReport) {
    $reportRoot = Join-Path $Root "artifacts\context-window-policy"
    New-Item -ItemType Directory -Force -Path $reportRoot | Out-Null
    $reportPath = Join-Path $reportRoot ("context-window-policy-" + (Get-Date).ToString("yyyyMMdd-HHmmss") + ".json")
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    $result["report_path"] = $reportPath
}

$result | ConvertTo-Json -Depth 12

if ($failed.Count -gt 0) {
    exit 1
}
