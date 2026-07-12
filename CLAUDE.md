# CLAUDE.md — AgentCore Control Plane

`AGENTS.md` and `PROJECT_ANCHOR.md` are the canonical contracts for this repo. Read them first; this
file only adds Claude-specific emphasis. If they diverge, `PROJECT_ANCHOR.md` wins.

## Native-first memory (2026-07-01 override — PROJECT_ANCHOR.md §0)

- Native SwarmRecall (memory/graph/learnings/skills/pools) + native SwarmVault (RAG/wiki/context/
  task ledger) are the automatic default memory/RAG plane for every IDE and agent.
- `global-memory-gateway` is RETIRED from the mandatory baseline and from all IDE default configs,
  renderers, and the master contract default surfaces (now in `default_exclusions.must_not_emit`).
  Do not re-introduce it into any IDE baseline.
- The `agent_core` governed DB (`127.0.0.1:55432`) and the memory projector remain available for
  governed/curated flows but are not the default IDE memory route.

## Guardrails

- Source authority = `D:\github\agentcore-control-plane`; `D:\MCP-Control-Plane` is evidence only.
- Secrets: Windows User-scope environment variables only. Never print values; never create `.env`;
  never commit secrets, rendered PAT URLs, DB dumps, or `F:\AgentCore` runtime state.
- Drives: `C:` OS/config, `D:` repos/projects/worktrees, `F:` hot DB/RAG/search, `E:` archive/cold,
  `G:` backup. Postgres `127.0.0.1:55432`; `agent_core` and `swarmrecall` are separate DBs; `:65432`
  is forbidden.
- Renderers under `renderers/` are marked read-only by convention; clear the attribute only for an
  approved edit and restore it afterward.
- DepWire uses global `depwire-cli@1.8.2` at
  `C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd mcp` with `DEPWIRE_NO_TELEMETRY=1`. Its local
  MCP server has no API/license key; Pro activation is the Cursor/VS Code extension setting
  `depwire.licenseKey` only. Use verified local repo paths and require approval for remote clone/pull.
  Keep the local `.depwire/` cache/runtime directory and `depwire-output.json` globally ignored.
- Git: push after every completed task; do not pull/fetch/merge/rebase unless the operator asks.

## Runtime facts

```text
PostgreSQL:      127.0.0.1:55432   (F:\AgentCore\database_cluster)
SwarmRecall API: http://127.0.0.1:3300   (health /api/v1/health)
Meilisearch:     http://127.0.0.1:7700
SwarmVault root: F:\AgentCore\agentmemory\swarmvault   (file-based)
Swarm launchers: ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp ; ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp
```
