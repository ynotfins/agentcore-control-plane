# Per-IDE Cleanup Prompts — AgentCore Swarm Rollout

These are **copy-paste prompts** for each managed IDE/agent to clean its **own** live config/rules.
Cursor (the control plane) does NOT edit live IDE configs directly — each app owns its sensitive config.

**Why:** the rogue incident (2026-06-30 00:42–00:45) left live configs unapproved-dirty:
- 7 live configs gained `swarmrecall`/`swarmvault` entries, but the `swarmvault` entry points to a **non-existent** wrapper `C:\Users\ynotf\.agentcore\mcp-wrappers\swarmvault-mcp.ps1` (broken).
- `swarmrecall` used the raw vendored CLI + an un-governed `${env:SWARMRECALL_API_KEY}`.
- Claude Code still carries active `context7` + Hostinger + a live `CONTEXT7_API_KEY`.

Each prompt reconciles the live config to the **governed source renderer** for that client
(`renderers/…`), which now launches SwarmRecall/SwarmVault via the governed wrappers.

## Governed local launch (use these exact entries)

SwarmRecall (stdio):
```
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp
```
SwarmVault (stdio):
```
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp
```
Both enforce local-only operation and read credentials from Windows environment variables. No `${env:}` is needed in the client config; no hosted URLs; no `.env` files.

## Mandatory MCP baseline (every managed IDE)
`arabold-docs, serena, sequential-thinking, cursor-agent-mcp, context-fabric, mcp-debugger, artiforge, global-memory-gateway, obsidian-vault, swarmrecall, swarmvault`
(Note: `cursor-agent-mcp`/`context-fabric`/`mcp-debugger` baseline expansion is staged — current source renderers carry the memory/RAG/context core + swarmrecall + swarmvault; add the remaining three when the source renderers add them.)

## Forbidden active routes (remove from live configs/rules)
`context7`, raw `mem0`/`openmemory` as memory, direct `composio`, `Hostinger`, hosted SwarmRecall/SwarmVault (`*.onrender.com`), direct SQL as normal memory, `:65432` active route, `D:\MCP-Control-Plane` as authority.

## Universal rule contract to enforce (two-tier, per database-plan.md §15)
**Now (existing tools):** use `memory_append`/`memory_search` (global-memory-gateway) for durable memory; `swarmrecall` MCP for native sessions/knowledge/learnings/skills/pools/recall; `swarmvault` MCP for RAG/wiki/graph/context-packs/task-ledger; `obsidian-vault` MCP REST for notes; `arabold-docs` for docs (never context7). Never raw-SQL `agent_core`/`swarmrecall`; never dual-write; never write `F:\AgentCore` by filesystem; never store secrets.
**Later (after migration):** `agentcore_get_startup_context` / `agentcore_retrieve_context` / `agentcore_store_memory` etc. (`agentcore_check_drift` excluded).

## Universal safety clauses (every prompt includes these)
1. Back up the live config before any change.
2. Never print secret values; reference Windows env var names only; no `.env` files.
3. Preserve auth/profile/session state and unrelated top-level config keys.
4. Verify MCP tool discovery after the change; restart the app; report proof.
5. Write a concise summary of changed files. Do not rewrite backups/history/logs.

## Files
- `codex-cleanup-prompt.md`
- `cursor-cleanup-prompt.md`
- `openclaw-cleanup-prompt.md`
- `open-interpreter-cleanup-prompt.md`
- `minimax-cleanup-prompt.md`
- `mavis-cleanup-prompt.md`
- `antigravity-cleanup-prompt.md`
- `claude-code-cleanup-prompt.md`  ← highest priority (active context7 + Hostinger + live key)
- `claude-desktop-obsidian-remediation.md`
