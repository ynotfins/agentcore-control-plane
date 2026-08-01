# Swarm Foreign Boundary

Foreign ecosystem: Swarm

Canonical control-plane path: `D:\github\swarm-ecosystem-control`

Canonical repository URL: `https://github.com/ynotfins/swarm-ecosystem.git`

**Operator amendment:** `AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE`  
ADR: `docs/adr/ADR-2026-08-01-neutral-shared-swarmrecall-context-engine.md`

Foreign authority lives in:

- `D:\github\swarm-ecosystem-control\SWARM_PROJECT_ANCHOR.md`
- `D:\github\swarm-ecosystem-control\SWARM_DOC_AUTHORITY.md`
- `D:\github\swarm-ecosystem-control\SWARM_BLUEPRINT.md`
- `D:\github\swarm-ecosystem-control\contracts\runtime-ports.yaml`
- `D:\github\swarm-ecosystem-control\contracts\storage-layout.yaml`
- `D:\github\swarm-ecosystem-control\contracts\memory-ownership.yaml`

AgentCore and Swarm remain independent control planes for **execution runtimes**. They share a machine and may both be **clients** of one **neutral shared SwarmRecall** semantic-memory plane.

## Neutral shared SwarmRecall (machine-level)

- One SwarmRecall API + PostgreSQL 16/pgvector + Meilisearch deployment serves cross-client curated semantic memory.
- Classification: **neutral infrastructure** — not AgentCore-owned runtime, not Swarm-owned runtime.
- AgentCore access: server-side adapter inside `agentcore-memory` only (via `agentcore-gateway` for IDEs).
- Swarm access: SwarmClaw bounded REST/SDK adapter only — SwarmClaw must not call Bifrost.
- Ordinary IDE baselines must never install raw SwarmRecall MCP tools or Recall credentials.
- Exact AgentCore evidence and LangGraph checkpoints remain on PG18. SwarmClaw transcripts/tasks remain SQLite. SwarmVault remains Swarm-owned.

## Still forbidden

- AgentCore must not consume SwarmVault graph/wiki/state as AgentCore memory.
- AgentCore must not consume SwarmClaw sessions, tasks, prompts, or runtime SQLite as AgentCore continuity.
- AgentCore must not use Swarm credentials, SwarmVault backup roots, or Swarm MCP entries as an AgentCore / enrolled non-Swarm IDE baseline.
- No normal AgentCore IDE continuity on Swarm **product** projects; selected Swarm-owned paths stop with `swarm_project_refused`.
- Dual-Recall (second AgentCore-owned Recall instance) is rejected.
- Non-loopback exposure and cross-device sync remain deferred.

## Shared-machine collision constraints

- AgentCore PG18, Bifrost, Cognee, and IDE gateway contracts remain AgentCore-exclusive.
- SwarmClaw operational data and SwarmVault remain Swarm-exclusive.
- Neutral Recall/PG16/Meili may be used by both clients with separately issued API keys.
- AgentCore hot namespace remains `F:\AgentCore\...` for AgentCore runtime; Swarm hot operational data remains on `H:`; cold backups under `E:\` with non-overlapping namespaces. Neutral Recall may continue in-place on the verified live loopback stack (`:3300` / `:65432` / `:7700`) after reclassification.

Last verification timestamp: `2026-08-01T21:21:18Z`
