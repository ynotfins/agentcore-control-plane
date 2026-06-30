# MiniMax (new) — Self-Cleanup Prompt

> Paste into MiniMax Code. Edits ONLY `~/.minimax/mcp/mcp.json` + `~/.minimax/skills/`. Do not print secrets.

Reconcile to governed renderer `renderers/minimax.mcp.json` in `D:\github\agentcore-control-plane`. Back up `mcp.json` first.

FIX rogue Swarm entries:
- `swarmrecall` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- `swarmvault` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` (replace the broken `.agentcore\mcp-wrappers\swarmvault-mcp.ps1`).

ENSURE governed set: arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, swarmrecall, swarmvault. Add `serena` to align with the baseline.
APP-INTERNAL: `matrix`, `cu`, `trash` are MiniMax-owned local servers (matrix-mcp-cli / 127.0.0.1:15321). Keep only if you confirm they are app-owned and local; otherwise remove. They are not part of the AgentCore baseline.
SKILLS: delete retired-route skill folders `mcp-context7`, `mcp-mem0`, `mcp-composio` (they teach forbidden routes).
REMOVE if present in MCP: context7, raw mem0, composio, Hostinger, hosted Swarm URLs, `:65432`.

ENFORCE the universal rule contract (`docs/prompts/README.md`). Verify discovery; restart; report active servers + swarmvault launch proof. Concise change summary. (Mavis is a SEPARATE client — clean it with `mavis-cleanup-prompt.md`.)
