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
- Project continuity is default-deny through `contracts/agentcore-project-enrollment.json`.
  The exact project key and repository/worktree path must be enrolled before any memory read/write;
  ordinary IDE profiles expose no project-router controls.

## Guardrails

- Source authority = `D:\github\agentcore-control-plane`; `D:\MCP-Control-Plane` is evidence only.
- Secrets: Windows User-scope environment variables only. Never print values; never create `.env`;
  never commit secrets, rendered PAT URLs, DB dumps, or `F:\AgentCore` runtime state.
- Drives: `C:` OS/config, `D:` repos/projects/worktrees, `E:` archive/cold, `F:` AgentCore hot DB/RAG/search/runtime,
  `G:` backup, `H:` reserved for Swarm hot runtime/data, `I:` disposable scratch,
  `J:` portable media. PostgreSQL 18 `agent_core` / `cognee_core` uses `127.0.0.1:55433`;
  PostgreSQL 16 at `127.0.0.1:55432` is preserved only for rollback/legacy evidence and Swarm-owned
  databases. `:65432` is forbidden.
- Renderers under `renderers/` are marked read-only by convention; clear the attribute only for an
  approved edit and restore it afterward.
- DepWire: the shared implicit-project Bifrost upstream is dormant. Use a host-owned explicit-cwd
  local CLI diagnostic when structurally required. Telemetry stays enabled — do **not** set `DEPWIRE_NO_TELEMETRY` unless the operator
  explicitly asks. The local MCP server has no API/license key; Pro activation is the Cursor/VS Code
  extension setting `depwire.licenseKey` only. Use verified local repo paths and require approval for
  remote clone/pull. Keep `.depwire/` cache/runtime state and `depwire-output.json` globally ignored.
- Project execution: follow `docs/agent-policy/` (New Project Bootstrap, Milestones, Macro/Micro
  checklists, tool audits, progressive tool disclosure). Memory/database work follows
  `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`.
- Git: push after every completed task; do not pull/fetch/merge/rebase unless the operator asks.

## Runtime facts

```text
Bifrost gateway: http://127.0.0.1:8080/mcp   (F:\AgentCore\runtime\bifrost; scheduled task \AgentCore\AgentCore-Bifrost-Gateway)
PostgreSQL 18:   127.0.0.1:55433   (F:\PostgreSQL18\data; canonical AgentCore agent_core + cognee_core)
PostgreSQL 16:   127.0.0.1:55432   (F:\AgentCore\database_cluster; rollback/legacy evidence and Swarm-owned DBs only)

Neutral semantic exception: SwarmRecall is reached server-side through agentcore-memory only.
All Swarm runtime paths, launchers, credentials, and mutable facts remain under swarm-ecosystem-control authority.
```
