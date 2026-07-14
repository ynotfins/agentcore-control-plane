#Requires -Version 5.1
<#
.SYNOPSIS
    Merge the AgentCore native-first Swarm MCP baseline into Claude Code's config.

.DESCRIPTION
    Implements MASTER_CONFIG_AND_PROMPT.md for Claude Code on CHAOSCENTRAL:
      - Discovers which file Claude Code actually reads for user-scope MCP servers
        (per Anthropic docs: ~/.claude.json, top-level "mcpServers" key).
      - Backs up any candidate config files found (.claude.json and .claude\config.json).
      - Merges in required MCP servers WITHOUT clobbering existing working entries
        for servers whose exact launch command was not specified in the source
        authority (serena, sequential-thinking, cursor-agent-mcp, context-fabric,
        mcp-debugger, global-memory-gateway, obsidian-vault) -- these are reported
        as unresolved blockers if missing, never invented.
      - Adds/normalizes swarmrecall, swarmvault, arabold-docs, artiforge with the
        exact commands given in the source authority.
      - Removes active context7 / Hostinger entries unless explicitly flagged
        disabled/quarantined.
      - Deletes the known rogue swarmvault wrapper script if present (after backup).
      - Scans for secret literals, replaces with ${ENV_VAR} references where the
        field supports it, and NEVER prints secret values -- only field paths.
      - Preserves every top-level key outside "mcpServers" untouched (auth/session/
        profile/statsig/etc).
      - Validates JSON syntax after edit.
      - Prints the required final report.

.PARAMETER Apply
    Actually write changes. Without this switch the script runs as a dry run:
    it performs discovery, backup, and prints the diff/report, but does not
    modify the live config. Review the dry run output first.

.PARAMETER ArtiforgePatEnvVar
    Name of the Windows User env var holding the Artiforge PAT.
    Default: ARTIFORGE_PAT. The value itself is never read into a variable
    that gets printed -- only used to build the ${VAR} reference string.

.EXAMPLE
    # Dry run first (recommended)
    pwsh -NoProfile -ExecutionPolicy Bypass -File .\Set-AgentCoreSwarmBaseline.ps1

.EXAMPLE
    # Apply for real
    pwsh -NoProfile -ExecutionPolicy Bypass -File .\Set-AgentCoreSwarmBaseline.ps1 -Apply
#>

[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$ArtiforgePatEnvVar = "ARTIFORGE_PAT"
)

$ErrorActionPreference = "Stop"
$ts = Get-Date -Format "yyyyMMdd-HHmmss"

$report = [ordered]@{
    ActiveConfigPath        = $null
    BackupPaths             = @()
    ServersAdded            = @()
    ServersUpdated          = @()
    ServersRemoved          = @()
    ServersLeftUntouched    = @()
    ServersQuarantinedSkip  = @()
    EnvVarsRequired         = @()
    SecretFieldsRotated     = @()
    SyntaxValidation        = "NOT RUN"
    MCPDiscoveryNote        = ""
    RogueWrapperAction      = "none found"
    RestartRequired         = $true
    UnresolvedBlockers      = @()
    Mode                    = if ($Apply) { "APPLY" } else { "DRY RUN" }
}

function Write-Section($title) {
    Write-Host ""
    Write-Host "=== $title ===" -ForegroundColor Cyan
}

# ---------------------------------------------------------------------------
# 1. DISCOVERY -- which file does Claude Code actually read?
# ---------------------------------------------------------------------------
Write-Section "Discovery"

$home_ = $env:USERPROFILE
$claudeJsonPath   = Join-Path $home_ ".claude.json"
$legacyConfigPath = Join-Path $home_ ".claude\config.json"

$claudeJsonExists   = Test-Path $claudeJsonPath
$legacyConfigExists = Test-Path $legacyConfigPath

Write-Host "Candidate A: $claudeJsonPath   exists=$claudeJsonExists"
Write-Host "Candidate B: $legacyConfigPath exists=$legacyConfigExists"

$activePath = $claudeJsonPath
$report.ActiveConfigPath = $activePath

if ($legacyConfigExists) {
    try {
        $legacyContent = Get-Content -Raw -Path $legacyConfigPath
        $legacyParsed = $legacyContent | ConvertFrom-Json -ErrorAction Stop
        if ($legacyParsed.PSObject.Properties.Name -contains "mcpServers") {
            $report.UnresolvedBlockers += "$legacyConfigPath contains an 'mcpServers' key but this path is NOT read by Claude Code for MCP servers per current docs. It is dead config and a source of confusion. Recommend manual review/deletion after confirming nothing else depends on it."
        } else {
            $report.UnresolvedBlockers += "$legacyConfigPath exists but is not a recognized Claude Code MCP config location. Left untouched aside from backup."
        }
    } catch {
        $report.UnresolvedBlockers += "$legacyConfigPath exists but is not valid JSON. Left untouched aside from backup."
    }
}

if (-not $claudeJsonExists) {
    $report.UnresolvedBlockers += "$claudeJsonPath does not exist. Cannot merge baseline until Claude Code has been run at least once to create it, or the file is created fresh with a minimal {`"mcpServers`":{}} skeleton."
    Write-Host "No active config found. Aborting merge (nothing to safely merge into)." -ForegroundColor Yellow
    $report | Format-List
    return
}

# ---------------------------------------------------------------------------
# 2. BACKUP -- back up both candidates if present, before touching anything
# ---------------------------------------------------------------------------
Write-Section "Backup"

function Backup-File($path) {
    if (Test-Path $path) {
        $backupPath = "$path.bak-$ts"
        Copy-Item -Path $path -Destination $backupPath -Force
        Write-Host "Backed up: $path -> $backupPath"
        return $backupPath
    }
    return $null
}

$backupA = Backup-File $claudeJsonPath
if ($backupA) { $report.BackupPaths += $backupA }

$backupB = Backup-File $legacyConfigPath
if ($backupB) { $report.BackupPaths += $backupB }

# ---------------------------------------------------------------------------
# 3. LOAD -- parse the active config, preserving everything outside mcpServers
# ---------------------------------------------------------------------------
Write-Section "Load & Parse"

$rawText = Get-Content -Raw -Path $claudeJsonPath
try {
    $config = $rawText | ConvertFrom-Json -ErrorAction Stop
} catch {
    $report.SyntaxValidation = "FAILED (pre-edit): active config is not valid JSON. Aborting."
    $report | Format-List
    throw "Active config at $claudeJsonPath is not valid JSON. Fix manually before re-running."
}

if (-not ($config.PSObject.Properties.Name -contains "mcpServers")) {
    $config | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([PSCustomObject]@{})
}

# ---------------------------------------------------------------------------
# 4. SECRET SCAN -- find literal secrets, never print them
# ---------------------------------------------------------------------------
Write-Section "Secret Scan"

$secretFieldPattern = '(?i)(api[_-]?key|token|pat|secret|password|bearer)'
function Test-IsLiteralSecret([string]$val) {
    if ([string]::IsNullOrWhiteSpace($val)) { return $false }
    if ($val -match '^\$\{.+\}$') { return $false }
    if ($val -match '^\$env:') { return $false }
    if ($val.Length -lt 8) { return $false }
    return $true
}

function Scan-And-Redact($node, [string]$pathPrefix) {
    if ($null -eq $node) { return }
    if ($node -is [System.Management.Automation.PSCustomObject]) {
        foreach ($p in @($node.PSObject.Properties)) {
            $fieldPath = "$pathPrefix.$($p.Name)"
            if ($p.Name -match $secretFieldPattern -and $p.Value -is [string] -and (Test-IsLiteralSecret $p.Value)) {
                $envVarName = ($p.Name -replace '[^A-Za-z0-9]', '_').ToUpper()
                $node.$($p.Name) = "`${$envVarName}"
                $report.SecretFieldsRotated += "$fieldPath -> replaced with `${$envVarName}; ROTATE and set Windows User env var $envVarName manually (value not printed here)."
            } elseif ($p.Value -is [string] -and $p.Value -match 'CONTEXT7_API_KEY\s*[:=]\s*\S+') {
                $node.$($p.Name) = ($p.Value -replace 'CONTEXT7_API_KEY\s*[:=]\s*\S+', 'CONTEXT7_API_KEY=${CONTEXT7_API_KEY}')
                $report.SecretFieldsRotated += "$fieldPath -> inline CONTEXT7_API_KEY literal replaced with `${CONTEXT7_API_KEY} reference."
            } else {
                Scan-And-Redact $p.Value $fieldPath
            }
        }
    } elseif ($node -is [System.Array]) {
        for ($i = 0; $i -lt $node.Count; $i++) {
            Scan-And-Redact $node[$i] "$pathPrefix[$i]"
        }
    }
}

Scan-And-Redact $config "config"

# ---------------------------------------------------------------------------
# 5. REMOVE FORBIDDEN ACTIVE ROUTES (context7, Hostinger) unless quarantined
# ---------------------------------------------------------------------------
Write-Section "Forbidden Route Removal"

$forbiddenNamePatterns = @('(?i)context7', '(?i)hostinger')
$mcpServers = $config.mcpServers

foreach ($serverName in @($mcpServers.PSObject.Properties.Name)) {
    $isForbidden = $forbiddenNamePatterns | Where-Object { $serverName -match $_ }
    if ($isForbidden) {
        $entry = $mcpServers.$serverName
        $isQuarantined = $false
        if ($entry.PSObject.Properties.Name -contains "disabled" -and $entry.disabled -eq $true) { $isQuarantined = $true }
        if ($entry.PSObject.Properties.Name -contains "quarantined" -and $entry.quarantined -eq $true) { $isQuarantined = $true }
        if ($serverName -match '(?i)(quarantine|disabled)') { $isQuarantined = $true }

        if ($isQuarantined) {
            $report.ServersQuarantinedSkip += $serverName
            Write-Host "Skipping removal (explicitly quarantined/disabled): $serverName"
        } else {
            $mcpServers.PSObject.Properties.Remove($serverName)
            $report.ServersRemoved += $serverName
            Write-Host "Removed active forbidden route: $serverName" -ForegroundColor Yellow
        }
    }
}

# ---------------------------------------------------------------------------
# 6. MERGE BASELINE
# ---------------------------------------------------------------------------
Write-Section "Baseline Merge"

$exactSpecServers = [ordered]@{
    "swarmrecall" = [ordered]@{
        type    = "stdio"
        command = "pwsh"
        args    = @(
            "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            "D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1",
            "-Mode", "Mcp"
        )
    }
    "swarmvault" = [ordered]@{
        type    = "stdio"
        command = "pwsh"
        args    = @(
            "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            "D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1",
            "-Mode", "Mcp"
        )
    }
    "arabold-docs" = [ordered]@{
        type = "sse"
        url  = "http://localhost:6280/sse"
    }
    "artiforge" = [ordered]@{
        type = "http"
        url  = "https://tools.artiforge.ai/mcp?pat=`${$ArtiforgePatEnvVar}"
    }
}

foreach ($name in $exactSpecServers.Keys) {
    $desired = $exactSpecServers[$name]
    $existed = $mcpServers.PSObject.Properties.Name -contains $name
    if ($existed) {
        $existingJson = ($mcpServers.$name | ConvertTo-Json -Compress -Depth 10)
        $desiredJson  = ($desired | ConvertTo-Json -Compress -Depth 10)
        if ($existingJson -ne $desiredJson) {
            $mcpServers.PSObject.Properties.Remove($name)
            $mcpServers | Add-Member -NotePropertyName $name -NotePropertyValue ([PSCustomObject]$desired)
            $report.ServersUpdated += $name
        } else {
            $report.ServersLeftUntouched += $name
        }
    } else {
        $mcpServers | Add-Member -NotePropertyName $name -NotePropertyValue ([PSCustomObject]$desired)
        $report.ServersAdded += $name
    }
}

$noCommandGivenServers = @(
    "serena", "sequential-thinking", "cursor-agent-mcp", "context-fabric",
    "mcp-debugger", "global-memory-gateway", "obsidian-vault"
)

foreach ($name in $noCommandGivenServers) {
    if ($mcpServers.PSObject.Properties.Name -contains $name) {
        $report.ServersLeftUntouched += $name
    } else {
        $report.UnresolvedBlockers += "'$name' is required by the baseline but has no existing entry and no exact launch command was specified in the source authority or prompt. Not invented. Retrieve the exact command from D:\github\agentcore-control-plane and re-run, or add manually with: claude mcp add $name --scope user ..."
    }
}

if ($ArtiforgePatEnvVar) {
    $report.EnvVarsRequired += $ArtiforgePatEnvVar
}
$report.EnvVarsRequired += "CONTEXT7_API_KEY (only if still referenced anywhere -- rotate/remove per forbidden-route policy)"
$report.EnvVarsRequired = $report.EnvVarsRequired | Select-Object -Unique

# ---------------------------------------------------------------------------
# 7. ROGUE WRAPPER CLEANUP
# ---------------------------------------------------------------------------
Write-Section "Rogue Wrapper Cleanup"

$rogueWrapper = Join-Path $home_ ".agentcore\mcp-wrappers\swarmvault-mcp.ps1"
if (Test-Path $rogueWrapper) {
    $wrapperBackup = "$rogueWrapper.bak-$ts"
    if ($Apply) {
        Copy-Item -Path $rogueWrapper -Destination $wrapperBackup -Force
        Remove-Item -Path $rogueWrapper -Force
        $report.RogueWrapperAction = "removed (backed up to $wrapperBackup)"
    } else {
        $report.RogueWrapperAction = "would remove (dry run) -- backup would go to $wrapperBackup"
    }
    Write-Host "Rogue wrapper: $($report.RogueWrapperAction)"
} else {
    Write-Host "No rogue wrapper found at $rogueWrapper"
}

# ---------------------------------------------------------------------------
# 8. WRITE + VALIDATE
# ---------------------------------------------------------------------------
Write-Section "Write & Validate"

$newJson = $config | ConvertTo-Json -Depth 25

try {
    $null = $newJson | ConvertFrom-Json -ErrorAction Stop
    $report.SyntaxValidation = "PASSED"
} catch {
    $report.SyntaxValidation = "FAILED: $($_.Exception.Message)"
    Write-Host "Syntax validation FAILED. Not writing file." -ForegroundColor Red
    $report | Format-List
    throw
}

if ($Apply) {
    Set-Content -Path $claudeJsonPath -Value $newJson -Encoding UTF8 -NoNewline
    Write-Host "Written: $claudeJsonPath" -ForegroundColor Green
} else {
    Write-Host "DRY RUN -- no changes written. Re-run with -Apply to commit." -ForegroundColor Yellow
    $diffPreviewPath = Join-Path $env:TEMP "claude-json-proposed-$ts.json"
    Set-Content -Path $diffPreviewPath -Value $newJson -Encoding UTF8 -NoNewline
    Write-Host "Proposed content written for review to: $diffPreviewPath"
}

$report.MCPDiscoveryNote = "After restart, run 'claude mcp list' and 'claude mcp get <name>' for each required server to confirm discovery/connection status per server."

# ---------------------------------------------------------------------------
# 9. FINAL REPORT
# ---------------------------------------------------------------------------
Write-Section "FINAL REPORT"
$report | Format-List