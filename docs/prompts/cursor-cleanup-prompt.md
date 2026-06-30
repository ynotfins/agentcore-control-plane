# Cursor — Self-Cleanup Prompt

> Paste into Cursor. Edits ONLY Cursor's own config/rules. Do not print secrets.

Reconcile Cursor's live MCP config to the governed source renderer `renderers/cursor-global.mcp.json` in `D:\github\agentcore-control-plane`. Source authority is that repo; `D:\MCP-Control-Plane` is not authority.

Inspect: `C:\Users\ynotf\.cursor\mcp.json` and `C:\Users\ynotf\.cursor\rules\*.mdc`.
Back up `mcp.json` to a timestamped copy first.

FIX the rogue-broken Swarm entries (the live config currently launches them incorrectly):
- Replace the `swarmrecall` entry (raw vendored CLI + `${env:SWARMRECALL_API_KEY}`) with the governed stdio launch:
  `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- Replace the broken `swarmvault` entry (points to non-existent `C:\Users\ynotf\.agentcore\mcp-wrappers\swarmvault-mcp.ps1`) with:
  `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp`

ENSURE present (governed local baseline): arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, serena, swarmrecall, swarmvault. (cursor-agent-mcp / context-fabric / mcp-debugger are staged for the next baseline expansion.)
REMOVE if present: context7, raw mem0, composio, Hostinger, any `*.onrender.com` Swarm URL, `:65432`.
Rules: scan `.cursor/rules/*.mdc` for any `mem0`/`composio`/`D:\MCP-Control-Plane`-as-authority language and align to the universal rule contract (see `docs/prompts/README.md`).

After editing: keep all `${env:...}` references (no literals, no `.env`); verify MCP tool discovery; restart Cursor; report active servers + proof that swarmvault now launches. Concise change summary; do not rewrite backups.
