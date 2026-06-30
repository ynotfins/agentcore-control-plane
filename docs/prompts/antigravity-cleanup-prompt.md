# Antigravity — Self-Cleanup Prompt

> Paste into Antigravity. Edits ONLY Antigravity's own configs. Do not print secrets.

Reconcile to governed renderer `renderers/antigravity.mcp_config.json` in `D:\github\agentcore-control-plane`.

Inspect/align BOTH (they are currently divergent after the incident):
- Primary: `C:\Users\ynotf\.gemini\config\mcp_config.json` (has swarmrecall/swarmvault)
- Secondary: `C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json` (does NOT yet have them)
Back up both first. Make them consistent.

FIX rogue Swarm entries:
- `swarmrecall` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- `swarmvault` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` (replace the broken `.agentcore\mcp-wrappers\swarmvault-mcp.ps1`).

ENSURE governed set: arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, serena, swarmrecall, swarmvault.
REMOVE if present as ACTIVE: context7 (a disabled quarantine block is acceptable but prefer removal), raw mem0, composio, Hostinger, GitKraken/cloudrun/firebase if not approved, hosted Swarm URLs, `:65432`.

ENFORCE the universal rule contract (`docs/prompts/README.md`). Use the top-level `mcpServers` object. Verify discovery; restart; report active servers in BOTH configs + swarmvault launch proof. Concise change summary.
