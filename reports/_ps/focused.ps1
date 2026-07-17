# Focused peek for specific directories

Write-Host "===== F:\ drive top-level (depth 3) ====="
if (Test-Path 'F:\') {
    Get-ChildItem 'F:\' -Force | Select-Object Name, Mode, @{N='SizeGB';E={[math]::Round($_.Length/1GB,2)}} | Format-Table -AutoSize | Out-String | Write-Host
    Get-ChildItem 'F:\' -Force -Directory | ForEach-Object {
        Write-Host ("-- DIR: {0}" -f $_.FullName)
        Get-ChildItem $_.FullName -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
    }
}

Write-Host "`n===== D:\ openclaw top-level ====="
Get-ChildItem 'D:\openclaw' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'D:\openclaw\bin' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'D:\openclaw\data' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'D:\openclaw\runtime' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== D:\Obsidian top-level ====="
if (Test-Path 'D:\Obsidian') {
    Get-ChildItem 'D:\Obsidian' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
}

Write-Host "`n===== D:\Codex_Managed top-level ====="
Get-ChildItem 'D:\Codex_Managed' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== D:\AgentOps top-level ====="
Get-ChildItem 'D:\AgentOps' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== .openclaw/lossless-claw top-level ====="
if (Test-Path 'C:\Users\ynotf\.openclaw\lossless-claw') {
    Get-ChildItem 'C:\Users\ynotf\.openclaw\lossless-claw' -Force | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host
}
Write-Host "`n===== .openclaw/memory top-level ====="
if (Test-Path 'C:\Users\ynotf\.openclaw\memory') {
    Get-ChildItem 'C:\Users\ynotf\.openclaw\memory' -Force | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host
}

Write-Host "`n===== .openclaw/qmd top-level ====="
if (Test-Path 'C:\Users\ynotf\.openclaw\qmd') {
    Get-ChildItem 'C:\Users\ynotf\.openclaw\qmd' -Force | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host
}

Write-Host "`n===== Codex memories/sqlite ====="
Get-ChildItem 'C:\Users\ynotf\.codex' -Filter '*.sqlite*' -Force | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'C:\Users\ynotf\.codex\memories' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== Codex .sandbox and .tmp ====="
Get-ChildItem 'C:\Users\ynotf\.codex\.sandbox' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'C:\Users\ynotf\.codex\.tmp' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== Cursor plans/rules ====="
Get-ChildItem 'C:\Users\ynotf\.cursor\rules' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'C:\Users\ynotf\.cursor\skills' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== Inventory docs in agentcore-control-plane ====="
$matches = Get-ChildItem 'D:\github\agentcore-control-plane' -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^(hardware|software|specs|PC|system|inventory|CHAOSCENTRAL|master|database-plan|handoff|rollout|memory|swarm|vault|recall|claw)' } |
    Select-Object FullName, Length
$matches | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== agentcore-control-plane ops dir ====="
Get-ChildItem 'D:\github\agentcore-control-plane\ops' -Force | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'D:\github\agentcore-control-plane\registry' -Force | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'D:\github\agentcore-control-plane\supervisor' -Force | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'D:\github\agentcore-control-plane\contracts' -Force | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'D:\github\agentcore-control-plane\schemas' -Force | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== Done ====="