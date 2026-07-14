# Check all listed repos for git status, latest commit, dirty state, manifests

$repos = @(
    'D:\github\swarm-agent-team',
    'D:\github\agentcore-control-plane',
    'D:\github\vendor\swarm\swarmrelay',
    'D:\github\vendor\swarm\swarmclaw',
    'D:\github\vendor\swarm\swarmvault',
    'D:\github\vendor\swarm\swarmdock',
    'D:\github\vendor\swarm\swarmfeed',
    'D:\github\agent-team',
    'D:\github\autonomous-agent-team'
)

foreach ($r in $repos) {
    Write-Host "`n===== $r ====="
    if (-not (Test-Path $r)) {
        Write-Host "MISSING"
        continue
    }
    Push-Location $r
    try {
        if (Test-Path '.git') {
            Write-Host "GIT: yes"
            $branch = git rev-parse --abbrev-ref HEAD 2>$null
            $commit = git log -1 --pretty=format:"%h %s %ci" 2>$null
            $porcelain = git status --porcelain 2>$null
            $dirtyCount = ($porcelain | Measure-Object -Line).Lines
            $remotes = git remote -v 2>$null
            Write-Host "Branch: $branch"
            Write-Host "Latest: $commit"
            Write-Host "Dirty files: $dirtyCount"
            Write-Host "Remotes:`n$remotes"
        } else {
            Write-Host "GIT: no"
        }
        $items = Get-ChildItem -Force | Select-Object -First 30 Name, Mode, Length | Format-Table -AutoSize | Out-String
        Write-Host "Top-level:`n$items"
        $manifests = @('package.json','pyproject.toml','Cargo.toml','go.mod','requirements.txt','README.md','ARCHITECTURE.md','openclaw.json','gateway.cmd','docker-compose.yml','docker-compose.yaml','compose.yml','compose.yaml')
        foreach ($m in $manifests) {
            $p = Join-Path $r $m
            if (Test-Path $p) {
                $size = (Get-Item $p).Length
                Write-Host ("manifest: {0,-30} size={1}" -f $m, $size)
            }
        }
    } finally {
        Pop-Location
    }
}