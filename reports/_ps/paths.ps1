# Check existence of all listed paths
$paths = @(
    "D:\github\swarm-agent-team",
    "D:\github\agentcore-control-plane",
    "D:\github\vendor\swarm\swarmrelay",
    "D:\github\vendor\swarm\swarmclaw",
    "D:\github\vendor\swarm\swarmvault",
    "D:\github\vendor\swarm\swarmdock",
    "D:\github\vendor\swarm\swarmfeed",
    "C:\Users\ynotf\.codex",
    "C:\Users\ynotf\.claude",
    "C:\Users\ynotf\.cursor",
    "C:\Users\ynotf\.openclaw",
    "C:\Users\ynotf\.openinterpreter",
    "C:\Users\ynotf\.minimax",
    "C:\Users\ynotf\.minimax-agent",
    "C:\Users\ynotf\.mavis",
    "C:\Users\ynotf\AppData\Roaming\Antigravity IDE",
    "C:\Users\ynotf\AppData\Roaming\Meilisearch",
    "C:\Users\ynotf\AppData\Roaming\swarmvault-desktop",
    "C:\Program Files\ClawX",
    "C:\Program Files\nodejs",
    "D:\openclaw",
    "D:\Obsidian\Dungeon Vault",
    "D:\Obsidian\Obsidian Vault",
    "D:\Codex_Managed",
    "D:\AgentOps",
    "D:\github\agent-team",
    "D:\github\autonomous-agent-team"
)
foreach ($p in $paths) {
    if (Test-Path $p) {
        $item = Get-Item $p -Force
        Write-Host ("EXISTS  [{0}]  {1}" -f $item.GetType().Name, $p)
    } else {
        Write-Host ("MISSING                {0}" -f $p)
    }
}