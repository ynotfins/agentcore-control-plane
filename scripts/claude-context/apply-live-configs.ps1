#Requires -Version 5.1
<#
.SYNOPSIS
  Merge claude-context into live Zed + Eigent MCP configs without writing secrets.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoLaunch = 'D:\github\agentcore-control-plane\scripts\claude-context\claude-context-mcp-launch.cmd'
$liveLaunch = 'C:\Users\ynotf\.agentcore\claude-context-mcp-launch.cmd'
$zedPath = 'C:\Users\ynotf\AppData\Roaming\Zed\settings.json'
$eigentPath = 'C:\Users\ynotf\.eigent\mcp.json'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

New-Item -ItemType Directory -Force -Path (Split-Path $liveLaunch) | Out-Null
Copy-Item -LiteralPath $repoLaunch -Destination $liveLaunch -Force

function Backup-File([string]$Path) {
  if (Test-Path -LiteralPath $Path) {
    Copy-Item -LiteralPath $Path -Destination ($Path + '.bak-' + $stamp) -Force
  }
}

function Merge-JsonObject([string]$Path, [string]$RootKey, [hashtable]$Entry) {
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Missing config: $Path"
  }
  Backup-File $Path
  $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  $obj = $raw | ConvertFrom-Json
  if (-not $obj.PSObject.Properties.Name.Contains($RootKey)) {
    $obj | Add-Member -NotePropertyName $RootKey -NotePropertyValue ([pscustomobject]@{})
  }
  $bucket = $obj.$RootKey
  if ($null -eq $bucket) {
    $bucket = [pscustomobject]@{}
    $obj.$RootKey = $bucket
  }
  $bucket | Add-Member -NotePropertyName 'claude-context' -NotePropertyValue ([pscustomobject]$Entry) -Force
  $json = $obj | ConvertTo-Json -Depth 40
  [System.IO.File]::WriteAllText($Path, $json + [Environment]::NewLine)
}

$entry = @{ command = $liveLaunch; args = @(); env = @{} }
Merge-JsonObject -Path $zedPath -RootKey 'context_servers' -Entry $entry
Merge-JsonObject -Path $eigentPath -RootKey 'mcpServers' -Entry @{ command = $liveLaunch; args = @() }
Write-Output "Applied claude-context to Zed and Eigent. Launcher=$liveLaunch"
Write-Output 'Restart Zed and Eigent to load the MCP server.'
