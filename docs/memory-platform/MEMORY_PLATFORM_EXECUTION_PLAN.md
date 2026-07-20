# Memory Platform Execution Plan — Locked Milestones

**Authority level:** 5 (see `DOC_AUTHORITY.md`). Detailed Milestone execution guidance; derives from `BLUEPRINT.md` (level 3). Where they conflict, BLUEPRINT.md wins.
**Status:** locked (operator-approved 2026-07-14). Lock source: `BLUEPRINT.md` §8 (locked Milestones). Also: `MILESTONES.md` (root, verbatim evidence).
**Prerequisite reads:** `PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → `BLUEPRINT.md` → `CONTEXT_BLOCK.md` → this file.
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

Durable virtual context has no normal token-count retention ceiling. One million tokens is a
supported active-context profile, not a storage maximum. The selected client/model hard limit
controls only one request; complete history remains recoverable through stable bounded pages and
exact source expansion. A bad summary is superseded and rebuilt from originals without mutating or
deleting the bad version or its source evidence.

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

**Exit criteria (locked — from BLUEPRINT.md §8 M0):**
- One authoritative read order.
- Stale Swarm-first, old database, old storage, and direct-MCP instructions neutralized.
- Current machine authority referenced.
- `BLUEPRINT.md` classified as current in DOC_AUTHORITY.md.
- New Project, Milestone, Macro/Micro, checklist, Context Fabric, Arabold, and tool-audit policies established.
- Per-IDE global-rule profiles generated from one canonical semantic policy.
- Memory implementation handoff identifies the exact branch, commit, worktree, and authority read list.
- No live memory/database build occurs during M0.

**Acceptance tests:** repo validators pass (`scripts/bifrost/validate_contracts.py`, `scripts/bifrost/test_contracts.py`, `validators/validate-control-plane.ps1 -DryRun`); `BLUEPRINT.md` appears in DOC_AUTHORITY.md under Authoritative — stable; no current-classified document teaches Swarm-first memory, direct IDE SQL, or `global-memory-gateway` as the final identity; `ide-profiles/` exists with editability declared per IDE.

**Rollback point:** commit `65d741f` (inherited-state checkpoint) on `task/authority-reconciliation`.

**Required evidence:** `audits/AUTHORITY_RECONCILIATION_MATRIX_2026-07-14.md`, `audits/VALIDATION_REPORT_2026-07-14.md`, the pushed task branch (HEAD `935b273` + BLUEPRINT.md install commit).

**Dependencies:** none. **Satisfied by the authority-reconciliation task (this commit).**

---

## M1 — Storage and PostgreSQL 18 Safety Foundation

**Purpose (locked):** Correct storage foundations and a recoverable PostgreSQL 18 + pgvector platform exist beside the preserved prior cluster. (Source: `BLUEPRINT.md` §8 M1)

**Exit criteria (locked — from BLUEPRINT.md §8 M1):**
- E:, F:, H:, and I: allocation units verified.
- Any mismatched target is safely corrected with backup, hash verification, restore, and service validation.
- Existing PostgreSQL cluster and roles inventoried.
- Logical and physical backups created.
- At least one isolated restore test passes.
- PostgreSQL 18 and compatible pgvector run on F:.
- Required databases and least-privilege service roles exist.
- Old PostgreSQL cluster remains preserved and recoverable.
- Rollback is proven.
- No durable database, WAL, checkpoint, queue, or lock workload is placed on I: or E:.

**Live storage state (2026-07-14 evidence):**
- E:, F:, H: already 65536-byte (64KB) allocation units — verified, no correction needed
- I: has 512-byte allocation units, is **empty** — correction to NTFS/64KB is authorized and safe
- F: PG16 cluster stopped (155,432 not listening); 3722 GB free beside ~3.4 GB used content

**Acceptance tests:** I: formatted and service health verified; restore a logical backup into a disposable database and verify row counts/hashes; PG18 service starts under native Windows lifecycle ownership; `CREATE EXTENSION vector` succeeds; role matrix (`agentcore_read/ingest/worker/admin/backup/cognee`) verified with negative permission tests; old PG16 cluster still starts; no workload on I: or E:.

**Rollback point:** pre-format manifests/backups and PG16 cluster untouched at `F:\AgentCore\database_cluster`. PG18 uses a **new data directory** on F:; never point PG18 at the PG16 data directory.

**Required evidence:** allocation-unit verification report, I: format manifest with hash (empty — no data to preserve), backup manifests with hashes, restore-test transcript, service configuration, role grants dump (no credentials).

**Dependencies:** M0.

**Macro guidance (refined from live evidence — see M1 execution plan below):**
1. Verify and record allocation units for all four drives (E:, F:, H:, I:) — three already correct, I: needs correction
2. Quick-format I: to NTFS/64KB (I: confirmed empty; no data at risk; physical disk identity verified first per BLUEPRINT §4)
3. Bring PG16 online and inventory databases/roles/schemas
4. Logical backup (`pg_dump`) via existing `ops/Backup-AgentCorePostgres.ps1` to E: and G:
5. Physical backup (`pg_basebackup`) to E:\AgentCoreArchive
6. Restore test into isolated disposable instance
7. Download and install PG18 to new directory on F: (e.g., `F:\PostgreSQL18`) — port 55433 during parallel operation
8. Build/install pgvector for PG18 — exact version via Arabold at execution time
9. Create `agent_core` (new), `cognee_core` databases; create roles with least-privilege grants
10. Prove rollback: PG16 still starts; PG18 service can be removed without affecting PG16

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

**Acceptance tests:** duplicate event submission produces one row; UPDATE/DELETE on evidence rows fails for non-admin roles; cross-project write attempt fails at the PostgreSQL schema/write boundary (RLS and/or governed `SECURITY DEFINER` functions, not merely in the future gateway); payload >N KB is stored by content hash on H: spool and retrievable; identity joins resolve for every event; queue, claim, lease, and dead-letter primitives survive a controlled PostgreSQL 18 restart with no lost, duplicated, or permanently stuck work.

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
- Model-aware profiles cover small, standard, large, one-million, and future above-one-million
  context limits without lowering an IDE model's configured hard limit.
- Current-state, Milestone, session, time-range, decision, failure/fix, and complete chronology
  recovery return stable pagination, hashes, trust, omitted counts, and exact expansion references.
- Incorrect summaries are superseded by corrected versions rebuilt from retained originals.

**Acceptance tests:** kill the compaction worker mid-run and verify no loss/corruption on restart; archive a payload to E: and expand it from a summary; regenerate STATE files twice and diff for determinism; verify a verbatim original behind every summary node; secrets-redaction test before durable write; retain a synthetic history above one million tokens and prove count/hash completeness; page the complete chronology; supersede an incorrect summary from originals; recover after model/IDE/service context loss; validate one-million and above-one-million profiles; verify backup/restore/PITR preserves the event/source/summary graph.

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

**Dependencies:** M2 (identity), M4 (gateway). **This Milestone implements the runtime Progressive Tool Disclosure / Milestone-Gated Capability Leases defined in `docs/agent-policy/TOOL_LIFECYCLE_POLICY.md`.**

**Implementation status (2026-07-20):** M6 leases + Bifrost JIT VK bridge are live for OpenRouter named groups (`docs/operations/OPENROUTER_MCP.md`, `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`). `TOOL_MANIFEST.yaml` still records per-project desired state. Some non-OpenRouter registry `permitted_tools: ["*"]` wildcards remain transitional until named inventories replace them.

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
