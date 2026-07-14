# Context Window Optimization Policy

> **HISTORICAL — SUPERSEDED (2026-07-14).** The per-client MCP budget model below predates the
> Bifrost cutover. Each non-Swarm IDE now has exactly one `agentcore-gateway` entry; tool exposure
> is governed by capability profiles and progressive tool disclosure
> (`docs/agent-policy/TOOL_LIFECYCLE_POLICY.md`), not per-IDE server budgets. Memory routes through
> `agentcore-memory`, not `global-memory-gateway` or Swarm. The `agentcore-context-window-optimizer`
> monitor was removed/deferred (2026-06-30). The core principle — do not expose every tool to every
> model turn — remains current and is now enforced by the tool-lifecycle policy.

Generated: 2026-06-26

The goal is to maximize effective context for Codex, Cursor, Open Interpreter, OpenClaw, MiniMax, and Mavis without inflating every client with every possible MCP tool.

## Operating Principle

Effective context is improved by:

- selecting the largest stable model/context setting each IDE supports
- keeping the default MCP server surface small and role-specific
- eliminating duplicate tool routes
- routing durable memory through `global-memory-gateway`
- offloading recall and long-form knowledge to SwarmRecall, SwarmVault, and Obsidian through governed paths
- using direct specialized MCP tools only when the active task needs them

The policy is not to expose all backends everywhere. That reduces available reasoning context and increases client instability.

## Default Memory Route

- Normal agent writes: `global-memory-gateway`
- Canonical database: PostgreSQL `agent_core` on `127.0.0.1:55432`
- SwarmRecall: local backend/runtime and retrieval service
- SwarmVault: local RAG/wiki substrate
- Direct SwarmRecall MCP: not default in v1

## Client Budgets

The canonical client server lists and budgets live in `contracts\master-mcp-server-config.json`.

Codex has the tightest default budget and should stay near its master-contract server list unless a task-specific connector is required. OpenClaw has a user-approved `eye2byte` exception and should not be reduced to exact Cursor parity.

## Monitor Duties

`agentcore-context-window-optimizer` runs every two hours during stabilization and must:

- run `ops\Test-AgentCoreContextWindowPolicy.ps1`
- inspect the master MCP contract and live client configs
- identify duplicate servers, retired routes, and unexpected broad tool surfaces
- recommend or apply only low-risk source-controlled fixes
- prefer source generator fixes over one-off live config edits
- report model/context settings where discoverable
- avoid printing secrets

## Stabilization Exit

After several clean cycles:

- reduce the context-window monitor cadence to weekly or twice weekly
- keep runtime/database/RAG health monitors at the cadence justified by active workloads
- keep direct backend MCP exposure opt-in and documented by client
