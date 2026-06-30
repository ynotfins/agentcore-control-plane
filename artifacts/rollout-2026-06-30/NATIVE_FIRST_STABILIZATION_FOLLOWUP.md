# Native-First Stabilization — Follow-up (2026-06-30)

Concise current-state follow-up. The stable constitution is `PROJECT_ANCHOR.md`; the doc hierarchy is `DOC_AUTHORITY.md`. This file is current-state/mutable.

## Native-first order (authoritative sequence)
1. Native SwarmRecall green (local MCP/API/CLI).
2. Native SwarmVault green (doctor/retrieval/graph; query timeout-bounded).
3. AgentCore gateway/projector wrapper verification.
4. Multi-IDE renderer/prompt adoption.
5. `memory_catalog` / `database-plan.md` migrations — later, approval-gated.

AgentCore wrappers, renderers, projectors, validators, `memory_catalog`, and cross-IDE enforcement **wrap** native tools only after native behavior is proven. They never replace native best practice.

## Status

| Layer | Status | Evidence |
|-------|--------|----------|
| 1. Native SwarmRecall | **GREEN** | `Test-AgentCoreSwarmRecall.ps1` 25/25; 53 MCP tools; local-only loopback 3300/7700/55432; health ok |
| 2. Native SwarmVault | **GREEN smokes; query BLOCKED (timeout-bounded)** | `doctor` 2465 sources / 5 managed / 7071 pages / 20545 nodes, retrieval fresh; `retrieval status` fresh; `graph stats` rich; `query` fail-fast BLOCKED at 60s |
| 3. Gateway/projector wrapper | Verified via projector evidence | SwarmRecall CLI shows 103 governed-projection memories (`gateway → agent_core → projector → SwarmRecall`) |
| 4. Multi-IDE adoption | Source renderers normalized; live cleanup gated | `renderers/*` governed wrappers; `docs/prompts/*` per-IDE prompts (run in each IDE) |
| 5. memory_catalog / migrations | NOT applied (authored only) | `migrations/0001–0005` dry-run only; `Test-AgentCoreUnifiedRetrieval.ps1` SKIP pre-migration |

## Hard runtime facts (unchanged)
PostgreSQL `127.0.0.1:55432`; `agent_core` and `swarmrecall` are **separate** DBs in one cluster; SwarmRecall API `http://127.0.0.1:3300` (health `/api/v1/health`); Meilisearch `http://127.0.0.1:7700`; SwarmVault `F:\AgentCore\agentmemory\swarmvault`; projection state `F:\AgentCore\agentmemory\projection-state`; `E:` archive/cold/spool only; no active `:65432` route.

## SwarmVault validator behavior
`ops/Test-AgentCoreSwarmVault.ps1` is native-first + timeout-bounded (never hangs): read-only smokes first, `query` single-attempt fail-fast BLOCKED on `-QueryTimeoutSeconds` (default 60), `context build` SKIP unless `-IncludeContextBuild`. Use `-SkipQuery` for a fast native-only pass. Source registration guidance: `docs/SWARMVAULT_SOURCE_REGISTRATION.md` (no broad recursive `source add`; exclude node_modules/.next/dist/build/coverage/.git/generated).

## Gated (require operator approval)
- SwarmVault full `query` performance tuning (raise timeout / narrow scope).
- Live IDE cleanup prompts (per IDE; Claude Code first) + `CONTEXT7_API_KEY` rotation.
- DB migration apply (backup + dry-run + sign-off); scheduled-task de-registration (elevated).

## Next-chat attachment set
`PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, `database-plan.md`, `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md`, `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md`, and this follow-up report.
