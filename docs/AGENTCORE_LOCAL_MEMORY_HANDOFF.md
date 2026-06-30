# AgentCore Local Memory Handoff

Generated: 2026-06-26

Purpose: preserve the current AgentCore database, storage, SwarmVault, SwarmRecall, and multi-agent governance context for Cursor, Codex, OpenClaw/ClawX, Open Interpreter, MiniMax, and future controller agents.

This handoff is non-secret. It records paths, ports, architecture decisions, validation gates, and open blockers, but not passwords, API keys, bearer tokens, cookies, private keys, or license material.

## Current User Intent

Tony wants a local-only, governed, lossless multi-agent memory system backed by the new 4 TB NVMe and the existing 6 TB external drive.

The target operating model is:

- `F:` Samsung 990 Pro 4 TB NVMe is the active AgentCore runtime drive.
- About 2 TB of `F:` is reserved for PostgreSQL/pgvector and related AgentCore runtime data.
- About 2 TB of `F:` is reserved for SwarmVault, SwarmRecall, and local persistent agent memory.
- `E:` 6 TB external drive is archive, cold backup, export, and rollback storage.
- Docker must not own persistent SwarmVault or SwarmRecall storage.
- Normal IDE agents must use the governed `global-memory-gateway`; direct SQL is reserved for approved admin/ingest runners.

## Source And Live Roots

- Source repo being hardened: `D:\github\agentcore-control-plane`
- Live control-plane root still referenced by active scheduled tasks and WAL archive command: `D:\MCP-Control-Plane`
- Primary runtime root: `F:\AgentCore`
- Primary archive roots: `E:\AgentCoreArchive` and `E:\AgentCoreBackups`

Important rule: do not edit live client configs, live scheduled-task targets, or `D:\MCP-Control-Plane` from this repo unless explicitly approved as a live rollout.

## Unified Memory Rollout Lock

The current approved rollout is locked to a gateway-governed three-layer model:

1. `global-memory-gateway` is the only normal agent write path.
2. `agent_core` on `127.0.0.1:55432` is the canonical governed memory database.
3. `SwarmRecall` is the shared local memory runtime and retrieval backend, but not a default broad MCP surface for every IDE.
4. `SwarmVault` is the shared local wiki/RAG substrate on `F:\AgentCore\agentmemory\swarmvault`.
5. Projection and synchronization into `SwarmRecall` and `SwarmVault` are handled by control-plane jobs, not by per-client dual-write behavior.
6. Full rollout completion is not proven until the live clients have restarted onto the governed config set and `ops\Test-AgentCoreLiveClientAdoption.ps1` passes.

## PostgreSQL And pgvector

Verified active database model:

- Deployment: native Windows PostgreSQL, not Docker.
- Engine path: `F:\AgentCore\postgres_runtime_engine\pgsql\bin\postgres.exe`
- Data directory: `F:\AgentCore\database_cluster`
- Host: `127.0.0.1`
- Port: `55432`
- Database: `agent_core`
- PostgreSQL version: `16.6`
- pgvector version: `0.8.2`
- Startup owner: `\AgentCore\PostgresRuntime`
- Startup command: `D:\github\agentcore-control-plane\ops\Start-AgentCorePostgres.ps1 -StartIfStopped`
- Vector dimensions: `1536`
- Main vector table: `global_vector_memory_store`
- Telemetry table: `agent_cross_project_telemetry`

Known archive behavior:

- WAL archive command currently invokes `D:/MCP-Control-Plane/ops/Archive-AgentCoreWal.ps1`.
- Active archive family is under `E:\AgentCoreArchive\backups_cold\pgvector`.
- Do not collapse `E:\AgentCoreArchive` and `E:\AgentCoreBackups` without a deliberate migration because live archive references still point at the inherited archive root.

Normal routing:

- `agent_admin`: migrations, schema maintenance, backup/restore validation.
- `agent_ingest`: governed gateway and approved ingest writes.
- `agent_read`: read-only inspection and validation.
- `postgres`: break-glass local maintenance.
- Normal agents should not direct-SQL into the database.

## Global Memory Gateway

The normal governed memory path is:

1. Agent calls `global-memory-gateway`.
2. Gateway validates content and metadata.
3. Gateway generates or accepts a compliant 1536-dimensional embedding.
4. Gateway writes to PostgreSQL/pgvector using the approved role.

Gateway credential issue captured during the earlier handoff:

- A direct attempt to append this context into `global-memory-gateway` failed because the gateway attempted to connect to `127.0.0.1:55432` without a supplied password.
- Do not bypass this by writing raw SQL as a normal agent.
- The Codex config was later corrected to supply the PostgreSQL-backed `global-memory-gateway` contract through Windows environment variables without printing secrets. Keep validating this with the global-memory-system validator before broad MCP rollout.

## SwarmVault

Current official source posture:

- Official repo: `https://github.com/swarmclawai/swarmvault`
- Upstream describes SwarmVault as local-first.
- First-run operation can use a built-in heuristic provider locally/offline.
- Expected on-disk vault layout includes `raw/`, `wiki/`, `state/`, and `agent`.
- `SWARMVAULT_OUT` is the relevant output-placement control.

Local state verified before this handoff:

- Source checkout exists at `D:\github\vendor\swarm\swarmvault`.
- Runtime root exists at `F:\AgentCore\agentmemory\swarmvault`.
- Vendored CLI build exists at `D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js`.
- Verified initialized runtime folders:
  - `raw`
  - `wiki`
  - `state`
  - `agent`
  - `inbox`
- Verified local files:
  - `swarmvault.config.json`
  - `swarmvault.schema.md`
- No global `swarmvault` install is required for the validated local path.
- No SwarmVault process or scheduled task is enabled by default.

Required activation target:

- Build or invoke SwarmVault deterministically from vendored source or a pinned package.
- Initialize local/offline/heuristic mode under `F:\AgentCore\agentmemory\swarmvault`.
- Keep all persistent SwarmVault artifacts on `F:` or approved archive/export paths.
- Avoid uncontrolled global installation unless explicitly approved or justified.
- Add or verify `ops\Invoke-AgentCoreSwarmVault.ps1` and `ops\Test-AgentCoreSwarmVault.ps1`.

Validation target:

- `raw/`, `wiki/`, `state/`, and `agent` exist under `F:\AgentCore\agentmemory\swarmvault`.
- A local ingest/compile/query smoke test passes.
- No cloud provider, hosted API, hidden Docker volume, or unapproved C-drive persistence is required for the local AgentCore path.

## SwarmRecall

Current official source posture:

- Official repo: `https://github.com/swarmclawai/swarmrecall`
- Public README language currently presents SwarmRecall as hosted persistence, but the source tree supports a self-hosted local stack.
- Official `docker-compose.yml` uses local Postgres/pgvector and Meilisearch.
- Official `.env.example` shows local `DATABASE_URL`, `MEILISEARCH_URL`, API port `3300`, dashboard port `3400`, optional Upstash variables, Firebase dashboard variables, and local HuggingFace embeddings.
- API source defaults to port `3300`.
- SDK source defaults to hosted `https://swarmrecall-api.onrender.com` if no base URL override is supplied.
- MCP docs and SDK support local override through an explicit API URL/base URL.

Tony's amended requirement:

- SwarmRecall is a local-only activation target, not a hosted service.
- No hosted fallback may be active for AgentCore agents.
- No Upstash may be required.
- No Firebase cloud dependency may be required for the AgentCore agent path.
- No hidden Docker volume may own persistent state.
- Docker must not be used for persistent SwarmRecall storage.

Preferred local design:

- Use the existing native PostgreSQL engine on `F:\AgentCore`.
- Create a separate `swarmrecall` database on `127.0.0.1:55432`.
- Create a least-privilege SwarmRecall role.
- Store all SwarmRecall persistent data under either native PostgreSQL data paths already under `F:\AgentCore\database_cluster` or `F:\AgentCore\agentmemory\swarmrecall`.
- Run SwarmRecall API locally, normally at `http://127.0.0.1:3300`.
- Set `SWARMRECALL_API_URL=http://127.0.0.1:3300` for CLI/MCP/SDK use.
- Override HuggingFace cache to an approved `F:` path before loading embeddings.
- If Meilisearch is used, persist its data under `F:\AgentCore\agentmemory\swarmrecall\meilisearch`.

Current validated state:

- Source checkout exists at `D:\github\vendor\swarm\swarmrecall`.
- Runtime root exists at `F:\AgentCore\agentmemory\swarmrecall`.
- Local config exists at `F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json`.
- Native Meilisearch binary exists at `F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe`.
- Meilisearch data path is `F:\AgentCore\agentmemory\swarmrecall\meilisearch\data`.
- Local HuggingFace cache path is `F:\AgentCore\agentmemory\swarmrecall\hf-cache`.
- Separate database `swarmrecall` exists on native PostgreSQL.
- Least-privilege role `swarmrecall_app` exists.
- Live `pg_hba.conf` was updated with scoped localhost `hostssl` rules for `swarmrecall_app` on database `swarmrecall`.
- Local API health succeeds on `http://127.0.0.1:3300`.
- Local registration succeeds and a local API key is now stored in the Windows environment.
- Local CLI call succeeds against the local API.
- Local MCP stdio probe succeeds against the local API with explicit `SWARMRECALL_API_URL`.
- API listener is loopback-only on `127.0.0.1:3300`.
- Exactly one Meilisearch listener is active on `127.0.0.1:7700`.
- Meilisearch process args no longer expose `--master-key`.
- PostgreSQL, SwarmRecall API, and Meilisearch are now owned by AgentCore scheduled tasks, not Cursor background terminals:
  - `\AgentCore\PostgresRuntime`
  - `\AgentCore\SwarmRecallApi`
  - `\AgentCore\SwarmRecallMeilisearch`
- SwarmRecall API startup is gated on PostgreSQL readiness at `127.0.0.1:55432`.
- Aggregate runtime validator passes: `D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1`.

Required deliverables:

- `ops\Invoke-AgentCoreSwarmRecall.ps1`
- `ops\Test-AgentCoreSwarmRecall.ps1`
- `ops\Start-AgentCorePostgres.ps1`
- `ops\Start-AgentCoreSwarmRecallComponent.ps1`
- `ops\Install-AgentCoreSwarmRecallScheduledTasks.ps1`
- `ops\Stop-AgentCoreSwarmRecallRuntime.ps1`
- `ops\Test-AgentCoreRuntimeSuite.ps1`
- Updated docs that make the local-only posture explicit.
- Handoff proof that the hosted SDK default is neutralized by local configuration.

Stop condition:

- If SwarmRecall cannot satisfy local-only operation with non-Docker persistent storage and no hosted fallback, stop before activation and document the exact blocker.

Validation target:

- Local API health succeeds on `127.0.0.1`.
- Agent registration or equivalent local API-key bootstrap succeeds without printing the key.
- MCP/SDK starts against `SWARMRECALL_API_URL=http://127.0.0.1:3300`.
- No runtime URL points at `swarmrecall-api.onrender.com` except source/docs references marked as forbidden defaults.
- Upstash variables are empty/unset and Redis behavior no-ops safely.
- Firebase dashboard auth is not required for the agent memory path.
- Docker volumes are not used for persistent SwarmRecall data.
- Persistent files are on `F:` or approved local PostgreSQL paths.
- These validation targets are now satisfied for the repo-controlled local-only setup path; live client config enablement remains pending by design.

## Docker Boundary

Docker is present on the machine for other stacks, but AgentCore Postgres on `55432` is not Docker.

Known separate Docker stacks include local-agent-stack Postgres on `5432`, n8n, Qdrant, GitHub MCP, and Portainer. These are not the AgentCore database.

For SwarmVault and SwarmRecall:

- Do not allow hidden Docker volumes to hold persistent memory.
- Prefer native Windows processes and explicit `F:` storage.
- If any temporary helper container is ever considered, it must use explicit `F:` bind mounts and must be documented before execution.

## Cursor Execution Plan State

Cursor had a prior plan at:

- `C:\Users\ynotf\.cursor\plans\agentcore_source_hardening_15ba3429.plan.md`

The plan has since been amended by Tony:

- SwarmRecall is no longer presumed blocked.
- SwarmRecall must be attempted as local-only.
- Existing local PostgreSQL on `F:\AgentCore` is the preferred database substrate.
- SwarmRecall should use a separate database and least-privilege role.
- Persistent SwarmVault/SwarmRecall storage must not live in Docker volumes.
- Cursor should update all docs and produce a new accurate handoff after execution.

## Documentation That Must Stay Aligned

At minimum, keep these docs synchronized when execution changes reality:

- `docs\AGENTCORE_LOCAL_MEMORY_HANDOFF.md`
- `docs\SYSTEM_HANDOVER_BLUEPRINT.md`
- `docs\memory_system.md`
- `docs\storage_layout.md`
- `docs\agent_integration_boundaries.md`
- `docs\vendor_repo_map.md`
- `docs\MCP_SERVER_CONFIGURATION_REFERENCE.md`
- `docs\GLOBAL_AGENT_RULES.md`
- `README.md`

If generated outputs drift from source scripts, patch generator scripts first rather than hand-editing only generated artifacts.

## Next Safe Execution Sequence

1. Keep `global-memory-gateway` as the governed cross-project memory writer.
2. Use `Test-AgentCoreRuntimeSuite.ps1` as the first local runtime validation gate.
3. Use the AgentCore scheduled tasks for SwarmRecall service ownership; do not relaunch long-running SwarmRecall services from Cursor chat terminals.
4. Validate Codex and IDE MCP configs against the control-plane policy before live rollout.
5. Roll out SwarmVault/SwarmRecall MCP exposure only through the governed control-plane generator/validator path.
6. After any live config rollout, restart the affected clients and run `D:\github\agentcore-control-plane\ops\Test-AgentCoreLiveClientAdoption.ps1` before claiming live adoption.
7. Continue the high-frequency Codex monitors until context-window pressure, DB health, RAG health, and MCP drift are stable; then reduce cadence.

## Current Open Risks

- `global-memory-gateway` authentication was corrected in Codex config, but must remain under recurring validation because all-agent MCP rollout can drift.
- SwarmVault local runtime is initialized and validated.
- SwarmRecall source/runtime is locally installed and validated as a local-only runtime path.
- SwarmRecall API and Meilisearch are now owned by AgentCore scheduled tasks.
- The hosted default in SwarmRecall SDK must be explicitly overridden before any agent uses it.
- Some legacy scheduled tasks and WAL archive references still point at `D:\MCP-Control-Plane`; source hardening in this repo is not full control-plane migration by itself.
- Live IDE MCP configs have not yet been broadly rolled out to expose SwarmVault or SwarmRecall.

## Source References

- SwarmVault README: `https://github.com/swarmclawai/swarmvault`
- SwarmRecall README: `https://github.com/swarmclawai/swarmrecall`
- SwarmRecall Docker Compose: `https://raw.githubusercontent.com/swarmclawai/swarmrecall/main/docker-compose.yml`
- SwarmRecall env example: `https://raw.githubusercontent.com/swarmclawai/swarmrecall/main/.env.example`
- SwarmRecall API source: `https://raw.githubusercontent.com/swarmclawai/swarmrecall/main/packages/api/src/index.ts`
- SwarmRecall Redis source: `https://raw.githubusercontent.com/swarmclawai/swarmrecall/main/packages/api/src/lib/redis.ts`
- SwarmRecall embeddings source: `https://raw.githubusercontent.com/swarmclawai/swarmrecall/main/packages/api/src/lib/embeddings.ts`
- SwarmRecall SDK source: `https://raw.githubusercontent.com/swarmclawai/swarmrecall/main/packages/sdk/src/client.ts`
- SwarmRecall MCP README: `https://raw.githubusercontent.com/swarmclawai/swarmrecall/main/packages/mcp/README.md`
