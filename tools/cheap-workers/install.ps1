[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$TargetRoot = (Join-Path $env:USERPROFILE ".codex\mcp\cheap-workers"),
    [string]$BackupRoot = (Join-Path $env:USERPROFILE ".codex\backups\cheap-workers-deploy"),
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"
$sourceRoot = $PSScriptRoot
$managedFiles = @(
    ".gitignore",
    "documentation-policy.mjs",
    "documentation-policy.test.mjs",
    "edit-worker.mjs",
    "edit-worker.test.mjs",
    "install.ps1",
    "package-lock.json",
    "package.json",
    "README.md",
    "secret-safety.mjs",
    "secret-safety.test.mjs",
    "server.mjs",
    "worker-prompts.mjs",
    "worker-prompts.test.mjs"
)

function Invoke-NpmChecked {
    param([string]$WorkingDirectory, [string[]]$Arguments)
    Push-Location $WorkingDirectory
    try {
        & npm.cmd @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "npm $($Arguments -join ' ') failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

foreach ($relativePath in $managedFiles) {
    $sourcePath = Join-Path $sourceRoot $relativePath
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Canonical deployment source is missing: $sourcePath"
    }
}

Invoke-NpmChecked -WorkingDirectory $sourceRoot -Arguments @("ci", "--ignore-scripts")
Invoke-NpmChecked -WorkingDirectory $sourceRoot -Arguments @("test")

if ($ValidateOnly) {
    Write-Output "VALIDATED: canonical cheap-workers source; no deployment performed."
    return
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $BackupRoot $timestamp
$targetExisted = Test-Path -LiteralPath $TargetRoot -PathType Container

if ($PSCmdlet.ShouldProcess($TargetRoot, "deploy canonical cheap-workers MCP package")) {
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null

    foreach ($relativePath in $managedFiles) {
        $targetPath = Join-Path $TargetRoot $relativePath
        if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
            Copy-Item -LiteralPath $targetPath -Destination (Join-Path $backupPath $relativePath)
        }
    }

    try {
        foreach ($relativePath in $managedFiles) {
            Copy-Item -LiteralPath (Join-Path $sourceRoot $relativePath) -Destination (Join-Path $TargetRoot $relativePath)
        }
        Invoke-NpmChecked -WorkingDirectory $TargetRoot -Arguments @("ci", "--ignore-scripts", "--omit=dev")
        Invoke-NpmChecked -WorkingDirectory $TargetRoot -Arguments @("test")
    }
    catch {
        foreach ($relativePath in $managedFiles) {
            $backupFile = Join-Path $backupPath $relativePath
            if (Test-Path -LiteralPath $backupFile -PathType Leaf) {
                Copy-Item -LiteralPath $backupFile -Destination (Join-Path $TargetRoot $relativePath)
            }
        }
        if ($targetExisted -and (Test-Path -LiteralPath (Join-Path $TargetRoot "package-lock.json"))) {
            Invoke-NpmChecked -WorkingDirectory $TargetRoot -Arguments @("ci", "--ignore-scripts", "--omit=dev")
        }
        throw
    }

    Write-Output "DEPLOYED: $TargetRoot"
    Write-Output "ROLLBACK: $backupPath"
    Write-Output "RESTART REQUIRED: open a fresh Codex task so the MCP process loads version 0.4.0."
}
