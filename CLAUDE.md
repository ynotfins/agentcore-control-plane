# CLAUDE.md — AgentCore Control Plane

`AGENTS.md` and `PROJECT_ANCHOR.md` are the canonical contracts for this repo. Read them first; this
file only adds Claude-specific emphasis. If they diverge, `PROJECT_ANCHOR.md` wins.

## Non-Swarm gateway baseline (2026-07-12 override — PROJECT_ANCHOR.md §0)

- Cursor, Claude, Codex, MiniMax, Mavis, Antigravity, and Open Interpreter use the single
  non-Swarm gateway entry `agentcore-gateway` at `http://127.0.0.1:8080/mcp`.
- Cursor's canonical global MCP file is `C:\Users\ynotf\.cursor\mcp.json`; project-level
  gateway duplicates are not normal.
- The default non-Swarm memory identity is `agentcore-memory` behind Bifrost. SwarmRecall,
  SwarmVault, and SwarmClaw remain separate Swarm ecosystem components and are not required
  in non-Swarm IDE MCP baselines.
- `global-memory-gateway` remains retired from IDE defaults.

## Guardrails

- Source authority = `D:\github\agentcore-control-plane`; `D:\MCP-Control-Plane` is evidence only.
- Secrets: Windows User-scope environment variables only. Never print values; never create `.env`;
  never commit secrets, rendered PAT URLs, DB dumps, or `F:\AgentCore` runtime state.
- Drives: `C:` OS/config, `D:` repos/projects/worktrees, `E:` archive/cold, `F:` hot DB/RAG/search,
  `G:` backup, `H:` AgentRuntime (live Bifrost gateway — never format), `I:` disposable scratch,
  `J:` portable media. Postgres `127.0.0.1:55432`; `agent_core` and `swarmrecall` are separate DBs;
  `:65432` is forbidden.
- Renderers under `renderers/` are marked read-only by convention; clear the attribute only for an
  approved edit and restore it afterward.
- DepWire: primary route is through `agentcore-gateway` (Bifrost `depwire` upstream). The local CLI at
  `C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd mcp` (`depwire-cli@1.8.2`) is a diagnostics-only
  fallback. Telemetry stays enabled — do **not** set `DEPWIRE_NO_TELEMETRY` unless the operator
  explicitly asks. The local MCP server has no API/license key; Pro activation is the Cursor/VS Code
  extension setting `depwire.licenseKey` only. Use verified local repo paths and require approval for
  remote clone/pull. Keep `.depwire/` cache/runtime state and `depwire-output.json` globally ignored.
- Project execution: follow `docs/agent-policy/` (New Project Bootstrap, Milestones, Macro/Micro
  checklists, tool audits, progressive tool disclosure). Memory/database work follows
  `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`.
- Git: push after every completed task; do not pull/fetch/merge/rebase unless the operator asks.

## Runtime facts

```text
Bifrost gateway: http://127.0.0.1:8080/mcp   (H:\AgentRuntime\bifrost; scheduled task \AgentCore\AgentCore-Bifrost-Gateway)
PostgreSQL 16:   127.0.0.1:55432   (F:\AgentCore\database_cluster; PG18 platform arrives per memory-platform M1)

Swarm ecosystem (separate — not part of non-Swarm IDE baselines):
SwarmRecall API: http://127.0.0.1:3300   (health /api/v1/health)
Meilisearch:     http://127.0.0.1:7700
SwarmVault root: F:\AgentCore\agentmemory\swarmvault   (file-based)
Swarm launchers: ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp ; ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp
```
