# FINAL_RECOMMENDATION — CHAOSCENTRAL

**Generated:** 2026-07-03
**Decision:** **Option A — SwarmRecall canonical spine, native-first.**
**Confidence:** **High** (matches source contract, most recent commit, rollout report, and design documents).
**Implementation prompt:** see `IMPLEMENTATION_SEQUENCE_AFTER_APPROVAL.md` — labeled **DO NOT RUN UNTIL USER APPROVES**.

---

## 1. The Fact-Based Answer

CHAOSCENTRAL already has a working native-first memory architecture. It does not need to be invented; it needs to be **committed, cleaned up, and brought online deterministically**.

The hard evidence:

1. **PostgreSQL 16.6 + pgvector 0.8.2** is installed natively at `F:\AgentCore\database_cluster\` with `agent_core` (governed memory) and `swarmrecall` (SwarmRecall runtime) databases. Schema applied. Cold-start contract exists (`\AgentCore\PostgresRuntime`).
2. **Meilisearch** is running natively at `127.0.0.1:7700` from `F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe`. Single instance, no master key in args.
3. **SwarmRecall API** source is at `D:\github\vendor\swarm\swarmrecall`. Runtime config exists. The API process is cold-started by `\AgentCore\SwarmRecallApi` task. Cold at audit moment; ready to start.
4. **SwarmVault** is healthy — 5 managed sources, 2465 raw sources, 7071 pages, 22 MB raw, 20545 nodes. Native CLI build present at `D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js`.
5. **All IDEs/agents** have a renderer file, a profile directory, and (except Android Studio) a cleanup prompt in `D:\github\agentcore-control-plane\docs\prompts\`.
6. **The contract is current.** `master-mcp-server-config.json` v2026-06-26 and the latest commit (`Native-first memory: retire global-memory-gateway from baseline`) explicitly move *away* from a single gateway and toward SwarmRecall + SwarmVault as the canonical surfaces.
7. **The rollout is PARTIAL-GREEN** — source state is green, validator-green, and matches the design. The remaining work is gated on operator actions (commit source, apply migrations, rotate secrets, run cleanup prompts), not new architecture.

The non-evidence — the assumptions that *don't* hold:

1. **There is no OpenAI-compatible gateway at `127.0.0.1:3000`** (or anywhere else on this host). The previous planning assumption is rejected on every measurable dimension. See `UNIVERSAL_GATEWAY_VERIFICATION.md`.
2. **OpenClaw does not host an OpenAI-compatible proxy.** OpenClaw gateway binds to `18789` and exposes its own control UI API, not OpenAI-compatible routes.
3. **Lossless Claw is local file-based memory**, not an HTTP service. It cannot route IDE traffic.
4. **E: is 932 GB SanDisk SSD**, not 10 TB HDD as some older planning docs assumed.
5. **`global-memory-gateway` has been retired from the baseline** — even though the older docs reference it, the current contract routes normal durable writes through SwarmRecall, not through the gateway.

---

## 2. The Recommended Architecture (Option A)

### 2.1 One-Line Description

> **SwarmRecall is the canonical durable memory plane for every IDE/agent; each IDE connects via a governed stdio MCP wrapper; native LLM APIs are unchanged; PostgreSQL/pgvector is the structured spine; SwarmVault is the local RAG/wiki substrate; LCM and Obsidian stay in their narrow roles; no single routing gateway; automatic startup retrieval is per-IDE.**

### 2.2 Per-Plane Role

| Plane | Role | Where | Write rule |
|-------|------|-------|-----------|
| Working context | Session-only | In-process | n/a |
| Canonical structured memory | Source of truth for cross-project facts | PostgreSQL `agent_core` | `agent_ingest` role only |
| Vector catalog | Embeddings + similarity search | pgvector `global_vector_memory_store` (1536-d HNSW cosine) | via projector |
| Semantic recall | Episode retrieval | SwarmRecall (API + Meilisearch + `swarmrecall` DB) | normal agents via MCP |
| Local RAG | Wiki + graph + context packs | SwarmVault file system | projector curated only |
| Human notes | Long-form handoffs | Obsidian vault on D: | via `obsidian-vault` MCP REST |
| Native IDE memory | Per-IDE lossless | Codex plugin, OpenClaw LCM, etc. | IDE-native only |
| Unified memory catalog | Future cross-backend index | (target: `agent_core` new tables) | (deferred until migration apply) |

### 2.3 Per-IDE Connection

| IDE | Native LLM API | Memory MCP | Long-form MCP |
|-----|----------------|------------|---------------|
| Codex | `https://api.openai.com` (default) | SwarmRecall + SwarmVault | — |
| Cursor | `https://api.cursor.com` | SwarmRecall + SwarmVault | obsidian-vault (planned) |
| OpenClaw | OpenClaw gateway `:18789` (control UI only) | SwarmRecall + SwarmVault | obsidian-vault |
| Open Interpreter | OpenRouter | SwarmRecall + SwarmVault | — |
| MiniMax Code | `https://agent.minimax.io/mavis/api/v1/llm/v1` | SwarmRecall + SwarmVault | obsidian-vault |
| Mavis | (same as MiniMax) | (deferred renderer) | — |
| Antigravity IDE | (per IDE) | SwarmRecall + SwarmVault | obsidian-vault |
| Claude Code | Anthropic API | SwarmRecall + SwarmVault (staged) | — |
| Claude Desktop + Obsidian | Anthropic API | — | obsidian-vault (planned) |
| Android Studio | (inherits MiniMax) | (inherits MiniMax) | — |

Every IDE retains its native LLM API. There is **no proxy**. Memory is shared via stdio MCP, governed wrappers only.

### 2.4 Cold-Start Contract

Deterministic chain at user logon:

1. `\AgentCore\PostgresRuntime` Task Scheduler task runs `Start-AgentCorePostgres.ps1 -StartIfStopped` → PostgreSQL on `:55432`.
2. `\AgentCore\SwarmRecallMeilisearch` runs `Start-AgentCoreSwarmRecallMeilisearch.ps1` → Meilisearch on `:7700`.
3. `\AgentCore\SwarmRecallApi` runs `Start-AgentCoreSwarmRecallApi.ps1` → SwarmRecall API on `:3300`.
4. Each IDE cold-start reads `mcp.json`, launches SwarmRecall + SwarmVault stdio MCP subprocesses via the governed wrappers.
5. First MCP `initialize` triggers `memory_search` against `associated_project_path` of the active workspace → automatic startup retrieval.

Failure modes are **per-MCP**, not whole-host. If Meilisearch is slow, SwarmRecall falls back to the `swarmrecall` DB. If SwarmVault is slow, the agent continues without context packs. If PostgreSQL is down, the projector is delayed but SwarmRecall + SwarmVault continue to serve cached state.

### 2.5 Lossless Storage Strategy

- **Codex native plugin** (`codex-lossless-memory-pack@personal`) keeps full session memory in `~/.codex\memories_1.sqlite` + Markdown pack. Untouched.
- **OpenClaw LCM/QMD** keeps OpenClaw-local lossless in `~/.openclaw\lossless-claw\` + `~/.openclaw\agents\main\qmd\xdg-cache\qmd\index.sqlite`. Untouched, narrow scope.
- **SwarmRecall** is the canonical cross-project durable plane; PG base backup + WAL archive on E: per existing contract.
- **SwarmVault** is file-based; backed up via `robocopy /MIR` to E: (script not yet written — add as Phase 2 task).
- **Codex logs DB** (`logs_2.sqlite`, currently 1.4 GB) — add rotation policy as Phase 2 task.

### 2.6 Rolling Summaries + Semantic Memory

- Hourly: `Invoke-AgentCoreMemoryProjector.ps1` re-embeds new/changed messages and projects them into SwarmRecall + curated SwarmVault subset.
- Daily: `summarize_old_messages` maintenance task collapses old `messages` rows into `agent_cross_project_telemetry` summaries (existing scheduled maintenance; preserve).
- Embeddings: `OPENAI_API_KEY` env var → `text-embedding-3-small` (preferred, 1536-d, matches pgvector schema). Fallback: `local_hash_v1`.

### 2.7 RAG / Context Packs

- SwarmVault context packs: `Invoke-AgentCoreSwarmVault.ps1 -Mode ContextPack -Query <q> -WorkspacePath <p>` returns a bounded pack of wiki + graph nodes + raw pages for the workspace.
- Codex memory pack: native plugin produces per-session packs.
- LCM context: OpenClaw-local QMD lookup.
- Per-agent assembly rule (from `memory_system.md` §"Context Assembly"):
  1. Task-local files.
  2. SwarmRecall for compact cross-project facts.
  3. Obsidian for long-form handoffs.
  4. QMD/LCM for local context.

### 2.8 pgvector Catalog / Pointers

- pgvector `global_vector_memory_store` holds embeddings of `messages` + `project_facts`.
- HNSW index, cosine distance, 1536-d.
- Each row carries `source_kind`, `document_source`, `associated_project_path`, `agent_id`, `run_id`.
- Future `memory_catalog` (migrations 0001-0005) adds cross-backend pointers; **apply is blocked** behind §13/§18 gates in `database-plan.md`. Option A does not require this for the current task.

### 2.9 Automatic Startup Retrieval

- Codex: `Stop` hook calls `codex-stop-audit.ps1`; on next start, native plugin reads memory pack + first MCP `initialize` reads SwarmRecall context pack for active workspace.
- Cursor / OpenClaw / OI / MiniMax / Antigravity: first MCP `initialize` triggers `memory_search` for the active workspace path.
- Claude Code: staged config does the same once the cleanup prompt is run.
- Per-workspace caching: SwarmRecall `agent_cross_project_telemetry` keeps the last-known context per workspace; first cold-start uses cached, then live.

---

## 3. Why Not Options B or C

### 3.1 Option B (universal local broker at 18789 or new port) — REJECTED

- Contradicts the source contract and the most recent commit.
- Re-creates the exact failure this report series already rejected (universal gateway at `localhost:3000`).
- Lossless Claw is file-based; bridging it to HTTP is a new code path that does not exist.
- Conflates memory routing with LLM proxying — two different governance problems.
- Per-IDE failure isolation is lost.
- Reintroduces `global-memory-gateway`, which the codebase explicitly retired.

### 3.2 Option C (PostgreSQL-only, all writes to PG) — REJECTED

- Contradicts `database-plan.md` §2 (no LCM as active backend — but more importantly, no single-DB thinking).
- Discards validated SwarmRecall work (53 MCP tools, native-green).
- Loses full-text recall (BM25 + faceting via Meilisearch).
- Loses RAG/wiki substrate (SwarmVault file-based state).
- Lossy vs. lossless roles collapse.
- pgvector would balloon if it had to absorb every long-form note.

---

## 4. The Three Ranked Options

| Rank | Option | Confidence | Effort | Risk |
|------|--------|-----------|--------|------|
| **1** | A — SwarmRecall canonical spine, native-first | **High** | None (baseline already green) | Low |
| 2 | B — Universal local broker | Low | High | High |
| 3 | C — Postgres-only | Low | Medium | High |

---

## 5. Required Pre-Flight Remediations

These must happen before Option A is "shipped," even though no new architecture is required.

### 5.1 Secret Remediations (security gates)

| Location | Action |
|----------|--------|
| `C:\Users\ynotf\.openinterpreter\config.toml` | Remove inline OpenRouter key; migrate to `OPENROUTER_API_KEY` env var |
| `C:\Users\ynotf\.openclaw\openclaw.json` | Rotate OpenClaw gateway token (rotation gate per rollout report) |
| `C:\Users\ynotf\.codex\config.toml` | Rotate `experimental_bearer_token` (rotation gate) |
| `C:\Users\ynotf\.claude.json` | Rotate `apiKey` and `CONTEXT7_API_KEY` (rotation gates) |

### 5.2 Source Repo Remediations

| Repo | Action |
|------|--------|
| `D:\github\agentcore-control-plane` | Commit the 6 uncommitted source edits (or roll back) — see rollout §6 commit gate |
| `D:\github\agent-team` | Commit the 20 dirty entries; risk of accidental loss |
| `D:\github\autonomous-agent-team` | Reattach to a branch; commit the 22 dirty entries; configure remotes |

### 5.3 Cleanup-Prompt Operator Runs

Run each `docs\prompts\*-cleanup-prompt.md` inside its own IDE per rollout §6 "Live IDE config edits" gate. Highest priority: `claude-code-cleanup-prompt.md`.

### 5.4 DB Migration Apply (deferred)

`migrations\0001`–`0005` remain blocked per `database-plan.md` §13/§18. Do not apply without operator sign-off.

---

## 6. Operational Risks Going Forward

| Risk | Mitigation |
|------|------------|
| SwarmVault `query` slow over 7071 pages | Tune `-QueryTimeoutSeconds`; reduce scope; future native-first query rework |
| PostgreSQL cold-start latency | Pre-warm in user logon; document expected cold-start time |
| Codex logs DB growing unbounded | Add rotation policy (Phase 2 deferred work) |
| Lossless Claw unbounded growth | Add compaction policy (Phase 2 deferred work) |
| Single-instance Meilisearch | No mitigation needed; matches design |
| `F:\VectorDB\pgvector\` naming overlap | Document; do not use as live path |
| 932 GB E: for cold retention | Add off-host mirror to G: |
| Renderer/registry drift | Re-run `validators\validate-control-plane.ps1 -DryRun` after each cleanup-prompt operator run |

---

## 7. Success Criteria

The architecture is "shipped" when:

1. All 9 IDEs/agents (Codex, Cursor, OpenClaw, OI, MiniMax, Mavis, Antigravity, Claude Code, Claude Desktop + Obsidian) have a live MCP wiring that matches their renderer contract.
2. Cold-start chain (PG → Meilisearch → SwarmRecall API → IDE MCP) completes within 60 seconds at user logon.
3. Every IDE's first MCP `initialize` returns a non-empty context pack for the active workspace path (when one exists).
4. The hourly projector runs green (`Invoke-AgentCoreMemoryProjector.ps1` exit 0).
5. `validate-control-plane.ps1 -DryRun` returns `Overall: PASS`.
6. No inline secrets remain in any IDE config file (Windows env vars only).
7. The 6 uncommitted source edits on `agentcore-control-plane` are committed (or rolled back) and the rollout PARTIAL-GREEN moves to GREEN.
8. Backup/restore drill: `Backup-AgentCorePostgres.ps1` produces a base backup on E:; a restore drill on a scratch cluster succeeds.

---

## 8. Bottom Line

**Option A is the architecture the codebase has already converged on.** The audit found no need for new components, no need for a universal gateway, and no need to collapse planes. Every claim in this recommendation is supported by prior deliverables in this directory plus the source contract and the rollout report. The work to ship is **operator work** (commit, rotate, run cleanup prompts, validate), not architectural redesign.

The implementation sequence in `IMPLEMENTATION_SEQUENCE_AFTER_APPROVAL.md` lays out the exact steps. **Do not run those steps until the user approves this recommendation.**