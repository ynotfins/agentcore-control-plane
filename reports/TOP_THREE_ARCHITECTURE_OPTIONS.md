# TOP_THREE_ARCHITECTURE_OPTIONS — CHAOSCENTRAL

**Generated:** 2026-07-03
**Goal:** Provide every IDE and agent with effectively never-lost project memory — durable lossless storage, rolling summaries, semantic memory, RAG / context packs, a pgvector catalog/pointer plane, and automatic startup retrieval — local-first, on D/E/F, with no forced Docker, verified against evidence.
**Input:** the seven prior reports in this directory (`SYSTEM_INVENTORY`, `PATH_EXISTENCE_AND_REPO_AUDIT`, `INSTALLED_TOOLING_AUDIT`, `IDE_INTEGRATION_MATRIX`, `MEMORY_STACK_AUDIT`, `UNIVERSAL_GATEWAY_VERIFICATION`, `DRIVE_PLACEMENT_PLAN`).
**Output:** Three ranked architecture options.

---

## 1. Recap of Hard Constraints (from prior reports)

These are the constraints every option must respect:

1. **OpenAI-compatible gateway at `localhost:3000` does not exist** (`UNIVERSAL_GATEWAY_VERIFICATION.md`). No option may depend on it.
2. **OpenClaw gateway port is `18789`**, and it is its own control UI, not an OpenAI-compatible proxy.
3. **`global-memory-gateway` is retired from the baseline** (per `master-mcp-server-config.json` v2026-06-26 and HEAD commit on `agentcore-control-plane`). Normal-agent durable writes route through **SwarmRecall** instead.
4. **PostgreSQL + pgvector is cold-start dependent** on Task Scheduler. Any always-on assumption is fragile unless paired with a deterministic cold-start contract.
5. **E: is 932 GB SanDisk SSD, not a 10 TB HDD.** Long-term cold retention must be planned accordingly.
6. **All secrets must be Windows env vars**, not in files. Open Interpreter currently has an inline API key (must be remediated).
7. **Governed wrappers, not direct CLI.** Per `master-mcp-server-config.json`, MCP servers are launched via `ops\Invoke-AgentCoreSwarm*.ps1`, not via raw CLI invocations from IDE configs.
8. **Native-first, no forced Docker.** Docker Desktop is stopped and only required by `github-mcp` Cursor/OpenClaw shape.
9. **Lossless Claw is local-only**, file-based, and not the canonical durable store.
10. **The `memory_catalog` migrations are authored but not applied.** Any option that depends on the unified catalog must include the migration-apply gate.

---

## 2. Option A — "SwarmRecall as Canonical Spine, Native-First" (RECOMMENDED)

### 2.1 Summary

Make **SwarmRecall** the canonical durable memory plane for all IDEs/agents. Each IDE gets a stdio MCP launched via the governed wrapper `ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`. **SwarmVault** is the local-first RAG/wiki substrate, also via governed wrapper. **PostgreSQL/pgvector** is the structured memory spine, used by the projector for catalog mirroring. **LCM/QMD/Obsidian** are local planes with explicit, narrow roles. There is no single routing gateway; each IDE retains its native LLM API and uses stdio MCP for memory.

### 2.2 Component Role

| Component | Role |
|-----------|------|
| PostgreSQL `agent_core` (cold-start) | Structured facts; projector source |
| pgvector `global_vector_memory_store` | Embedding catalog (read-only for normal agents) |
| SwarmRecall (API + Meilisearch + `swarmrecall` DB) | Canonical durable memory; semantic + full-text recall |
| SwarmVault (file-based RAG) | Long-form local RAG; wiki + graph + context packs |
| Lossless Claw (LCM/QMD) | OpenClaw-local lossless context only |
| Obsidian | Long-form human notes (Claude Desktop + selective IDEs) |
| Codex native memories | Codex-specific lossless (project-local) |
| MemoryProjector | Hourly projector from `agent_core` → SwarmRecall → SwarmVault |

### 2.3 Memory Plane Write/Read

- **Normal IDE agents**: write to SwarmRecall via `memory_append`/`memory_search`/`memory_state` MCP tools.
- **Projector**: every 2h, mirrors curated `agent_core` content into SwarmRecall + SwarmVault.
- **Read path**: SwarmRecall first (canonical), then SwarmVault (context pack), then LCM (OpenClaw-local), then Obsidian (human notes), then native IDE memory (e.g., Codex plugin).
- **Startup retrieval**: per-IDE stop/start hook runs `Invoke-AgentCoreSwarmRecall.ps1 -Mode ContextPack` to fetch the most recent context pack matching the active workspace path.

### 2.4 Cold-Start Contract

Deterministic chain:
1. Windows logon → `\AgentCore\PostgresRuntime` starts PG on `:55432`.
2. `\AgentCore\SwarmRecallMeilisearch` starts Meilisearch on `:7700`.
3. `\AgentCore\SwarmRecallApi` starts SwarmRecall API on `:3300`.
4. Each IDE cold-start reads its `mcp.json` and launches `Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp` and `Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` as stdio subprocesses.
5. First MCP `initialize` triggers `memory_search` for the active workspace path → automatic startup retrieval.

### 2.5 Lossless Storage

- **Codex native memories** (`~/.codex\memories_1.sqlite`) are Codex's own lossless plane; not duplicated.
- **OpenClaw LCM** (`~/.openclaw\lossless-claw\`) is OpenClaw's local plane; not duplicated.
- **SwarmRecall** is the canonical cross-project durable plane; backed up via `Backup-AgentCorePostgres.ps1` (PG base backup) + WAL archive on E:.
- **SwarmVault** state is file-based; backed up via `robocopy /MIR F:\AgentCore\agentmemory\swarmvault E:\AgentCoreBackups\swarmvault`.
- **Codex logs** rotation policy: cap at 200 MB with 7-day TTL.

### 2.6 Rolling Summaries + Semantic Memory

- SwarmRecall API has 53 MCP tools including summarization + episodic retrieval (per `ROLLOUT_REPORT.md`).
- `Invoke-AgentCoreMemoryProjector.ps1` runs every 2h, computes embeddings via OpenAI `text-embedding-3-small` (preferred) or `local_hash_v1` (fallback), writes into pgvector +SwarmRecall.
- Rolling summaries: triggered by daily maintenance task — older messages get summarized into `agent_cross_project_telemetry` then compacted in `messages`.

### 2.7 RAG / Context Packs

- SwarmVault produces **context packs** on demand: `Invoke-AgentCoreSwarmVault.ps1 -Mode ContextPack -Query <q> -WorkspacePath <p>`.
- Codex native plugin produces **memory packs** for its own sessions.
- LCM produces QMD context for OpenClaw sessions.
- Combined at the IDE level: each agent assembles `task-local files → SwarmRecall → Obsidian → LCM/QMD`.

### 2.8 pgvector Catalog / Pointers

- pgvector `global_vector_memory_store` (1536-d HNSW cosine) holds embeddings for `messages` + `project_facts`.
- Index for fast ANN queries: HNSW, cosine distance.
- Each row has `source_kind`, `document_source`, `associated_project_path`, `agent_id`, `run_id` metadata.
- Future `memory_catalog` (migrations 0001-0005) will add cross-backend pointers; not required for Option A to function, but the migration path is staged.

### 2.9 Automatic Startup Retrieval

- Codex: `Stop` hook calls `codex-stop-audit.ps1`; startup context comes from the native plugin + `Invoke-AgentCoreSwarmRecall.ps1 -Mode ContextPack`.
- Cursor / OpenClaw / OI / MiniMax / Antigravity / Mavis: on first MCP `initialize`, fetch a context pack for the active workspace.
- Claude Code: staged config does the same; live cleanup prompt activates it.

### 2.10 Strengths

- Matches the current source contract (v2026-06-26).
- Matches the most recent source commit (`Native-first memory: retire global-memory-gateway from baseline`).
- Matches the rollout report's PARTIAL-GREEN verdict — extends rather than replaces the existing baseline.
- No new architecture is needed; the baseline is already validated.
- All governance rules from `database-plan.md` §2, §4, §13 are respected.
- No new install or new service is required.
- Each IDE retains its native LLM API (no proxying through anything).

### 2.11 Weaknesses

- SwarmVault `query` is slow over ~7071 pages; needs tuning.
- PostgreSQL is cold-start dependent; if a user starts the IDE before the Task Scheduler runs, the first MCP call fails.
- No unified catalog yet; agents must know which backend to query (mitigated by the per-IDE context-pack assembly).
- The 2026-06-30 rollout has 6 uncommitted source edits on `agentcore-control-plane`; architecture cannot ship until those are committed or rolled back.

### 2.12 Confidence

**High.** This is what the source contract, the most recent commit, the rollout report, and the canonical handover blueprint all already say. It is "the architecture the codebase is already converging on."

---

## 3. Option B — "Universal Local Gateway (Broker at 18789, Forwarding-Only)"

### 3.1 Summary

Stand up a single HTTP broker on `127.0.0.1:18789` (or a new dedicated port like `127.0.0.1:4318`) that exposes:
- An **OpenAI-compatible** `/v1/chat/completions`, `/v1/embeddings`, `/v1/models` surface, *forwarding* to the IDE's native LLM API (no rewriting of model behavior, just a uniform local entry point).
- An **MCP HTTP** endpoint at `/mcp` that proxies to a small fixed set of stdio MCP servers (SwarmRecall, SwarmVault, Obsidian) via streamable-HTTP.
- A **Lossless Claw bridge** at `/v1/memory/*` that proxies to the local SQLite store.
- Every IDE is reconfigured to point at this broker instead of its native LLM API and native MCP servers.

### 3.2 Why This Was Considered

It would give a "single URL for everything," which is appealing for symmetry, observability, and routing control. It would also let the user add cross-IDE policy in one place (rate limits, audit, content scanning).

### 3.3 Why It Is REJECTED for This Report

1. **Contradicts the source contract.** `master-mcp-server-config.json` v2026-06-26 and HEAD commit explicitly move *away* from a single router. Adding one back reverses the design pivot.
2. **Re-creates the exact failure the audit identified.** The previous planning assumption ("OpenClaw universal gateway at `localhost:3000`") was already rejected in `UNIVERSAL_GATEWAY_VERIFICATION.md`. This option is the same idea with a different port.
3. **No OpenAI-compatible proxy implementation exists on the host.** Building one from scratch would require a new service, new test surface, new failure modes, and new governance.
4. **Lossless Claw is file-based, not HTTP.** Bridging it to HTTP would require writing new server code that does not exist in the codebase.
5. **Conflates two roles.** Routing memory calls and proxying LLM calls are different problems with different governance rules; merging them violates separation of concerns that the design has carefully maintained.
6. **No clear benefit.** Each IDE already has its native LLM API; routing through a local broker adds latency, a new failure mode, and zero new capability. The only real benefit (uniform observability) can be achieved with MCP-level instrumentation without an HTTP broker.
7. **MCP transport is moving toward streamable-HTTP, but the contract still says stdio.** Changing the transport for every IDE is a major change that affects every IDE/agent's renderer and cleanup prompt.

### 3.4 When This Would Become Viable

If the user later wants a uniform LLM API surface (e.g., for cost/usage tracking) and accepts the design implications, a *narrowly scoped* LLM proxy (no memory bridging) could be considered. But it is out of scope for the current "never-lost memory" goal.

### 3.5 Confidence

**Low for this task.** Architecturally coherent in isolation, but contradicts the live source authority.

---

## 4. Option C — "Database-First, All Writes to PostgreSQL, RAG via pgvector Only"

### 4.1 Summary

Make **PostgreSQL/pgvector** the canonical durable plane for every IDE/agent. SwarmRecall is reduced to a thin Postgres projection (or removed entirely). SwarmVault is dropped from the live baseline. LCM is preserved as OpenClaw-local only. Every IDE writes through a single Postgres-backed gateway (a re-introduced `global-memory-gateway`).

### 4.2 Why This Was Considered

It is the simplest mental model: "all memory is in one DB." It would consolidate the canonical surface, simplify backup (just dump Postgres), and let a single SQL query span everything.

### 4.3 Why It Is REJECTED

1. **Contradicts the most recent commit.** *"Native-first memory: retire global-memory-gateway from baseline"* explicitly retires the gateway. This option brings it back.
2. **`database-plan.md` §2 forbids it.** *"No LCM/lossless active backend. LCM is a future source-system type only"* — but more importantly, the design has moved away from single-DB thinking.
3. **Lossy vs. lossless conflated.** PostgreSQL/pgvector is not optimized for lossless long-term session state; it is for structured facts + embeddings. LCM + Codex native + Obsidian exist precisely because they serve different roles.
4. **SwarmRecall is already validated.** Per the rollout report, SwarmRecall is native-green with 53 MCP tools. Throwing it away would discard validated work.
5. **No full-text recall.** pgvector alone gives embeddings. Meilisearch (inside SwarmRecall) provides BM25 + typo-tolerance + faceting. Dropping Meilisearch regresses retrieval quality.
6. **No RAG/wiki substrate.** SwarmVault's wiki/graph/context-packs cannot be replicated in pgvector without writing new code from scratch.
7. **Capacity planning.** Putting every long-form note + log + raw corpus into pgvector would balloon the DB and degrade index performance; the 4 TB NVMe is currently used precisely because the data is spread across multiple specialized stores.

### 4.4 When This Would Become Viable

Never, for the current scope. The design has already moved past single-DB thinking. The "unified memory catalog" (migrations 0001-0005) is the *correct* way to unify, not by collapsing stores but by adding an index over them.

### 4.5 Confidence

**Low.** Direct contradiction with the source contract.

---

## 5. Comparison Matrix

| Dimension | Option A (RECOMMENDED) | Option B (universal broker) | Option C (Postgres-only) |
|-----------|-------------------------|-----------------------------|---------------------------|
| Matches source contract | **Yes** | No | No |
| Matches most recent commit | **Yes** | No | No |
| Matches `database-plan.md` | **Yes** | Partial | No |
| Requires new install | No | Yes (new broker service) | No (uses existing PG) |
| Cold-start complexity | Low (3 task scheduler tasks) | High (broker + PG + Meilisearch + every MCP) | Medium (just PG) |
| Memory plane count | 5 (PG, SwarmRecall, SwarmVault, LCM, Obsidian) | 5 + broker | 2 (PG + LCM) |
| Cross-IDE consistency | High (shared MCP) | High (shared broker) | High (shared DB) |
| Failure blast radius | Per-MCP | Broker-down = all IDEs down | PG-down = all IDEs down |
| Lossless history depth | Strong (per-plane) | Medium (broker mediates) | Weak (PG is not designed for this) |
| Full-text + semantic recall | Yes (Meilisearch + pgvector) | Yes (same) | Partial (pgvector only) |
| RAG wiki/graph | Yes (SwarmVault) | Yes (same) | **No** |
| Long-form human notes | Yes (Obsidian) | Yes (same) | Yes (Obsidian, but file-based only) |
| Per-IDE autonomy | High | Low | Medium |
| Operator mental model | "Use the right MCP for the job" | "Everything goes through one URL" | "Everything is in Postgres" |
| Reversibility | High (per-component) | Low (broker becomes dependency) | Medium (data is recoverable, code is rewritten) |
| Implementation effort | None (baseline already green) | High (new service + new tests) | Medium (rewrite projections) |

---

## 6. Why Option A Wins

Option A is **the architecture the codebase is already converging on.** It is what the source contract says, what the most recent commit says, what the rollout report validated, and what the design documents describe. It does not require any new install. It respects every governance rule. Each IDE retains its native LLM API; memory is shared via MCP. Failure modes are per-MCP, not whole-host. The "unified memory catalog" path (migrations 0001-0005) is already authored and staged, so Option A evolves naturally toward better cross-backend discovery without architectural churn.

Options B and C were considered seriously and rejected with specific evidence. Option B would re-introduce the "universal gateway at `localhost:3000`" failure that this report series already rejected. Option C would discard validated SwarmRecall work and lose full-text recall + RAG substrate.

---

## 7. Risks for Option A (carried forward)

| Risk | Mitigation |
|------|------------|
| SwarmVault `query` slow | Tune `-QueryTimeoutSeconds`; reduce scope; future native-first query rework |
| PostgreSQL cold-start latency | Pre-warm in user logon script; document expected cold-start time |
| 6 uncommitted source edits on `agentcore-control-plane` | Operator commits or rolls back before next rollout phase |
| Open Interpreter inline API key | Migrate to env var per cleanup prompt |
| SwarmRecall broad MCP rollout forbidden | Stays at "governed wrapper only" — never emit `swarmrecall_direct_mcp` to non-Codex |
| Lossless Claw unbounded growth | Add rotation/compaction policy (deferred work) |
| Codex logs DB 1.4 GB and growing | Add rotation policy (deferred work) |
| Pre-wired vector store overlap (`F:\VectorDB\pgvector\`) | Document; do not use as live path |

---

## 8. Conclusion

**Option A** — SwarmRecall canonical spine with native-first governance — is the recommended architecture. Options B and C are documented but rejected with evidence. The next deliverable formalizes the recommendation and the implementation sequence.