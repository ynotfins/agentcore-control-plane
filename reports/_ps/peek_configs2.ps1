# Inspect additional configs and inventory docs
function Peek-File($p, $n = 200) {
    if (-not (Test-Path $p)) { Write-Host "MISSING: $p"; return }
    $item = Get-Item $p
    Write-Host "`n=========== FILE: $p (size=$($item.Length)) ==========="
    $lines = Get-Content $p -TotalCount $n -ErrorAction SilentlyContinue
    foreach ($line in $lines) { Write-Host $line }
}

# Codex more config + memories
Peek-File 'C:\Users\ynotf\.codex\memories\AGENTS.md' 60
Peek-File 'C:\Users\ynotf\.openclaw\OI_MEM0_BRIDGE_CHECKLIST.txt' 80
Peek-File 'C:\Users\ynotf\.openclaw\openclaw.json' 600

# Try peek openclaw.json.bak variants
foreach ($f in @('openclaw.json.last-good','openclaw.json.pre-update','openclaw.json.bak.4','openclaw.json.pre-lcver-2026-06-20-175000')) {
    Peek-File "C:\Users\ynotf\.openclaw\$f" 200
}

# Check F:\AgentCore layout
Write-Host "`n=========== F:\ drive top-level ==========="
Get-ChildItem 'F:\' -Force | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
if (Test-Path 'F:\AgentCore') {
    Write-Host "`n--- F:\AgentCore ---"
    Get-ChildItem 'F:\AgentCore' -Force -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object FullName, Mode | Out-String | Write-Host
}

# Inventory docs in agentcore-control-plane
Write-Host "`n=========== Search inventory/hardware/specs docs in agentcore-control-plane ==========="
$matches = Get-ChildItem 'D:\github\agentcore-control-plane' -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match 'hardware|software|specs|PC|system|inventory|CHAOSCENTRAL|master|database-plan|handoff|rollout|memory|swarm|vault|recall|claw' } |
    Select-Object FullName, Length | Format-Table -AutoSize | Out-String
Write-Host $matches

# Lossless-claw directory
Write-Host "`n=========== .openclaw/lossless-claw ==========="
Get-ChildItem 'C:\Users\ynotf\.openclaw\lossless-claw' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host
Get-ChildItem 'C:\Users\ynotf\.openclaw\memory' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host

# mcp-oauth, secrets, identity
foreach ($d in @('mcp-oauth','secrets','identity','data','state','qmd')) {
    Write-Host "`n--- .openclaw/$d ---"
    Get-ChildItem "C:\Users\ynotf\.openclaw\$d" -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode, Length | Format-Table -AutoSize | Out-String | Write-Host
}

# Codex memories / databases
Write-Host "`n=========== Codex sqlite databases ==========="
Get-ChildItem 'C:\Users\ynotf\.codex\*.sqlite*' -Force -ErrorAction SilentlyContinue | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize | Out-String | Write-Host

# Codex sessions
Write-Host "`n--- .codex/sessions top ---"
Get-ChildItem 'C:\Users\ynotf\.codex\sessions' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

# Codex memories
Write-Host "`n--- .codex/memories top ---"
Get-ChildItem 'C:\Users\ynotf\.codex\memories' -Force -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "`n=========== Done =========="