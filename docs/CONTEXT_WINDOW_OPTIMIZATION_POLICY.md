# Context Window Optimization Policy

> **HISTORICAL — SUPERSEDED (2026-07-14).** The per-client MCP budget model below predates the
> Bifrost cutover. Each non-Swarm IDE now has exactly one `agentcore-gateway` entry; tool exposure
> is governed by capability profiles and progressive tool disclosure
> (`docs/agent-policy/TOOL_LIFECYCLE_POLICY.md`), not per-IDE server budgets. AgentCore/enrolled
> non-Swarm IDE memory routes through `agentcore-memory` to neutral SwarmRecall server-side, not
> through `global-memory-gateway` or raw Swarm MCP entries. The `agentcore-context-window-optimizer`
> monitor was removed/deferred (2026-06-30). The core principle — do not expose every tool to every
> model turn — remains current and is now enforced by the tool-lifecycle policy.

Generated: 2026-06-26

Historical goal captured below: maximize effective context for Codex, Cursor, Open Interpreter, OpenClaw, MiniMax, and Mavis without inflating every client with every possible MCP tool.

## Operating Principle

Effective context is improved by:

- selecting the largest stable model/context setting each IDE supports
- keeping the default MCP server surface small and role-specific
- eliminating duplicate tool routes
- routing durable memory through `global-memory-gateway` (historical; current route is `agentcore-gateway` -> `agentcore-memory` -> neutral SwarmRecall server-side)
- offloading recall and long-form knowledge to SwarmRecall, SwarmVault, and Obsidian through governed paths (historical; current ordinary IDEs receive no raw SwarmRecall/SwarmVault MCP)
- using direct specialized MCP tools only when the active task needs them

The policy is not to expose all backends everywhere. That reduces available reasoning context and increases client instability.

## Default Memory Route

- Historical normal agent writes: `global-memory-gateway`
- Current AgentCore/enrolled non-Swarm IDE route: `agentcore-gateway` -> `agentcore-memory` -> neutral SwarmRecall server-side semantic adapter plus AgentCore PG18 exact evidence.
- Current canonical AgentCore exact-evidence database: PostgreSQL 18 `agent_core` on `127.0.0.1:55433`.
- Current ordinary IDE baseline: no raw SwarmRecall, SwarmVault, PostgreSQL, Meilisearch, or direct SQL credentials.

## Client Budgets

Historical client server lists and budgets lived in `contracts\master-mcp-server-config.json`. Current MCP exposure authority is `contracts\bifrost-upstream-mcp-registry.json`, `contracts\agentcore-gateway-client.json`, `MASTER_CONFIG_AND_PROMPT.md`, and `docs/agent-policy/TOOL_LIFECYCLE_POLICY.md`.

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
