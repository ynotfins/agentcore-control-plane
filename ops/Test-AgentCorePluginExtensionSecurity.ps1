[CmdletBinding()]
param(
    [string]$Root = "D:\github\agentcore-control-plane",
    [string]$ReportRoot = "D:\github\agentcore-control-plane\artifacts\plugin-extension-security",
    [int]$MaxFilesPerRoot = 500,
    [int]$MaxFileBytes = 524288,
    [switch]$NoReport,
    [switch]$DetailedOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Add-Finding {
    param(
        [System.Collections.Generic.List[object]]$Findings,
        [string]$Severity,
        [string]$Category,
        [string]$Path,
        [string]$Detail
    )

    $Findings.Add([ordered]@{
        severity = $Severity
        category = $Category
        path = $Path
        detail = $Detail
    }) | Out-Null
}

function Get-ExistingScanRoots {
    $roots = @(
        "$env:USERPROFILE\.codex\plugins\cache",
        "$env:USERPROFILE\.codex\skills",
        "$env:USERPROFILE\.codex\mcp-wrappers",
        "$env:USERPROFILE\.agents\skills",
        "$env:USERPROFILE\.cursor\extensions",
        "$env:USERPROFILE\.cursor\vendor",
        "$env:USERPROFILE\.vscode\extensions",
        "$env:USERPROFILE\.openclaw",
        "$env:USERPROFILE\.minimax",
        "$env:USERPROFILE\.mavis"
    )

    $roots |
        Where-Object { Test-Path -LiteralPath $_ } |
        Sort-Object -Unique
}

function Get-InspectableFiles {
    param([string]$Path, [int]$Limit)

    $extensions = @(".ps1", ".psm1", ".bat", ".cmd", ".js", ".mjs", ".cjs", ".ts", ".py", ".json", ".toml", ".yaml", ".yml")
    Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object {
            $extensions -contains $_.Extension.ToLowerInvariant() -and
            $_.Length -le $script:MaxFileBytes -and
            $_.FullName -notmatch "\\node_modules\\\.cache\\" -and
            $_.FullName -notmatch "\\\.git\\"
        } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First $Limit
}

function Test-FilePatterns {
    param(
        [System.IO.FileInfo]$File,
        [System.Collections.Generic.List[object]]$Findings
    )

    $patterns = @(
        @{ severity = "high"; category = "encoded-command"; regex = "(?i)\b(encodedcommand|frombase64string)\b"; detail = "Encoded command or base64 execution pattern." },
        @{ severity = "critical"; category = "security-tool-disable"; regex = "(?i)\b(Set-MpPreference|Add-MpPreference)\b.*\b(Disable|Exclusion)\b"; detail = "Security-tool disable or exclusion pattern." },
        @{ severity = "high"; category = "download-execute"; regex = "(?i)\b(iwr|irm|Invoke-WebRequest|Invoke-RestMethod|curl)\b.{0,120}\|\s*(iex|Invoke-Expression|powershell|pwsh|cmd)"; detail = "Downloaded content appears to be piped into an executor." },
        @{ severity = "high"; category = "startup-persistence"; regex = "(?i)\b(New-ScheduledTask|Register-ScheduledTask)\b|\\RunOnce\b|CurrentVersion\\Run\b"; detail = "Startup or scheduled-task persistence pattern." },
        @{ severity = "warning"; category = "destructive-recursive-delete"; regex = "(?i)\bRemove-Item\b.{0,160}\b-Recurse\b.{0,160}\b-Force\b"; detail = "Recursive force delete pattern." },
        @{ severity = "warning"; category = "force-process-stop"; regex = "(?i)\b(taskkill\s+/F|Stop-Process\b.{0,80}\b-Force\b)"; detail = "Force process termination pattern." },
        @{ severity = "warning"; category = "credential-file-reference"; regex = "(?i)\b(auth\.json|installation_id|credentials|refresh_token|private_key|api[_-]?key|bearer)\b"; detail = "Credential-like file or token reference. Do not print values." },
        @{ severity = "warning"; category = "dynamic-eval"; regex = "(?i)\b(Invoke-Expression|eval\(|new Function\()\b"; detail = "Dynamic code evaluation pattern." }
    )

    try {
        $text = Get-Content -Raw -LiteralPath $File.FullName -ErrorAction Stop
    } catch {
        return
    }

    foreach ($pattern in $patterns) {
        if ($text -match $pattern.regex) {
            Add-Finding $Findings $pattern.severity $pattern.category $File.FullName $pattern.detail
        }
    }
}

$findings = New-Object System.Collections.Generic.List[object]
$scanRoots = @(Get-ExistingScanRoots)
$rootSummaries = @()
$recentThreshold = (Get-Date).AddDays(-2)

foreach ($scanRoot in $scanRoots) {
    $files = @(Get-InspectableFiles -Path $scanRoot -Limit $MaxFilesPerRoot)
    $recentFiles = @($files | Where-Object { $_.LastWriteTime -gt $recentThreshold })

    foreach ($file in $files) {
        Test-FilePatterns -File $file -Findings $findings
    }

    foreach ($file in $recentFiles | Select-Object -First 50) {
        Add-Finding $findings "info" "recent-change" $file.FullName ("Modified " + $file.LastWriteTime.ToString("o"))
    }

    $rootSummaries += [ordered]@{
        root = $scanRoot
        inspected_files = $files.Count
        recent_files = $recentFiles.Count
        newest_write_time = if ($files.Count -gt 0) { ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime.ToString("o") } else { $null }
    }
}

$baselinePath = Join-Path $ReportRoot "baseline.json"
$baselineExists = Test-Path -LiteralPath $baselinePath
if (-not $baselineExists) {
    Add-Finding $findings "warning" "baseline-missing" $baselinePath "No approved plugin/extension baseline exists yet."
}

$findingRows = @($findings.ToArray())
$critical = @($findingRows | Where-Object { $_.severity -eq "critical" })
$high = @($findingRows | Where-Object { $_.severity -eq "high" })
$warnings = @($findingRows | Where-Object { $_.severity -eq "warning" })
$status = if ($critical.Count -gt 0) { "fail" } elseif ($high.Count -gt 0 -or $warnings.Count -gt 0) { "warn" } else { "pass" }

$result = [ordered]@{
    status = $status
    generated_at = (Get-Date).ToString("o")
    report_only = $true
    roots_scanned = $scanRoots.Count
    critical = $critical.Count
    high = $high.Count
    warnings = $warnings.Count
    scan_roots = @($rootSummaries)
    findings = @($findingRows)
    policy = [ordered]@{
        destructive_actions_taken = $false
        secret_values_recorded = $false
    }
}

if (-not $NoReport) {
    New-Item -ItemType Directory -Force -Path $ReportRoot | Out-Null
    $reportPath = Join-Path $ReportRoot ("plugin-extension-security-" + (Get-Date).ToString("yyyyMMdd-HHmmss") + ".json")
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    $result["report_path"] = $reportPath
}

$output = if ($DetailedOutput) {
    $result
} else {
    [ordered]@{
        status = $result.status
        generated_at = $result.generated_at
        report_only = $result.report_only
        roots_scanned = $result.roots_scanned
        critical = $result.critical
        high = $result.high
        warnings = $result.warnings
        report_path = if ($result.Contains("report_path")) { $result.report_path } else { $null }
        high_or_critical_findings = @($findingRows | Where-Object { $_.severity -in @("critical", "high") } | Select-Object -First 20)
        policy = $result.policy
    }
}

$output | ConvertTo-Json -Depth 8

if ($critical.Count -gt 0) {
    exit 1
}
