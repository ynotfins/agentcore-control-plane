# Inspect IDE / agent config layouts

Write-Host "===== Codex ====="
Get-ChildItem 'C:\Users\ynotf\.codex' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'C:\Users\ynotf\.codex\instructions' -Force -ErrorAction SilentlyContinue | Select-Object Name, Length | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== Claude ====="
Get-ChildItem 'C:\Users\ynotf\.claude' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== Cursor ====="
Get-ChildItem 'C:\Users\ynotf\.cursor' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== OpenClaw ====="
Get-ChildItem 'C:\Users\ynotf\.openclaw' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'D:\openclaw' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== OpenInterpreter ====="
Get-ChildItem 'C:\Users\ynotf\.openinterpreter' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== MiniMax (minimax and minimax-agent) ====="
Get-ChildItem 'C:\Users\ynotf\.minimax' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'C:\Users\ynotf\.minimax-agent' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== Mavis ====="
Get-ChildItem 'C:\Users\ynotf\.mavis' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== AppData\\Roaming ====="
Get-ChildItem 'C:\Users\ynotf\AppData\Roaming' -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'Antigravity|Claw|Meili|Swarm|Obsidian|Claude|Cursor' } | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n===== Done ====="