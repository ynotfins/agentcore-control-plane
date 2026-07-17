# Inspect listening TCP ports and active processes

Write-Host "===== Listening TCP Ports ====="
$conns = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue
foreach ($c in $conns) {
    $proc = $null
    try { $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue } catch {}
    $procName = if ($proc) { $proc.ProcessName } else { "(unknown)" }
    $procPath = if ($proc) { $proc.Path } else { "(unknown)" }
    Write-Host ("{0}:{1}  pid={2}  proc={3}  path={4}" -f $c.LocalAddress, $c.LocalPort, $c.OwningProcess, $procName, $procPath)
}

Write-Host "`n===== All running processes (filtered by memory/agent related names) ====="
$patterns = 'claw','swarm','qdrant','meili','postgres','ollama','codex','claude','cursor','antigravity','openinterpreter','minimax','mavis','lancedb','qmd','lossless','recall','vault','relay','dock','feed','node','docker','python','electron','obsidian','winget'
foreach ($p in Get-Process -ErrorAction SilentlyContinue) {
    $name = $p.ProcessName
    if ($patterns | Where-Object { $name -match $_ }) {
        $path = $p.Path
        Write-Host ("pid={0,-6} {1,-30} path={2}" -f $p.Id, $name, $path)
    }
}

Write-Host "`n===== Services ====="
Get-Service | Where-Object { $_.Name -match 'claw|swarm|qdrant|meili|postgres|ollama|docker|obsidian' } | Select-Object Name, Status, StartType | Format-Table -AutoSize

Write-Host "`n===== Done ====="