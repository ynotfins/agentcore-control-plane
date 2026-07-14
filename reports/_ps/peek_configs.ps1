# Peek specific config files only
function Peek-File($p, $n = 120) {
    if (-not (Test-Path $p)) { Write-Host "MISSING: $p"; return }
    $item = Get-Item $p
    Write-Host "`n=========== FILE: $p (size=$($item.Length)) ==========="
    $lines = Get-Content $p -TotalCount $n -ErrorAction SilentlyContinue
    foreach ($line in $lines) { Write-Host $line }
}

Peek-File 'C:\Users\ynotf\.openclaw\openclaw.json' 200
Peek-File 'C:\Users\ynotf\.openclaw\gateway.cmd' 80
Peek-File 'C:\Users\ynotf\.openclaw\local.env' 80
Peek-File 'C:\Users\ynotf\.openclaw\gateway-supervisor-restart-handoff.json' 60
Peek-File 'C:\Users\ynotf\.openclaw\openclaw.json.last-good' 80
Peek-File 'C:\Users\ynotf\.codex\config.toml' 200
Peek-File 'C:\Users\ynotf\.claude\settings.json' 200
Peek-File 'C:\Users\ynotf\.cursor\mcp.json' 200
Peek-File 'C:\Users\ynotf\.minimax\config.yaml' 200
Peek-File 'C:\Users\ynotf\.minimax\AGENT.md' 120
Peek-File 'C:\Users\ynotf\.minimax-agent\AGENT.md' 60
Peek-File 'C:\Users\ynotf\.mavis\config.yaml' 200
Peek-File 'C:\Users\ynotf\.mavis\AGENT.md' 120
Peek-File 'C:\Users\ynotf\.openinterpreter\config.toml' 100
Peek-File 'C:\Users\ynotf\.openclaw\OI_MEM0_BRIDGE_CHECKLIST.txt' 80
Peek-File 'C:\Users\ynotf\.codex\hooks.json' 40
Peek-File 'C:\Users\ynotf\.codex\swarmvault.config.json' 40
Peek-File 'C:\Users\ynotf\.codex\swarmvault.schema.md' 80