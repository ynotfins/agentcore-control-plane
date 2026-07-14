# Memory Platform Execution Plan — Locked Milestones

**Authority level:** 4 (see `DOC_AUTHORITY.md`). Implementation authority for the AgentCore memory/context/database build.
**Status:** locked (operator-approved 2026-07-14). Source: operator-authored `MILESTONES.md` (root, preserved as evidence).
**Prerequisite reads:** `PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → `CONTEXT_BLOCK.md` → this file.
**Handoff:** `docs/handoffs/MEMORY_PLATFORM_IMPLEMENTATION_HANDOFF_2026-07-14.md`

---

## 1. Locked architecture

These decisions are operator-approved and may not be changed without explicit operator approval:

- **PostgreSQL 18 + pgvector** is the canonical non-Swarm authority for identity, evidence, policy, queue, claim, lease, and workflow state.
- **AgentCore itself** owns immutable evidence, rolling context, compaction, exact source expansion, project state, and generated STATE.md projections.
- **Cognee** is the selected curated semantic/knowledge-graph subsystem behind an AgentCore adapter (`KnowledgeMemoryPort`). **Mem0 is rejected for v1 and must not be installed.**
- **Bifrost** retains the stable IDE-facing `agentcore-gateway` (`http://127.0.0.1:8080/mcp`).
- The memory subsystem retains the stable Bifrost upstream identity **`agentcore-memory`**. No IDE configuration change is required at any Milestone.
- **Swarm remains independent.** SwarmRecall/SwarmVault/SwarmClaw are never a dependency of this platform.
- **No Docker or WSL dependency** for the core platform.
- **No Redis, Memurai, Qdrant, LanceDB, Neo4j, or any second canonical memory store.** A separate engine requires a benchmark proving a distinct requirement that PostgreSQL FTS, pgvector, and Cognee cannot satisfy.
- `database-plan.md` and `AGENT_DATABASE_BOOTSTRAP.md` are historical evidence; do not implement their schemas, tool names, or Swarm memory planes.
- `D:\github\memory-context-database` is supporting corpus/template planning, not the controlling architecture.

## 2. Lossless requirement (binding definition)

"Lossless" means all of the following, testably:

1. Original prompts, messages, tool events, decisions, outputs, and accepted evidence are durably preserved **before** compaction.
2. Originals are never replaced by summaries.
3. Hierarchical summaries retain exact source edges.
4. Any summary or fact can expand back to exact original evidence.
5. Old payloads may move from H: to E: without breaking retrieval.
6. Active model context is token-budgeted; durable virtual context is effectively unbounded.
7. Compaction is deterministic, versioned, idempotent, and restart-safe.
8. Secrets are redacted before durable storage.
9. Trust and provenance follow every event, fact, summary, and retrieval.

## 3. State model (generated projections)

PostgreSQL is canonical. A projection worker writes these files atomically (temp file + rename); agents contribute **only** through `agentcore-memory` and never directly edit shared STATE files:

```text
C:\Users\ynotf\.agentcore\GLOBAL_STATE.md
<project>\.agentcore\STATE.md
<project>\.agentcore\DECISIONS.md
<project>\.agentcore\CONTEXT_INDEX.md
```

## 4. Milestone governance

**Locked (operator approval required to change):** Milestone purposes, exit criteria, ordering, core architecture, storage ownership, the Cognee decision, the Bifrost identity, and the lossless guarantees.

**Flexible (implementation guidance):** Macro and Micro steps. The execution agent may add, remove, split, and reorder steps inside a Milestone, choose better APIs or package structures, and adapt tests and tooling — as long as the Milestone outcome, exit criteria, boundaries, and acceptance guarantees are preserved.

**Refinement protocol:** Do not pre-generate speculative Micro steps for distant Milestones. Immediately before starting each Milestone, the execution agent must refine that Milestone's Macro/Micro checklists using: current repository state, Context Fabric capture/drift, Arabold exact-version documentation, Serena, Depwire, Tentra, and machine evidence (`D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md`). Milestone entry and exit follow `docs/agent-policy/MILESTONE_EXECUTION_STANDARD.md`.

---

## M0 — Authority and Execution Foundation

**Purpose (locked):** Every agent sees one accurate architecture and execution policy.

**Exit criteria (locked):**
- One authoritative read order.
- Stale Swarm-first and old database instructions neutralized.
- Current machine authority referenced.
- Per-IDE global-rule profiles created.
- New Project, Milestone, Macro/Micro, checklist, Context Fabric, Arabold, and tool-audit policies established.
- This exact memory-platform Milestone plan is the execution authority.
- No live memory/database implementation begins in M0.

**Acceptance tests:** repo validators pass (`scripts/bifrost/validate_contracts.py`, `scripts/bifrost/test_contracts.py`, `validators/validate-control-plane.ps1 -DryRun`); no current-classified document teaches Swarm-first memory, direct IDE SQL, or `global-memory-gateway` as the final identity; `ide-profiles/` exists with editability declared per IDE.

**Rollback point:** commit `65d741f` (inherited-state checkpoint) on `task/authority-reconciliation`.

**Required evidence:** `audits/AUTHORITY_RECONCILIATION_MATRIX_2026-07-14.md`, `audits/VALIDATION_REPORT_2026-07-14.md`, the pushed task branch.

**Dependencies:** none. **Satisfied by the authority-reconciliation task (this task).**

---

## M1 — PostgreSQL 18 Safety Foundation

**Purpose (locked):** A recoverable PostgreSQL 18 + pgvector platform exists beside the preserved old cluster.

**Exit criteria (locked):**
- Existing cluster inventory completed.
- Logical and physical backups created.
- At least one restore test passes.
- PostgreSQL 18 and compatible pgvector run on F:.
- Required databases and least-privilege service roles exist.
- Old PostgreSQL installation remains recoverable.
- Rollback is proven.

**Acceptance tests:** restore a logical backup into a disposable database and verify row counts/hashes; PG18 service starts under native Windows lifecycle ownership; `CREATE EXTENSION vector` succeeds; role matrix (`agentcore_read/ingest/worker/admin/backup/cognee`) verified with negative permission tests; old PG16 cluster still starts.

**Rollback point:** PG16 cluster untouched at `F:\AgentCore\database_cluster` (port 55432) + verified backups on E: and G:. PG18 uses a **new data directory**; never point PG18 at the PG16 data directory.

**Required evidence:** backup manifests with hashes, restore-test transcript, service configuration, role grants dump (no credentials).

**Dependencies:** M0.

**Macro guidance:** inventory → backup → restore-test → install PG18 side-by-side on F: → build/install pgvector for PG18 → create `agent_core` (new) and roles → prove rollback. Exact PG18 minor version and pgvector build verified via Arabold at execution time (CONTEXT_BLOCK baseline: PG 18.4, pgvector 0.8.5).

---

## M2 — Canonical Identity and Immutable Evidence

**Purpose (locked):** Every durable operation has an identity and every accepted event is preserved.

**Exit criteria (locked):**
- Machine, user, project, repo, worktree, IDE/client, agent, session, run, and LangGraph thread identities are separate.
- Append-only evidence ledger works.
- Idempotent event writes work.
- Large payloads are externalized by content hash.
- Project A cannot write Project B.
- Normal IDE agents have no database credentials.
- Raw evidence cannot be updated or deleted by normal service roles.

**Acceptance tests:** duplicate event submission produces one row; UPDATE/DELETE on evidence rows fails for non-admin roles; cross-project write attempt fails; payload >N KB stored by content hash on H: spool and retrievable; identity joins resolve for every event.

**Rollback point:** M1 baseline backup; identity/evidence schema applied via versioned, reversible migrations.

**Required evidence:** migration files, permission-denial test transcripts, idempotency test results.

**Dependencies:** M1.

---

## M3 — Lossless Context and STATE Projections

**Purpose (locked):** Long sessions compact without losing recoverability.

**Exit criteria (locked):**
- L0 recent raw context.
- L1 event-span summaries.
- L2 session summaries.
- L3 project chronology.
- Exact source links from all summaries.
- Original long prompts preserved verbatim.
- Exact expansion works after compaction.
- Exact expansion works after archival to E:.
- GLOBAL_STATE.md and project STATE.md regenerate deterministically.
- Process interruption during compaction causes no loss or corruption.

**Acceptance tests:** kill the compaction worker mid-run and verify no loss/corruption on restart; archive a payload to E: and expand it from a summary; regenerate STATE files twice and diff for determinism; verify a verbatim original behind every summary node; secrets-redaction test before durable write.

**Rollback point:** M2 schema + backups; compaction is versioned so any compaction generation can be recomputed from originals.

**Required evidence:** interruption-test transcript, expansion-after-archival transcript, deterministic regeneration diff, redaction test results.

**Dependencies:** M2.

---

## M4 — AgentCore Memory Gateway

**Purpose (locked):** All non-Swarm IDEs use the completed memory system through the existing Bifrost connection.

**Required compact tool surface (locked):**
`memory_status`, `startup_context`, `retrieve_context`, `append_event`, `propose_fact`, `expand_source`, `session_open`, `session_close`, `build_handoff`, `docs_search`

**Exit criteria (locked):**
- Existing `agentcore-memory` Bifrost identity is preserved.
- No IDE configuration change is required.
- Multiple IDEs can use separate sessions safely.
- Append → retrieve → compact → expand works end to end.
- Degraded components are reported clearly.
- No raw database/admin tools are exposed.

**Acceptance tests:** Cursor and one other IDE run concurrent sessions without interference; end-to-end append/retrieve/compact/expand through the gateway; `memory_status` reports component degradation truthfully (e.g., Cognee stopped); registry `permitted_tools` for `agentcore-memory` lists exactly the compact surface (wildcard removed for this server); Bifrost tools-list refresh shows the new tools without IDE edits.

**Rollback point:** previous `scripts/agentcore_memory/server.py` (health/status only) restorable via registry re-render + gateway restart through the scheduled-task owner.

**Required evidence:** multi-IDE session transcript, end-to-end test transcript, sanitized tools-list dump.

**Dependencies:** M3.

---

## M5 — Hybrid Retrieval and Curated Cognee Memory

**Purpose (locked):** Relevant facts and knowledge are retrieved efficiently without creating a second source of truth.

**Exit criteria (locked):**
- PostgreSQL full-text search and trigram search work.
- Selective pgvector search works.
- Official documents live on E: and indexes live on F:.
- Cognee runs natively behind KnowledgeMemoryPort.
- Cognee uses its own `cognee_core` database on the PostgreSQL 18 service.
- Only promoted knowledge enters Cognee.
- Raw transcripts and entire repositories do not enter Cognee.
- Cognee failure does not break evidence, summaries, exact expansion, or STATE generation.
- Mem0 is not installed.

**Acceptance tests:** hybrid retrieval quality checks on seeded fixtures; stop Cognee and verify evidence/summaries/expansion/STATE all still work; promotion-gate test (raw transcript rejected, curated fact accepted); confirm no Mem0 package/service exists; confirm Cognee runs without Docker/WSL.

**Rollback point:** Cognee is additive — disable `KnowledgeMemoryPort` adapter; core platform unaffected.

**Required evidence:** retrieval benchmark notes, Cognee-failure degradation transcript, dependency inventory showing no Mem0.

**Dependencies:** M4 (may overlap M4 finalization where safe).

---

## M6 — Durable LangGraph Autonomous Workflow

**Purpose (locked):** The autonomous developer workflow resumes safely and verifies its work.

**Exit criteria (locked):**
- PostgreSQL-backed LangGraph checkpoints.
- Resume after process restart.
- Milestone state and checklist state persist.
- Requirement/scope/architecture drift gates.
- Critic, deterministic scorer, and independent judge.
- A/B implementation only when risk justifies it.
- Human pause/resume for genuine operator decisions.
- Progressive tool disclosure and JIT leases backed by PostgreSQL.
- Concurrent projects cannot change each other's tools or state.

**Acceptance tests:** kill and resume a workflow mid-Milestone; lease a tool for a Micro step, verify expiry on step completion/timeout/session close; two concurrent projects verify tool-set isolation (per-project capability state, no shared-VK mutation side effects); high-risk activation requires operator approval; drift gate blocks scope change without approval.

**Rollback point:** workflow engine is additive; disable the LangGraph service; M4 gateway continues to function.

**Required evidence:** resume transcript, lease lifecycle audit rows, concurrency isolation test, approval-gate test.

**Dependencies:** M2 (identity), M4 (gateway). **This Milestone implements the runtime Progressive Tool Disclosure / Milestone-Gated Capability Leases defined in `docs/agent-policy/TOOL_LIFECYCLE_POLICY.md`.** Until M6 passes, `TOOL_MANIFEST.yaml` files record policy and desired state only, and registry wildcard grants remain classified transitional.

---

## M7 — Engineering Knowledge and Templates

**Purpose (locked):** Agents have trusted examples and predictable implementation standards.

**Exit criteria (locked):**
- Engineering Constitution.
- Approved dependency catalog.
- Recipes and focused reference implementations.
- Official-source provenance.
- First two Copier templates pass admission: `mcp-server-python`, `agent-langgraph-postgres-checkpointer`.
- No random codebase dump.
- No whole-repository embedding requirement.

**Acceptance tests:** both templates generate, build, and pass their own tests in a clean directory; every catalog entry carries official-source provenance; admission gate rejects an unpinned/unprovenanced candidate.

**Rollback point:** knowledge library is additive content on E:/F:; removable without platform impact.

**Required evidence:** template generation transcripts, admission-gate results, catalog with provenance.

**Dependencies:** M5 (retrieval), M6 (workflow) for full value; content work may start earlier. Corpus layout input: `D:\github\memory-context-database\DOCS_PLAN.md` (supporting evidence only).

---

## M8 — Operations, Recovery, Performance, and Cutover

**Purpose (locked):** The platform operates reliably without expert intervention.

**Exit criteria (locked):**
- Native Windows lifecycle ownership.
- Backup to E: and second copy to G:.
- Restore tests pass.
- PostgreSQL, memory service, Bifrost, Cognee, and LangGraph restart tests pass.
- Resource limits prevent workstation exhaustion.
- Context assembly and retrieval latency measured.
- Security and secret scans pass.
- Old PostgreSQL remains preserved for rollback.
- Complete acceptance suite passes.
- Swarm remains untouched.

**Acceptance tests:** full restart cycle of every component under scheduled-task/service ownership; restore test from E: and from G:; latency measurements recorded against budgets; secret scan of all configs and evidence; Swarm services verified unmodified; full M1–M8 acceptance suite green.

**Rollback point:** preserved PG16 cluster + M-series backups; documented rollback runbook per component.

**Required evidence:** ops runbooks, restart/restore transcripts, latency report, final acceptance report.

**Dependencies:** M1–M7.

---

## Out of scope for every Milestone

- Modifying Swarm products, OpenClaw, or ClawX.
- Adding a second canonical memory store.
- Installing Mem0.
- Docker/WSL dependency for the core platform.
- Whole-drive filesystem exposure or database credentials in IDE configs.
- Renaming the `agentcore-gateway` or `agentcore-memory` identities.
