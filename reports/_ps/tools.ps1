# Tooling audit
$tools = @(
    @{ n = 'node'; cmd = 'node --version' },
    @{ n = 'npm'; cmd = 'npm --version' },
    @{ n = 'pnpm'; cmd = 'pnpm --version' },
    @{ n = 'yarn'; cmd = 'yarn --version' },
    @{ n = 'python'; cmd = 'python --version' },
    @{ n = 'python3'; cmd = 'python3 --version' },
    @{ n = 'pip'; cmd = 'pip --version' },
    @{ n = 'uv'; cmd = 'uv --version' },
    @{ n = 'git'; cmd = 'git --version' },
    @{ n = 'docker'; cmd = 'docker --version' },
    @{ n = 'docker-compose'; cmd = 'docker compose version' },
    @{ n = 'psql'; cmd = 'psql --version' },
    @{ n = 'postgres'; cmd = 'postgres --version' },
    @{ n = 'meilisearch'; cmd = 'meilisearch --version' },
    @{ n = 'qdrant'; cmd = 'qdrant --version' },
    @{ n = 'obsidian'; cmd = 'obsidian --version' },
    @{ n = 'openclaw'; cmd = 'openclaw --version' },
    @{ n = 'clawx'; cmd = 'clawx --version' },
    @{ n = 'codex'; cmd = 'codex --version' },
    @{ n = 'claude'; cmd = 'claude --version' },
    @{ n = 'cursor'; cmd = 'cursor --version' },
    @{ n = 'minimax'; cmd = 'minimax --version' },
    @{ n = 'mavis'; cmd = 'mavis --version' }
)
foreach ($t in $tools) {
    $cmd = $t.cmd
    try {
        $out = & cmd /c $cmd 2>$null
        if ($out) {
            $ver = ($out -split "`n")[0]
            $where = & where.exe $t.n 2>$null | Select-Object -First 1
            Write-Host ("OK     {0,-20}  {1,-40}  loc={2}" -f $t.n, $ver, $where)
        } else {
            Write-Host ("MISS   {0,-20}  (no output)" -f $t.n)
        }
    } catch {
        Write-Host ("MISS   {0,-20}  ({1})" -f $t.n, $_.Exception.Message)
    }
}
Write-Host "`n===== PATH ====="
$env:Path -split ';' | Select-String -Pattern 'Programs|nodejs|postgres|qdrant|meili|openclaw|obsidian|docker|antigravity|cursor|codex' | ForEach-Object { $_.Line }