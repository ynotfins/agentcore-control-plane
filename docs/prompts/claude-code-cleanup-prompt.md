# Claude Code — Self-Cleanup Prompt

> Paste this into Claude Code. It edits ONLY Claude Code's own config/rules. Do not print secret values.

You are cleaning Claude Code's own MCP configuration and rules on CHAOSCENTRAL to match the AgentCore governed baseline. Source authority is `D:\github\agentcore-control-plane`. Do not treat `D:\MCP-Control-Plane` as authority.

Inspect:
- `C:\Users\ynotf\.claude.json` (primary — runtime discovery showed the active forbidden routes here)
- `C:\Users\ynotf\.claude\config.json` (reconcile)
- `C:\Users\ynotf\.claude\rules\context7.md` and `C:\Users\ynotf\.claude\skills\context7-mcp\` (retire)
- `CLAUDE.md` and any project `.mcp.json`

Back up first: copy `.claude.json` and `.claude\config.json` to a timestamped backup beside them before editing.

REMOVE (forbidden active routes):
- `context7` MCP server (retired — use `arabold-docs`).
- `hostinger-hosting`, `hostinger-domains`, `hostinger-dns`, `hostinger-vps` MCP servers.
- The retired `context7.md` rule and `context7-mcp` skill.

SECRET (do NOT print the value):
- `.claude.json` contains a live `CONTEXT7_API_KEY` literal. After removing the `context7` server, the key is unused. **Rotate it at the provider and remove the literal** — this requires operator approval; if you cannot rotate now, remove the `context7` server block (which carries the literal) and record that rotation is still required. Never echo the value.
- `HOSTINGER_API_TOKEN` / `API_TOKEN` literals: remove with their server blocks.

ADD (governed baseline; swarmvault uses the swarmvault-lite profile for Claude Code):
- `swarmrecall` (stdio): `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
- `swarmvault` (stdio): `pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp`
- `global-memory-gateway`, `arabold-docs`, `serena`, `sequential-thinking`, `artiforge`, `obsidian-vault`, `context-fabric` per the governed shapes in `contracts/master-mcp-server-config.json`. Use Windows env var references only; no `.env`.
- A staged candidate config is provided at `artifacts/staging/claude-code/claude-code.mcp.json` — use it as the reference shape.

ENFORCE the universal rule contract (see `docs/prompts/README.md`): governed memory via `global-memory-gateway` (`memory_append`/`memory_search`); native recall via `swarmrecall`; RAG/context via `swarmvault`; `arabold-docs` not context7; never raw-SQL or dual-write; never write `F:\AgentCore` by filesystem; never store secrets.

After editing: preserve auth/profile/session state; verify MCP tool discovery in Claude Code; restart; report which servers are active, confirm context7/Hostinger are gone, confirm no secret value was printed, and state whether `CONTEXT7_API_KEY` rotation is still pending. Write a concise summary of changed files; do not rewrite backups/history.
