<#
.SYNOPSIS
    Bootstrap AgentCore Python runtime - create/update venv and install dependencies.

.DESCRIPTION
    Creates (or updates) a virtual environment at scripts\.venv\, installs all
    pinned requirements from agentcore_workflow and agentcore_memory, verifies
    Python version, and prints key package versions.

    Authority: BLUEPRINT.md M8 / AGENTS.md

.USAGE
    From repo root:
        powershell -ExecutionPolicy Bypass -File scripts\bootstrap-runtime.ps1

.EXIT CODES
    0  Success
    1  Failure (Python too old, pip failure, etc.)
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot   = Split-Path -Parent $ScriptDir
$VenvDir    = Join-Path $ScriptDir ".venv"
$ReqWorkflow = Join-Path $ScriptDir "agentcore_workflow\requirements.txt"
$ReqMemory   = Join-Path $ScriptDir "agentcore_memory\requirements.txt"
$ContextCatalog = Join-Path $RepoRoot "contracts\context-engine-execution-catalog.json"

# -- Prefer the AgentCore Python installation ---------------------------------
$PythonExe = "C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"  # fall back to PATH
}

function Write-Step { param([string]$Msg) Write-Host "[bootstrap] $Msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Msg) Write-Host "  OK  $Msg" -ForegroundColor Green }
function Write-Fail { param([string]$Msg) Write-Host "  !! $Msg" -ForegroundColor Red }

Write-Step "AgentCore Runtime Bootstrap"
Write-Step "Repo:    $RepoRoot"
Write-Step "Venv:    $VenvDir"
Write-Step "Python:  $PythonExe"
Write-Host ""

# -- 1. Verify Python version >= 3.11 -----------------------------------------
Write-Step "Checking Python version..."
try {
    $VerStr = & $PythonExe --version 2>&1
    Write-Ok "$VerStr"

    # Extract major.minor
    if ($VerStr -match 'Python (\d+)\.(\d+)') {
        $Major = [int]$Matches[1]
        $Minor = [int]$Matches[2]
        if ($Major -lt 3 -or ($Major -eq 3 -and $Minor -lt 11)) {
            Write-Fail "Python >= 3.11 required; found $VerStr"
            exit 1
        }
    } else {
        Write-Fail "Could not parse Python version from: $VerStr"
        exit 1
    }
} catch {
    Write-Fail "Python not found at $PythonExe - $_"
    exit 1
}

# -- 2. Create / update virtual environment ----------------------------------
Write-Step "Creating/updating virtual environment..."
if (-not (Test-Path $VenvDir)) {
    & $PythonExe -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { Write-Fail "venv creation failed"; exit 1 }
    Write-Ok "venv created at $VenvDir"
} else {
    Write-Ok "venv already exists at $VenvDir"
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip    = Join-Path $VenvDir "Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Fail "venv Python not found at $VenvPython"
    exit 1
}

# A partially-created venv can contain python.exe without pip. Repair that
# supported state in place instead of requiring an operator to recreate it.
& $VenvPython -m pip --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Step "Repairing missing pip in the existing virtual environment..."
    & $VenvPython -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) { Write-Fail "pip bootstrap failed"; exit 1 }
    Write-Ok "pip bootstrapped"
}

# -- 3. Upgrade pip -----------------------------------------------------------
Write-Step "Upgrading pip..."
& $VenvPython -m pip install --quiet --upgrade pip
if ($LASTEXITCODE -ne 0) { Write-Fail "pip upgrade failed"; exit 1 }
Write-Ok "pip upgraded"

# -- 4. Install agentcore_workflow requirements ------------------------------
Write-Step "Installing agentcore_workflow requirements..."
if (Test-Path $ReqWorkflow) {
    & $VenvPip install --quiet -r $ReqWorkflow
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to install $ReqWorkflow"
        exit 1
    }
    Write-Ok "agentcore_workflow requirements installed"
} else {
    Write-Fail "Requirements file not found: $ReqWorkflow"
    exit 1
}

# -- 5. Install agentcore_memory requirements (if present) -------------------
Write-Step "Checking agentcore_memory requirements..."
if (Test-Path $ReqMemory) {
    & $VenvPip install --quiet -r $ReqMemory
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to install $ReqMemory"
        exit 1
    }
    Write-Ok "agentcore_memory requirements installed"
} else {
    # agentcore_memory shares psycopg with workflow; no separate requirements is normal
    Write-Ok "No separate requirements.txt for agentcore_memory (shares agentcore_workflow deps)"
}

Write-Step "Installing governed Context Engine runtime..."
if (-not (Test-Path -LiteralPath $ContextCatalog -PathType Leaf)) {
    Write-Fail "Context Engine execution catalog not found: $ContextCatalog"
    exit 1
}
$Catalog = Get-Content -LiteralPath $ContextCatalog -Raw | ConvertFrom-Json
$ContextSource = [string]$Catalog.portable_catalog.source
$ContextVersion = [string]$Catalog.portable_catalog.version
$ReleaseDir = Join-Path $ContextSource ("release\" + $ContextVersion)
$ReleaseManifestPath = Join-Path $ReleaseDir "manifest.json"
if (-not (Test-Path -LiteralPath $ReleaseManifestPath -PathType Leaf)) {
    Write-Fail "Context Engine release manifest not found: $ReleaseManifestPath"
    exit 1
}
$ReleaseManifest = Get-Content -LiteralPath $ReleaseManifestPath -Raw | ConvertFrom-Json
if ([string]$ReleaseManifest.release -ne $ContextVersion) {
    Write-Fail "Context Engine catalog/release version mismatch"
    exit 1
}
$EngineArtifacts = @($ReleaseManifest.artifacts | Where-Object { [string]$_.file -like "agentcore_context_engine-*.whl" })
if ($EngineArtifacts.Count -ne 1) {
    Write-Fail "Expected exactly one Context Engine wheel in the sealed release"
    exit 1
}
$EngineWheel = Join-Path $ReleaseDir ([string]$EngineArtifacts[0].file)
if (-not (Test-Path -LiteralPath $EngineWheel -PathType Leaf)) {
    Write-Fail "Context Engine wheel not found: $EngineWheel"
    exit 1
}
$EngineWheelHash = (Get-FileHash -LiteralPath $EngineWheel -Algorithm SHA256).Hash.ToLowerInvariant()
if ($EngineWheelHash -ne ([string]$EngineArtifacts[0].sha256).ToLowerInvariant()) {
    Write-Fail "Context Engine wheel hash does not match the sealed release manifest"
    exit 1
}
& $VenvPip install --quiet --force-reinstall --no-deps $EngineWheel
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Failed to install the governed Context Engine wheel"
    exit 1
}
Write-Ok "agentcore-context-engine $ContextVersion installed from verified sealed wheel"

# -- 6. Print pinned versions of key packages --------------------------------
Write-Host ""
Write-Step "Installed key package versions:"
$KeyPackages = @("langgraph", "langgraph-checkpoint-postgres", "psycopg", "psycopg-pool", "deepagents", "langchain-openrouter", "agentcore-context-engine", "copier")
foreach ($pkg in $KeyPackages) {
    $ver = & $VenvPip show $pkg 2>$null | Select-String "^Version:" | ForEach-Object { $_.ToString() }
    if ($ver) {
        Write-Host "    $pkg - $($ver.Trim())"
    } else {
        Write-Host "    $pkg - (not installed)"
    }
}

# -- 7. Quick smoke test ------------------------------------------------------
Write-Host ""
Write-Step "Smoke test: import LangGraph, OpenRouter, and Context Engine security..."
$smoke = & $VenvPython -c "import importlib.metadata as metadata; import langgraph; from langchain_openrouter import ChatOpenRouter; from agentcore_context_engine.security import DeviceIdentityManager; print('langgraph', metadata.version('langgraph'), 'langchain-openrouter', metadata.version('langchain-openrouter'), 'agentcore-context-engine', metadata.version('agentcore-context-engine'))" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Ok $smoke
} else {
    Write-Fail "langgraph import failed: $smoke"
    exit 1
}

Write-Host ""
Write-Ok "Bootstrap complete. Activate venv: scripts\.venv\Scripts\Activate.ps1"
Write-Ok "Run tests: scripts\.venv\Scripts\python.exe scripts\agentcore_workflow\tests\m8_acceptance.py"
exit 0
