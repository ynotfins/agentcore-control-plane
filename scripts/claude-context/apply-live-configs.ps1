#Requires -Version 5.1
<#
.SYNOPSIS
  Merge claude-context into live IDE MCP configs without writing secrets.
  Targets: Zed, Eigent, Zoo Code (Cursor), Devin, ZCode.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoLaunch = 'D:\github\agentcore-control-plane\scripts\claude-context\claude-context-mcp-launch.cmd'
$liveLaunch = 'C:\Users\ynotf\.agentcore\claude-context-mcp-launch.cmd'
$zedPath = 'C:\Users\ynotf\AppData\Roaming\Zed\settings.json'
$eigentPath = 'C:\Users\ynotf\.eigent\mcp.json'
$zooPath = 'C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json'
$devinPath = 'C:\Users\ynotf\AppData\Roaming\devin\mcp_config.json'
$zcodePath = 'C:\Users\ynotf\.zcode\cli\config.json'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

Copy-Item -LiteralPath $repoLaunch -Destination $liveLaunch -Force

function Backup-File([string]$Path) {
  if (Test-Path -LiteralPath $Path) {
    Copy-Item -LiteralPath $Path -Destination ($Path + '.bak-' + $stamp) -Force
  }
}

function Get-JsonObject([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { throw "Missing config: $Path" }
  Backup-File $Path
  return ((Get-Content -LiteralPath $Path -Raw -Encoding UTF8) | ConvertFrom-Json)
}

function Write-JsonObject([string]$Path, $Obj) {
  $json = $Obj | ConvertTo-Json -Depth 40
  [System.IO.File]::WriteAllText($Path, $json + [Environment]::NewLine)
}

function Ensure-NoteProperty($Obj, [string]$Name) {
  if (-not $Obj.PSObject.Properties.Name.Contains($Name)) {
    $Obj | Add-Member -NotePropertyName $Name -NotePropertyValue ([pscustomobject]@{})
  }
  if ($null -eq $Obj.$Name) { $Obj.$Name = [pscustomobject]@{} }
}

# Zed
$zed = Get-JsonObject $zedPath
Ensure-NoteProperty $zed 'context_servers'
$zed.context_servers | Add-Member -NotePropertyName 'claude-context' -NotePropertyValue ([pscustomobject]@{ command = $liveLaunch; args = @(); env = @{} }) -Force
Write-JsonObject $zedPath $zed

# Eigent
$eigent = Get-JsonObject $eigentPath
Ensure-NoteProperty $eigent 'mcpServers'
$eigent.mcpServers | Add-Member -NotePropertyName 'claude-context' -NotePropertyValue ([pscustomobject]@{ command = $liveLaunch; args = @() }) -Force
Write-JsonObject $eigentPath $eigent

# Zoo Code in Cursor
$zoo = Get-JsonObject $zooPath
Ensure-NoteProperty $zoo 'mcpServers'
$zoo.mcpServers | Add-Member -NotePropertyName 'claude-context' -NotePropertyValue ([pscustomobject]@{ command = $liveLaunch; args = @(); disabled = $false; timeout = 300 }) -Force
Write-JsonObject $zooPath $zoo

# Devin
$devin = Get-JsonObject $devinPath
Ensure-NoteProperty $devin 'mcpServers'
$devin.mcpServers | Add-Member -NotePropertyName 'claude-context' -NotePropertyValue ([pscustomobject]@{ command = $liveLaunch; args = @() }) -Force
Write-JsonObject $devinPath $devin

# ZCode
$zcode = Get-JsonObject $zcodePath
Ensure-NoteProperty $zcode 'mcp'
Ensure-NoteProperty $zcode.mcp 'servers'
$zcode.mcp.servers | Add-Member -NotePropertyName 'claude-context' -NotePropertyValue ([pscustomobject]@{ type = 'stdio'; command = $liveLaunch; args = @(); enabled = $true; timeoutMs = 300000 }) -Force
Write-JsonObject $zcodePath $zcode

Write-Output "Applied claude-context to Zed, Eigent, Zoo Code, Devin, and ZCode. Launcher=$liveLaunch"
Write-Output 'Restart each client to load the MCP server.'
