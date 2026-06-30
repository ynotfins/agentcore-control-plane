# Mavis (MiniMax classic) — Self-Cleanup Prompt

> Paste into Mavis. Edits ONLY `~/.mavis/mcp/mcp.json` + `~/.mavis/skills/`. Mavis is a SEPARATE managed client from MiniMax-new (own config path, own restart, own adoption proof). Do not print secrets.

Reconcile to the governed MiniMax-family renderer (`renderers/minimax.mcp.json`; a dedicated `renderers/mavis.mcp.json` split is staged). Back up `mcp.json` first.

FIX rogue Swarm entries:
- `swarmrecall` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- `swarmvault` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` (replace the broken wrapper path).

ENSURE governed set: arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, swarmrecall, swarmvault. Add `serena`.
APP-INTERNAL: `matrix`, `cu`, `trash` are Mavis/MiniMax-owned local servers — keep only if confirmed app-owned and local.
SKILLS: delete retired-route skill folders `mcp-context7`, `mcp-mem0`, `mcp-composio`.
REMOVE if present: context7, raw mem0, composio, Hostinger, hosted Swarm URLs, `:65432`.

ENFORCE the universal rule contract (`docs/prompts/README.md`). Verify discovery; restart Mavis; report active servers + swarmvault launch proof separately from MiniMax-new. Concise change summary.
