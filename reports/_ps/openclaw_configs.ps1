# Inspect OpenClaw / ClawX / Codex / Claude / Cursor / MiniMax configs

$dirs = @(
    'C:\Users\ynotf\.openclaw',
    'D:\openclaw',
    'C:\Users\ynotf\.codex',
    'C:\Users\ynotf\.claude',
    'C:\Users\ynotf\.cursor',
    'C:\Users\ynotf\.minimax',
    'C:\Users\ynotf\.minimax-agent',
    'C:\Users\ynotf\.mavis',
    'C:\Users\ynotf\.openinterpreter',
    'C:\Users\ynotf\AppData\Roaming\Meilisearch',
    'C:\Users\ynotf\AppData\Roaming\swarmvault-desktop',
    'C:\Users\ynotf\AppData\Roaming\Antigravity IDE'
)

# Function: peek at file head (read-only)
function Peek-File($p, $n = 80) {
    if (-not (Test-Path $p)) { return }
    $item = Get-Item $p
    Write-Host "`n----- FILE: $p (size=$($item.Length)) -----"
    $lines = Get-Content $p -TotalCount $n -ErrorAction SilentlyContinue
    foreach ($line in $lines) { Write-Host $line }
}

# function: list small JSON/text files
function List-Small($dir, $maxBytes = 64KB) {
    if (-not (Test-Path $dir)) { return }
    Get-ChildItem $dir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -le $maxBytes -and $_.Extension -in '.json','.yaml','.yml','.toml','.cmd','.ps1','.md','.txt','.conf','.ini','.sh' } |
        Select-Object FullName, Length | Format-Table -AutoSize | Out-String | Write-Host
}

foreach ($d in $dirs) {
    Write-Host "`n========== $d =========="
    if (-not (Test-Path $d)) { Write-Host "MISSING"; continue }
    Get-ChildItem $d -Force | Select-Object -First 60 Name, Mode | Format-Table -AutoSize | Out-String | Write-Host
    List-Small $d
}

# Peek at the most important config files
Peek-File 'C:\Users\ynotf\.openclaw\openclaw.json' 200
Peek-File 'C:\Users\ynotf\.openclaw\gateway.cmd' 80
Peek-File 'C:\Users\ynotf\.openclaw\local.env' 80
Peek-File 'C:\Users\ynotf\.codex\config.toml' 200
Peek-File 'C:\Users\ynotf\.claude\settings.json' 200
Peek-File 'C:\Users\ynotf\.cursor\mcp.json' 200
Peek-File 'C:\Users\ynotf\.minimax\config.yaml' 200
Peek-File 'C:\Users\ynotf\.minimax\AGENT.md' 120
Peek-File 'C:\Users\ynotf\.mavis\config.yaml' 200
Peek-File 'C:\Users\ynotf\.mavis\AGENT.md' 120

Write-Host "`n========== End =========="