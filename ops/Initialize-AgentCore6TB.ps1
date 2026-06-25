param(
    [string]$DriveLetter = "E",
    [string]$VolumeLabel = "Agent_Core_6TB",
    [int]$AllocationUnitSize = 65536,
    [int]$PostgresPort = 55432,
    [bool]$SkipFormatWhenAlreadyCorrect = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffK"
    $line = "[$timestamp] $Message"
    Write-Host $line
    if ($script:LogPath) {
        Add-Content -LiteralPath $script:LogPath -Value $line
    }
}

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$FailureMessage
    )
    Write-Log ("RUN: {0} {1}" -f $FilePath, ($Arguments -join " "))
    $output = & $FilePath @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    if ($output) {
        $output | ForEach-Object { Write-Log ("  {0}" -f $_) }
    }
    if ($exitCode -ne 0) {
        throw "$FailureMessage ExitCode=$exitCode"
    }
}

function ConvertTo-ForwardSlashPath {
    param([string]$Path)
    return ($Path -replace "\\", "/")
}

function Find-PostgresBin {
    $candidateBins = [System.Collections.Generic.List[string]]::new()

    foreach ($name in @("initdb.exe", "pg_ctl.exe", "psql.exe", "pg_config.exe")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source) {
            $candidateBins.Add((Split-Path -Parent $cmd.Source))
        }
    }

    foreach ($base in @(
        "$env:ProgramFiles\PostgreSQL",
        "${env:ProgramFiles(x86)}\PostgreSQL",
        "$env:LOCALAPPDATA\Programs\PostgreSQL",
        "C:\PostgreSQL",
        "D:\PostgreSQL"
    )) {
        if ($base -and (Test-Path -LiteralPath $base)) {
            Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue |
                ForEach-Object {
                    $bin = Join-Path $_.FullName "bin"
                    if (Test-Path -LiteralPath $bin) {
                        $candidateBins.Add($bin)
                    }
                }
        }
    }

    $uniqueBins = $candidateBins | Where-Object { $_ } | Sort-Object -Unique
    foreach ($bin in $uniqueBins) {
        $required = @("initdb.exe", "pg_ctl.exe", "psql.exe", "createdb.exe", "pg_config.exe")
        $missing = $required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $bin $_)) }
        if (-not $missing) {
            return $bin
        }
    }

    return $null
}

function Get-NtfsClusterSize {
    param([string]$TargetDriveLetter)

    $ntfsInfo = (& fsutil fsinfo ntfsinfo "$TargetDriveLetter`:" 2>&1) -join "`n"
    $match = [regex]::Match($ntfsInfo, "Bytes Per Cluster\s*:\s*([0-9,]+)")
    if (-not $match.Success) {
        throw "Unable to parse NTFS cluster size for $TargetDriveLetter`:. Output: $ntfsInfo"
    }
    return [int](($match.Groups[1].Value) -replace ",", "")
}

function Get-VectorExtensionStatus {
    param([string]$PostgresBin)

    $pgConfig = Join-Path $PostgresBin "pg_config.exe"
    $sharedir = (& $pgConfig "--sharedir" 2>$null)
    $pkglibdir = (& $pgConfig "--pkglibdir" 2>$null)
    $control = if ($sharedir) { Join-Path $sharedir "extension\vector.control" } else { $null }
    $dll = if ($pkglibdir) { Join-Path $pkglibdir "vector.dll" } else { $null }

    [ordered]@{
        sharedir = $sharedir
        pkglibdir = $pkglibdir
        control_file = $control
        control_file_exists = [bool]($control -and (Test-Path -LiteralPath $control))
        dll_file = $dll
        dll_file_exists = [bool]($dll -and (Test-Path -LiteralPath $dll))
    }
}

function Write-Manifest {
    param(
        [string]$Path,
        [hashtable]$State
    )

    $manifest = [ordered]@{
        generated_at = (Get-Date).ToString("o")
        system_id = "agent_core_6tb"
        drive = [ordered]@{
            letter = "$DriveLetter`:"
            label = $VolumeLabel
            file_system = "NTFS"
            allocation_unit_size_bytes = $AllocationUnitSize
        }
        filesystem = [ordered]@{
            root = "$DriveLetter`:\"
            system_nexus = "$DriveLetter`:\.system_nexus"
            sql_migrations = "$DriveLetter`:\.system_nexus\sql_migrations"
            blackboard = "$DriveLetter`:\.blackboard"
            database_cluster = "$DriveLetter`:\database_cluster"
            agents_workspace = "$DriveLetter`:\agents_workspace"
            mcp_control_plane_workspace = "$DriveLetter`:\agents_workspace\mcp-control-plane"
        }
        network = [ordered]@{
            host = "127.0.0.1"
            postgres_port = $PostgresPort
            external_network_exposure = "disabled"
        }
        credentials = [ordered]@{
            mode = "local_trust_for_loopback_only"
            username_placeholder = "agent_core_admin"
            password_placeholder = "<set-via-secret-manager-if-host-auth-is-enabled>"
            secrets_storage_policy = "do_not_store_secrets_in_manifest"
        }
        database = [ordered]@{
            engine = "postgresql"
            cluster_data_directory = "$DriveLetter`:\database_cluster"
            database_name = "agent_core"
            pgvector_required = $true
            schema_migration = "$DriveLetter`:\.system_nexus\sql_migrations\001_universal_core.sql"
            verification_script = "$DriveLetter`:\.system_nexus\verify_global_handshake.py"
            table_paths = [ordered]@{
                postgres_base_directory = "$DriveLetter`:\database_cluster\base"
                postgres_wal_directory = "$DriveLetter`:\database_cluster\pg_wal"
            }
        }
        status = $State
    }

    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Path -Encoding UTF8
}

if (-not (Test-IsAdministrator)) {
    throw "This script must run in an elevated Administrator PowerShell process. Current token is not elevated."
}

$root = "$DriveLetter`:\"
$systemNexus = Join-Path $root ".system_nexus"
$sqlMigrations = Join-Path $systemNexus "sql_migrations"
$blackboard = Join-Path $root ".blackboard"
$databaseCluster = Join-Path $root "database_cluster"
$agentsWorkspace = Join-Path $root "agents_workspace"
$mcpWorkspace = Join-Path $agentsWorkspace "mcp-control-plane"
$script:LogPath = $null

$logicalDisk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$DriveLetter`:'"
if (-not $logicalDisk) {
    throw "Drive $DriveLetter`: was not found."
}
if ([int]$logicalDisk.DriveType -ne 3) {
    throw "Drive $DriveLetter`: is not a fixed/local disk type. DriveType=$($logicalDisk.DriveType)"
}

$partition = Get-CimAssociatedInstance -InputObject $logicalDisk -Association Win32_LogicalDiskToPartition
$disk = $null
if ($partition) {
    $disk = Get-CimInstance Win32_DiskDrive | Where-Object { $_.Index -eq $partition.DiskIndex } | Select-Object -First 1
}
if ($disk -and ($disk.Model -notmatch "Avolusion")) {
    throw "Drive $DriveLetter`: is not the expected Avolusion target. DiskModel=$($disk.Model)"
}

Write-Host "Confirmed destructive format target: $DriveLetter`: $($logicalDisk.VolumeName) $($logicalDisk.Size) bytes"
if ($disk) {
    Write-Host "Disk identity: Index=$($disk.Index) Model=$($disk.Model) Serial=$($disk.SerialNumber)"
}

$currentClusterSize = $null
if ($logicalDisk.FileSystem -eq "NTFS") {
    $currentClusterSize = Get-NtfsClusterSize -TargetDriveLetter $DriveLetter
}

if (
    $SkipFormatWhenAlreadyCorrect -and
    $logicalDisk.VolumeName -eq $VolumeLabel -and
    $logicalDisk.FileSystem -eq "NTFS" -and
    $currentClusterSize -eq $AllocationUnitSize
) {
    Write-Host "Volume already matches target format. Skipping destructive format and resuming provisioning."
} else {
    $formatExe = Join-Path $env:SystemRoot "System32\format.com"
    $formatArgs = @("$DriveLetter`:", "/FS:NTFS", "/Q", "/A:64K", "/V:$VolumeLabel", "/X", "/Y")
    Invoke-Checked -FilePath $formatExe -Arguments $formatArgs -FailureMessage "Format failed."
}

Start-Sleep -Seconds 3
$postFormatDisk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$DriveLetter`:'"
if (-not $postFormatDisk -or $postFormatDisk.VolumeName -ne $VolumeLabel -or $postFormatDisk.FileSystem -ne "NTFS") {
    throw "Post-format volume verification failed."
}

$verifiedClusterSize = Get-NtfsClusterSize -TargetDriveLetter $DriveLetter
if ($verifiedClusterSize -ne $AllocationUnitSize) {
    throw "Post-format cluster-size verification failed. Expected 65,536 bytes per cluster."
}

New-Item -ItemType Directory -Force -Path $systemNexus, $sqlMigrations, $blackboard, $databaseCluster, $agentsWorkspace, $mcpWorkspace | Out-Null
$script:LogPath = Join-Path $systemNexus ("agent-core-6tb-pipeline-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
Write-Log "Formatted $DriveLetter`: as NTFS label=$VolumeLabel allocation_unit=$AllocationUnitSize."

Write-Log "Applying broad local-agent modify ACLs within $root."
& icacls.exe $root /grant "*S-1-5-11:(OI)(CI)M" /T /C | ForEach-Object { Write-Log ("  {0}" -f $_) }

$migrationPath = Join-Path $sqlMigrations "001_universal_core.sql"
@"
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS global_vector_memory_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_signature TEXT NOT NULL,
    associated_project_path TEXT NOT NULL,
    document_source TEXT NOT NULL,
    content_chunk TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_global_vector_memory_agent_project
    ON global_vector_memory_store (agent_signature, associated_project_path);

CREATE INDEX IF NOT EXISTS idx_global_vector_memory_metadata
    ON global_vector_memory_store USING gin (metadata);

CREATE INDEX IF NOT EXISTS idx_global_vector_memory_embedding_hnsw
    ON global_vector_memory_store USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS agent_cross_project_telemetry (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    active_project_path TEXT NOT NULL,
    execution_status TEXT NOT NULL,
    shared_logs TEXT,
    last_sync_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_cross_project_telemetry_agent_status
    ON agent_cross_project_telemetry (agent_name, execution_status);

CREATE INDEX IF NOT EXISTS idx_agent_cross_project_telemetry_last_sync
    ON agent_cross_project_telemetry (last_sync_timestamp DESC);
"@ | Set-Content -LiteralPath $migrationPath -Encoding UTF8
Write-Log "Wrote SQL migration $migrationPath."

$verifyPath = Join-Path $systemNexus "verify_global_handshake.py"
@'
import json
import os
import sys

try:
    import psycopg
except ImportError:
    psycopg = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None


def connect():
    host = os.environ.get("AGENT_CORE_PGHOST", "127.0.0.1")
    port = int(os.environ.get("AGENT_CORE_PGPORT", "55432"))
    dbname = os.environ.get("AGENT_CORE_PGDATABASE", "agent_core")
    user = os.environ.get("AGENT_CORE_PGUSER", os.environ.get("USERNAME", "postgres"))

    if psycopg is not None:
        return psycopg.connect(host=host, port=port, dbname=dbname, user=user)
    if psycopg2 is not None:
        return psycopg2.connect(host=host, port=port, dbname=dbname, user=user)
    raise RuntimeError("Neither psycopg nor psycopg2 is installed for this Python interpreter.")


def main():
    embedding = "[" + ",".join(["0.001"] * 1536) + "]"
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO global_vector_memory_store (
                    agent_signature,
                    associated_project_path,
                    document_source,
                    content_chunk,
                    embedding,
                    metadata
                )
                VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb)
                RETURNING id
            """, (
                "Codex Verification",
                "E:/agents_workspace/mcp-control-plane",
                "verify_global_handshake.py",
                "deterministic pgvector handshake",
                embedding,
                json.dumps({"verification": True, "dimensions": 1536}),
            ))
            row_id = cur.fetchone()[0]

            cur.execute("""
                SELECT id, 1 - (embedding <=> %s::vector) AS cosine_similarity
                FROM global_vector_memory_store
                WHERE id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT 1
            """, (embedding, row_id, embedding))
            match_id, similarity = cur.fetchone()

            cur.execute("""
                INSERT INTO agent_cross_project_telemetry (
                    agent_name,
                    active_project_path,
                    execution_status,
                    shared_logs
                )
                VALUES (%s, %s, %s, %s)
                RETURNING run_id
            """, (
                "Codex Verification",
                "E:/agents_workspace/mcp-control-plane",
                "verified",
                "pgvector insert and cosine query completed",
            ))
            run_id = cur.fetchone()[0]
        conn.commit()

    print(json.dumps({
        "status": "ok",
        "vector_row_id": str(match_id),
        "telemetry_run_id": str(run_id),
        "cosine_similarity": float(similarity),
    }, indent=2))


if __name__ == "__main__":
    main()
'@ | Set-Content -LiteralPath $verifyPath -Encoding UTF8
Write-Log "Wrote Python verification script $verifyPath."

$state = @{
    format = "completed"
    directory_tree = "completed"
    postgres = "not_started"
    pgvector = "not_checked"
    schema = "not_started"
    python_handshake = "not_started"
}

$manifestPath = Join-Path $systemNexus "infrastructure_manifest.json"
Write-Manifest -Path $manifestPath -State $state

$postgresBin = Find-PostgresBin
if (-not $postgresBin) {
    $state.postgres = "blocked_postgresql_binaries_not_found"
    Write-Manifest -Path $manifestPath -State $state
    Write-Log "PostgreSQL binaries not found. Expected initdb.exe, pg_ctl.exe, psql.exe, createdb.exe, pg_config.exe."
    exit 20
}

Write-Log "PostgreSQL bin path: $postgresBin"
$vectorStatus = Get-VectorExtensionStatus -PostgresBin $postgresBin
$state.pgvector = $vectorStatus
Write-Manifest -Path $manifestPath -State $state
if (-not $vectorStatus.control_file_exists -or -not $vectorStatus.dll_file_exists) {
    $state.postgres = "blocked_pgvector_extension_files_not_found"
    Write-Manifest -Path $manifestPath -State $state
    Write-Log "pgvector extension files are missing. vector.control and vector.dll are required before schema deployment."
    exit 21
}

$initdb = Join-Path $postgresBin "initdb.exe"
$pgCtl = Join-Path $postgresBin "pg_ctl.exe"
$psql = Join-Path $postgresBin "psql.exe"
$createdb = Join-Path $postgresBin "createdb.exe"

if ((Get-ChildItem -LiteralPath $databaseCluster -Force | Measure-Object).Count -gt 0) {
    throw "$databaseCluster must be empty before initdb."
}

Invoke-Checked -FilePath $initdb -Arguments @("-D", $databaseCluster, "-E", "UTF8", "--auth-local=trust", "--auth-host=trust") -FailureMessage "initdb failed."

$pgHbaPath = Join-Path $databaseCluster "pg_hba.conf"
@"
# Agent Core local-only trust access. Do not expose this cluster beyond loopback.
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
"@ | Set-Content -LiteralPath $pgHbaPath -Encoding ASCII

$pgConfPath = Join-Path $databaseCluster "postgresql.conf"
Add-Content -LiteralPath $pgConfPath -Value @"

# Agent Core isolated local engine settings
listen_addresses = '127.0.0.1'
port = $PostgresPort
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
logging_collector = on
"@

$pgLog = Join-Path $systemNexus "postgresql-pgctl.log"
Invoke-Checked -FilePath $pgCtl -Arguments @("-D", $databaseCluster, "-l", $pgLog, "-o", "-p $PostgresPort", "start", "-w") -FailureMessage "pg_ctl start failed."
$state.postgres = "started"
Write-Manifest -Path $manifestPath -State $state

Invoke-Checked -FilePath $createdb -Arguments @("-h", "127.0.0.1", "-p", "$PostgresPort", "agent_core") -FailureMessage "createdb failed."
Invoke-Checked -FilePath $psql -Arguments @("-h", "127.0.0.1", "-p", "$PostgresPort", "-d", "agent_core", "-v", "ON_ERROR_STOP=1", "-f", $migrationPath) -FailureMessage "schema migration failed."
$state.schema = "completed"
Write-Manifest -Path $manifestPath -State $state

$python = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $python) {
    $state.python_handshake = "blocked_python_not_found"
    Write-Manifest -Path $manifestPath -State $state
    Write-Log "python.exe not found; verification script was written but not executed."
    exit 22
}

$env:AGENT_CORE_PGHOST = "127.0.0.1"
$env:AGENT_CORE_PGPORT = "$PostgresPort"
$env:AGENT_CORE_PGDATABASE = "agent_core"
Invoke-Checked -FilePath $python.Source -Arguments @($verifyPath) -FailureMessage "Python verification failed."
$state.python_handshake = "completed"
Write-Manifest -Path $manifestPath -State $state
Write-Log "Agent Core 6TB pipeline completed."
