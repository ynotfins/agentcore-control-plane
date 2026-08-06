# Swarm Foreign Boundary

Foreign ecosystem: Swarm

Canonical control-plane path: `D:\github\swarm-ecosystem-control`

Canonical repository URL: `https://github.com/ynotfins/swarm-ecosystem.git`

**Operator amendment:** `AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE`  
ADR: `docs/adr/ADR-2026-08-01-neutral-shared-swarmrecall-context-engine.md`

## Operator-Locked Ownership Model

Lock approval: `AUTH-2026-08-06-PC-MEMORY-RUNTIME-OWNERSHIP`

1. **SwarmClaw/Sally** MUST own Swarm operation, canonical Swarm agents, sessions, tasks, schedules, approvals, recovery, restart recovery, and lifecycle.
2. **SwarmRecall** (one deployment) MUST remain neutral machine-level semantic memory — neither AgentCore-owned nor Swarm-owned exclusive runtime. Separately credentialed bounded clients MUST be issued for each ecosystem.
3. **SwarmVault** MUST own the Swarm document/wiki/graph/RAG corpus and bounded context packs.
4. **AgentCore** MUST own exact IDE prompts, evidence, identity, provenance, recovery, Bifrost and agentcore-gateway, and LangGraph production checkpoints in AgentCore PG18.
5. Enrolled IDEs MUST use only `agentcore-gateway` → `agentcore-memory` → neutral SwarmRecall for curated semantic projection/retrieval.
6. IDEs MUST NOT receive raw SwarmRecall or SwarmVault MCP/API access, PostgreSQL/Meilisearch credentials, or direct SQL.
7. LangGraph checkpoints MUST NOT enter SwarmRecall, SwarmVault, or SwarmClaw SQLite.
8. Swarm normal maintenance is not AgentCore daily operational work. AgentCore remains responsible for its own adapter, gateway, and client enrollment.
9. No statement in this document grants either ecosystem authority to mutate the other.

### Change control

Semantic changes to this ownership model require:

- Written operator approval bearing an `AUTH` identifier;
- A rollback backup created before the change is applied;
- Validators confirming the change does not violate locked ownership boundaries;
- Independent review; and
- Re-lock after the change is accepted.

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
