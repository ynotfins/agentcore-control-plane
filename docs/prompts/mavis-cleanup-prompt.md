# Mavis (MiniMax classic) — Self-Cleanup Prompt

**Superseded for normal non-Swarm IDE setup (2026-07-14):** Use install-agentcore-gateway-in-ide.md or the embedded prompt in MASTER_CONFIG_AND_PROMPT.md. This file is retained only as historical/remediation reference for older direct-server or Swarm rollout cleanup. Do not use it to create a normal IDE baseline.

> Paste into Mavis. Edits ONLY `~/.mavis/mcp/mcp.json` + `~/.mavis/skills/`. Mavis is a SEPARATE managed client from MiniMax-new (own config path, own restart, own adoption proof). Do not print secrets.

Reconcile to the governed MiniMax-family renderer (`renderers/minimax.mcp.json`; a dedicated `renderers/mavis.mcp.json` split is staged). Back up `mcp.json` first.

FIX rogue Swarm entries:

- `swarmrecall` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- `swarmvault` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` (replace the broken wrapper path).

ENSURE governed set: arabold-docs, artiforge, filesystem, obsidian-vault, playwright, sequential-thinking, serena, swarmrecall, swarmvault. Serena must use the installed `serena.exe` launcher with `start-mcp-server --transport stdio --context ide`; do not use git `uvx` or `--context ide-assistant`. Do not add `global-memory-gateway` unless the current source renderer explicitly contains it.
APP-INTERNAL: `matrix`, `cu`, `trash` are Mavis/MiniMax-owned local servers — keep only if confirmed app-owned and local.
SKILLS: delete retired-route skill folders `mcp-context7`, `mcp-mem0`, `mcp-composio`.
REMOVE if present: context7, raw mem0, composio, Hostinger, hosted Swarm URLs, `:65432`.

ENFORCE the universal rule contract (`docs/prompts/README.md`). Verify discovery; restart Mavis; report active servers + swarmvault launch proof separately from MiniMax-new. Concise change summary.
