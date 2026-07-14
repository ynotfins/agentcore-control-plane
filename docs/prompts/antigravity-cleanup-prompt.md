# Antigravity — Self-Cleanup Prompt

**Superseded for normal non-Swarm IDE setup (2026-07-14):** Use install-agentcore-gateway-in-ide.md or the embedded prompt in MASTER_CONFIG_AND_PROMPT.md. This file is retained only as historical/remediation reference for older direct-server or Swarm rollout cleanup. Do not use it to create a normal IDE baseline.

> Paste into Antigravity. Edits ONLY Antigravity's own configs. Do not print secrets.

Reconcile to governed renderer `renderers/antigravity.mcp_config.json` in `D:\github\agentcore-control-plane`.

Inspect/align BOTH (they are currently divergent after the incident):

- Primary: `C:\Users\ynotf\.gemini\config\mcp_config.json` (has swarmrecall/swarmvault)
- Secondary: `C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json` (does NOT yet have them)

Back up both first. Make them consistent.

FIX rogue Swarm entries:

- `swarmrecall` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- `swarmvault` → `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` (replace the broken `.agentcore\mcp-wrappers\swarmvault-mcp.ps1`).

ENSURE governed set: arabold-docs, artiforge, filesystem, obsidian-vault, playwright, sequential-thinking, serena, swarmrecall, swarmvault. Serena must use the installed `serena.exe` launcher with `start-mcp-server --transport stdio --context antigravity --project-from-cwd`; do not use git `uvx` or `--context ide-assistant`. Do not add `global-memory-gateway` unless the current source renderer explicitly contains it.
REMOVE if present as ACTIVE: context7 (a disabled quarantine block is acceptable but prefer removal), raw mem0, composio, Hostinger, GitKraken/cloudrun/firebase if not approved, hosted Swarm URLs, `:65432`.

ENFORCE the universal rule contract (`docs/prompts/README.md`). Use the top-level `mcpServers` object. Verify discovery; restart; report active servers in BOTH configs + swarmvault launch proof. Concise change summary.
