[CmdletBinding()]
param(
  [string]$Version = "1.19.0",
  [string]$Root = "I:\LocalApps\ZooCode\qdrant",
  [string]$HostAddress = "127.0.0.1",
  [int]$HttpPort = 6333,
  [int]$GrpcPort = 6334,
  [switch]$RegisterScheduledTask,
  [switch]$StartAfterInstall
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function New-DirectoryIfMissing([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
  }
}

function Test-PortFree([int]$Port) {
  $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
  return $listeners.Count -eq 0
}

$releaseTag = if ($Version.StartsWith("v")) { $Version } else { "v$Version" }
$versionBare = $releaseTag.TrimStart("v")
$archiveUrl = "https://github.com/qdrant/qdrant/releases/download/$releaseTag/qdrant-x86_64-pc-windows-msvc.zip"

$releaseRoot = Join-Path $Root "releases\$releaseTag"
$currentRoot = Join-Path $Root "current"
$downloadRoot = Join-Path $Root "downloads"
$configRoot = Join-Path $Root "config"
$storageRoot = Join-Path $Root "storage"
$snapshotsRoot = Join-Path $Root "snapshots"
$logsRoot = Join-Path $Root "logs"
$runtimeRoot = Join-Path $Root "runtime"

foreach ($path in @($releaseRoot, $currentRoot, $downloadRoot, $configRoot, $storageRoot, $snapshotsRoot, $logsRoot, $runtimeRoot)) {
  New-DirectoryIfMissing $path
}

foreach ($port in @($HttpPort, $GrpcPort)) {
  if (-not (Test-PortFree $port)) {
    throw "Port $port is already listening; refusing to install ZooCode Qdrant on an occupied port."
  }
}

$archivePath = Join-Path $downloadRoot "qdrant-$releaseTag-windows-x86_64.zip"
if (-not (Test-Path -LiteralPath $archivePath)) {
  Invoke-WebRequest -Uri $archiveUrl -OutFile $archivePath -UseBasicParsing
}

$archiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash

$extractMarker = Join-Path $releaseRoot ".extracted"
if (-not (Test-Path -LiteralPath $extractMarker)) {
  Expand-Archive -LiteralPath $archivePath -DestinationPath $releaseRoot -Force
  Set-Content -LiteralPath $extractMarker -Value (Get-Date -Format o) -Encoding ascii
}

$releaseExe = Get-ChildItem -LiteralPath $releaseRoot -Recurse -Filter "qdrant.exe" -File | Select-Object -First 1
if (-not $releaseExe) {
  throw "qdrant.exe was not found after extracting $archivePath"
}

Copy-Item -LiteralPath $releaseExe.FullName -Destination (Join-Path $currentRoot "qdrant.exe") -Force
$currentExe = Join-Path $currentRoot "qdrant.exe"
$exeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $currentExe).Hash

$configPath = Join-Path $configRoot "zoo-code-qdrant.yaml"
$config = @"
log_level: INFO

storage:
  storage_path: "$($storageRoot.Replace('\','/'))"
  snapshots_path: "$($snapshotsRoot.Replace('\','/'))"

service:
  host: $HostAddress
  http_port: $HttpPort
  grpc_port: $GrpcPort
  enable_cors: false
  enable_tls: false

cluster:
  enabled: false
"@
Set-Content -LiteralPath $configPath -Value $config -Encoding ascii

$manifest = [ordered]@{
  schema_version = 1
  id = "zoocode-qdrant"
  owner = "AgentCore"
  consumer = "Zoo Code in Cursor"
  classification = "REBUILDABLE_DERIVED_CODE_INDEX"
  version = $versionBare
  release_tag = $releaseTag
  installed_at = (Get-Date).ToString("o")
  source_url = $archiveUrl
  archive_path = $archivePath
  archive_sha256 = $archiveHash
  executable_path = $currentExe
  executable_sha256 = $exeHash
  config_path = $configPath
  storage_path = $storageRoot
  snapshots_path = $snapshotsRoot
  logs_path = $logsRoot
  runtime_path = $runtimeRoot
  http_url = "http://${HostAddress}:$HttpPort"
  grpc = "${HostAddress}:$GrpcPort"
  distributed_port_enabled = $false
  api_key_configured = $false
  api_key_decision = "No API key for local loopback-only development index; Qdrant docs recommend TLS when API keys are enabled, and this deployment is bound to 127.0.0.1 only."
}
$manifestPath = Join-Path $Root "ZOO_CODE_QDRANT_MANIFEST.json"
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding ascii

if ($RegisterScheduledTask) {
  $startScript = Join-Path (Split-Path $PSScriptRoot -Parent) "zoo-code\Start-ZooCodeQdrant.ps1"
  $argument = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$startScript`" -Root `"$Root`""
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argument -WorkingDirectory $Root
  $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
  $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
  $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal
  Register-ScheduledTask -TaskPath "\AgentCore\" -TaskName "ZooCode-Qdrant" -InputObject $task -Force | Out-Null
}

if ($StartAfterInstall) {
  & (Join-Path $PSScriptRoot "Start-ZooCodeQdrant.ps1") -Root $Root
}

[PSCustomObject]@{
  status = "installed"
  version = $versionBare
  manifest = $manifestPath
  executable = $currentExe
  archive_sha256 = $archiveHash
  executable_sha256 = $exeHash
  scheduled_task_registered = [bool]$RegisterScheduledTask
  started = [bool]$StartAfterInstall
}
