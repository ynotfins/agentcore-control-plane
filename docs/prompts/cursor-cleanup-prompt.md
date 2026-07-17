# Cursor — Self-Cleanup Prompt

**Superseded for normal non-Swarm IDE setup (2026-07-14):** Use install-agentcore-gateway-in-ide.md or the embedded prompt in MASTER_CONFIG_AND_PROMPT.md. This file is retained only as historical/remediation reference for older direct-server or Swarm rollout cleanup. Do not use it to create a normal IDE baseline.

> Paste into Cursor. Edits ONLY Cursor's own config/rules. Do not print secrets.

Reconcile Cursor's live MCP config to the governed source renderer `renderers/cursor-global.mcp.json` in `D:\github\agentcore-control-plane`. Source authority is that repo; `D:\MCP-Control-Plane` is not authority.

Inspect: `C:\Users\ynotf\.cursor\mcp.json` and `C:\Users\ynotf\.cursor\rules\*.mdc`.
Back up `mcp.json` to a timestamped copy first.

FIX the rogue-broken Swarm entries (the live config currently launches them incorrectly):

- Replace the `swarmrecall` entry (raw vendored CLI + `${env:SWARMRECALL_API_KEY}`) with the governed stdio launch:

  `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`

- Replace the broken `swarmvault` entry (points to non-existent `C:\Users\ynotf\.agentcore\mcp-wrappers\swarmvault-mcp.ps1`) with:

  `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp`

ENSURE present from the governed renderer: arabold-docs, artiforge, context-fabric, cursor-agent-mcp, filesystem, mcp-debugger, obsidian-vault, playwright, sequential-thinking, serena, swarmrecall, swarmvault. Serena must use the installed `serena.exe` launcher with `start-mcp-server --transport stdio --context ide`; do not use git `uvx` or `--context ide-assistant`. Do not add `global-memory-gateway` unless the current source renderer explicitly contains it.
REMOVE if present: context7, raw mem0, composio, Hostinger, any `*.onrender.com` Swarm URL, `:65432`.
Rules: scan `.cursor/rules/*.mdc` for any `mem0`/`composio`/`D:\MCP-Control-Plane`-as-authority language and align to the universal rule contract (see `docs/prompts/README.md`).

After editing: keep all `${env:...}` references (no literals, no `.env`); verify MCP tool discovery; restart Cursor; report active servers + proof that swarmvault now launches. Concise change summary; do not rewrite backups.
