# BLUEPRINT.md — AgentCore Global Memory, Context, and Database Platform

> **Status:** Locked implementation blueprint  
> **Repository:** `D:\github\agentcore-control-plane`  
> **Machine:** `CHAOSCENTRAL`  
> **Operator:** Tony Valentine (`ynotf`)  
> **Scope:** Non-Swarm AgentCore platform only  
> **Last updated:** 2026-07-14  
>
> This file is the stable blueprint for the memory/context/database build.  
> It defines the goal, architecture, storage roles, immutable guarantees, and Milestone exit criteria.
>
> Cursor may optimize Macro and Micro steps from repository and machine evidence. Cursor may not change the architecture, Milestone outcomes, Milestone ordering, storage authority, lossless guarantees, Cognee decision, Bifrost identities, or Swarm boundary without explicit operator approval.

---

## 1. Authority and Read Order

Read in this order:

1. `PROJECT_ANCHOR.md` — constitutional boundaries.
2. `DOC_AUTHORITY.md` — authority classification and read order.
3. `BLUEPRINT.md` — locked goal, architecture, and Milestones.
4. `CONTEXT_BLOCK.md` — current mutable implementation state.
5. `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` — detailed execution guidance.
6. Current Bifrost contracts, runbooks, and handoff.
7. `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md` — machine-fact authority.

Historical, Swarm-only, superseded, and compatibility documents do not override this chain.

---

## 2. Final Goal

Build one local, durable, lossless memory and context platform for every non-Swarm IDE and agent on `CHAOSCENTRAL`.

The platform must:

- Preserve original prompts, messages, accepted evidence, tool events, decisions, results, summaries, and state transitions.
- Compact active context without deleting or replacing original evidence.
- Maintain short-term, session, project, and long-term memory.
- Resume after context resets, IDE restarts, process failures, and machine restarts.
- Give each project a current, accurate, generated `STATE.md`.
- Allow all project agents to contribute through governed memory operations.
- Keep PostgreSQL as the canonical authority.
- Use Cognee only for curated semantic and relationship memory.
- Use LangGraph for durable autonomous workflows and checkpoints.
- Expose memory through the existing Bifrost gateway.
- Keep SwarmRecall, SwarmVault, SwarmClaw, OpenClaw, and ClawX independent and untouched.

The platform is for one human operator with large local storage. Durable storage and complete provenance are preferred over aggressive deletion.

---

## 3. Locked Architecture

```text
Non-Swarm IDEs and agents
        |
        v
Bifrost: agentcore-gateway
        |
        v
Bifrost upstream: agentcore-memory
        |
        +-- PostgreSQL 18 + pgvector on F:
        |     - identity
        |     - immutable evidence
        |     - artifacts metadata
        |     - summaries and source edges
        |     - facts and proposals
        |     - project/session state
        |     - capability profiles and leases
        |     - queues, claims, locks, and audit
        |     - LangGraph persistence
        |     - documentation metadata and indexes
        |
        +-- H:
        |     - Bifrost runtime
        |     - hot content-addressed artifacts
        |     - context/compaction scratch
        |     - active models and caches
        |     - service logs
        |
        +-- E:
        |     - cold original evidence
        |     - archived artifacts
        |     - official documentation corpus
        |     - templates and reference implementations
        |     - PostgreSQL backups and WAL archive
        |
        +-- Cognee
        |     - promoted facts
        |     - verified decisions
        |     - reusable patterns
        |     - curated knowledge relationships
        |
        +-- Generated projections
              - C:\Users\ynotf\.agentcore\GLOBAL_STATE.md
              - <project>\.agentcore\STATE.md
              - <project>\.agentcore\DECISIONS.md
              - <project>\.agentcore\CONTEXT_INDEX.md
```

### Canonical authority

- PostgreSQL is canonical.
- Markdown projections are generated, reproducible views.
- Cognee is not canonical.
- No IDE receives raw database credentials.
- No normal agent receives SQL, DDL, database-admin, or Bifrost-admin tools.

### Memory technology decision

- **Use Cognee for v1** behind an AgentCore adapter.
- **Do not install Mem0 for v1.**
- Mem0 may be evaluated later as a benchmark alternative only.
- Neither Cognee nor Mem0 owns the immutable evidence ledger or lossless compaction system.

---

## 4. Machine and Storage Facts

### Workstation

- Intel Core i9-14900KF
- 24 cores / 32 threads
- 128 GB DDR5
- NVIDIA RTX 4070 SUPER with 12 GB VRAM
- Windows 11 Pro
- No Docker or WSL dependency for the core AgentCore platform

### Drive roles

| Drive | Device/role | Locked use |
|---|---|---|
| C: | OS and applications | Windows, user profile, IDE-owned global files; no high-volume database writes |
| D: | Project NVMe | Repositories, worktrees, builds, tests |
| E: | 10 TB HGST HDD | Cold evidence, documentation, archives, backups, WAL archive |
| F: | 4 TB Samsung 990 PRO | PostgreSQL 18, pgvector, hot indexes, canonical database state |
| G: | 4 TB external HDD | Second backup copy |
| H: | 2 TB Crucial P5 Plus NVMe | Bifrost runtime, hot artifacts, models, caches, compaction scratch |
| I: | 1 TB Crucial BX500 SATA SSD | Disposable staging and sequential temporary exports only |
| J: | 1 TB portable exFAT SSD | Portable transfer only |

### Allocation-unit targets

| Drive | Target filesystem/allocation unit | Rule |
|---|---:|---|
| C: | Existing NTFS / 4 KB | Preserve |
| D: | Existing NTFS / 4 KB | Preserve |
| E: | NTFS / 64 KB | Verify; correct only if mismatched |
| F: | NTFS / 64 KB | Verify; correct only if mismatched |
| H: | NTFS / 64 KB | Verify; correct only if mismatched |
| I: | NTFS / 64 KB | Expected to require correction |
| G: | Preserve | Do not format |
| J: | Preserve exFAT | Do not format |

### Storage preparation authorization

Before durable platform installation, Cursor may inspect and correct E:, F:, H:, and I: when their live allocation-unit size does not match the target.

For any drive requiring correction:

1. Identify the physical disk by model, serial/device identity, disk number, volume GUID, and drive letter.
2. Inventory files, services, tasks, open handles, ACLs, and used space.
3. Stop only dependent services.
4. Copy required contents to a verified temporary location.
5. Create a manifest and SHA-256 hashes.
6. Verify the temporary copy.
7. Quick-format the correct volume as GPT/NTFS with 64 KB allocation units.
8. Restore required contents.
9. Verify hashes, permissions, paths, services, and runtime health.
10. Retain rollback evidence until the Milestone passes.

Never format C:, D:, G:, or J:.

Never format by drive letter alone.

H: contains the live Bifrost runtime.  
F: may contain preserved PostgreSQL material.  
Those contents must be backed up and restored or reinstalled deliberately before the build continues.

---

## 5. Lossless Memory Guarantees

“Lossless” means active context may be summarized and compacted, but durable evidence remains recoverable.

Required guarantees:

1. Original prompts, messages, accepted evidence, tool events, decisions, results, and state transitions are persisted before compaction.
2. Originals are never replaced by summaries.
3. Large payloads are externalized into a content-addressed artifact store.
4. Every summary retains exact source edges.
5. Every fact retains provenance and source evidence.
6. Any summary or fact can expand back to exact original evidence.
7. Compaction is deterministic, versioned, idempotent, and restart-safe.
8. Archiving from H: to E: does not break retrieval or expansion.
9. Contradictory facts create proposals/reviews instead of silent overwrites.
10. Trust labels and provenance follow every stored and retrieved item.
11. Secrets are redacted before durable storage.
12. Active model context is token-budgeted; durable virtual history is effectively unbounded.
13. Failed compaction cannot corrupt or delete the last valid context version.
14. Backups are not accepted until a restore test succeeds.

### Context hierarchy

- **L0:** recent accepted raw event tail
- **L1:** coherent event-span summaries
- **L2:** session summaries
- **L3:** project chronology
- **L4:** promoted global facts and reusable knowledge

---

## 6. STATE Model

### Generated files

```text
C:\Users\ynotf\.agentcore\GLOBAL_STATE.md
<project>\.agentcore\STATE.md
<project>\.agentcore\DECISIONS.md
<project>\.agentcore\CONTEXT_INDEX.md
```

### Rules

- PostgreSQL is canonical.
- Agents do not directly edit shared STATE projections.
- Agents contribute events, proposals, decisions, evidence, and status through `agentcore-memory`.
- A projection worker writes files atomically.
- Each projection includes revision, timestamp, source revision, and content hash.
- The previous valid projection remains recoverable.
- Every project agent reads `STATE.md` at startup and before a Milestone transition.
- Every accepted project change updates durable state before the session closes.
- `STATE.md` records current truth, progress, blockers, active Milestone, next actions, and verified decisions—not raw transcripts.

---

## 7. Project Execution Rules

Every managed project uses:

- Project Charter
- Locked Milestones
- Adaptable Macro steps
- Adaptable Micro steps
- Evidence-backed checklists
- Context Fabric checkpoints
- Arabold exact-version documentation
- Serena, Depwire, and Tentra where relevant
- Milestone entry and exit gates
- Tool audits
- Restore points
- Durable handoffs

### Milestones versus steps

Milestones are fixed outcome and acceptance boundaries.

Cursor may optimize Macro and Micro steps using current repository and machine evidence. Cursor may:

- add steps
- remove unnecessary steps
- split or combine steps
- reorder steps inside the current Milestone
- change package layout
- choose better supported APIs
- add required tests
- adapt implementation details

Cursor may not change a Milestone’s purpose, exit criteria, ordering, architecture, or irreversible boundary without explicit operator approval.

Do not pre-plan hundreds of speculative Micro steps. Refine the current Milestone immediately before execution.

---

## 8. Locked Milestones

## M0 — Authority and Execution Foundation

**Outcome:** Every agent sees one accurate architecture and execution policy.

**Exit criteria:**

- One authoritative read order.
- Stale Swarm-first, old database, old storage, and direct-MCP instructions neutralized.
- Current machine authority referenced.
- `BLUEPRINT.md` classified as current.
- New Project, Milestone, Macro/Micro, checklist, Context Fabric, Arabold, and tool-audit policies established.
- Per-IDE global-rule profiles generated from one canonical semantic policy.
- Memory implementation handoff identifies the exact branch, commit, worktree, and authority read list.
- No live memory/database build occurs during M0.

**Rollback point:** inherited-state checkpoint plus logical reconciliation commits.

---

## M1 — Storage and PostgreSQL 18 Safety Foundation

**Outcome:** Correct storage foundations and a recoverable PostgreSQL 18 + pgvector platform exist beside the preserved prior cluster.

**Exit criteria:**

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

**Rollback point:** pre-format manifests/backups and preserved prior PostgreSQL cluster.

---

## M2 — Canonical Identity and Immutable Evidence

**Outcome:** Every durable operation has an identity and every accepted event is preserved.

**Exit criteria:**

- Separate identities for machine, user, project, repository, worktree, IDE/client, agent, session, run, LangGraph thread, and workflow.
- Append-only evidence ledger works.
- Idempotent writes work.
- Large payloads externalize by content hash.
- Project A cannot write Project B.
- Normal IDE agents have no database credentials.
- Raw evidence cannot be updated or deleted by normal service roles.
- Trust, provenance, timestamps, schema version, and source identity are enforced.
- Queue, claim, lease, and dead-letter primitives recover after restart.

**Rollback point:** versioned migration boundary and verified pre-migration backup.

---

## M3 — Lossless Context and STATE Projections

**Outcome:** Long sessions compact without losing recoverability or current project truth.

**Exit criteria:**

- L0/L1/L2/L3 context hierarchy works.
- Original long prompts are preserved verbatim.
- Requirements, constraints, assumptions, acceptance criteria, and unresolved questions link to exact source spans.
- Exact expansion works after compaction.
- Exact expansion works after archival to E:.
- Context assembly obeys model-specific token budgets.
- `GLOBAL_STATE.md` and project `STATE.md` regenerate deterministically.
- Projection writes are atomic and versioned.
- Process interruption during compaction causes no loss or corruption.
- Multi-session project chronology remains coherent.
- Contradictory facts follow a proposal/review path.

**Rollback point:** prior summary/projection revision and immutable source evidence.

---

## M4 — AgentCore Memory Gateway

**Outcome:** Every non-Swarm IDE uses the completed memory system through the existing Bifrost connection.

**Required compact surface:**

```text
memory_status
startup_context
retrieve_context
append_event
propose_fact
expand_source
session_open
session_close
build_handoff
docs_search
```

**Exit criteria:**

- Bifrost identity `agentcore-gateway` remains unchanged.
- Upstream identity `agentcore-memory` remains unchanged.
- No IDE configuration edit is required for cutover.
- Multiple IDEs use separate sessions safely.
- Append → retrieve → compact → expand works end to end.
- Startup context includes bounded global, project, session, and constraint state.
- Degraded components are reported clearly.
- No raw database or administration tools are exposed.
- Restart and reconnect tests pass.

**Rollback point:** prior compatible `agentcore-memory` adapter and Bifrost upstream configuration.

---

## M5 — Hybrid Retrieval and Curated Cognee Memory

**Outcome:** Relevant knowledge is retrieved efficiently without creating a second source of truth.

**Exit criteria:**

- PostgreSQL full-text and trigram search work.
- Selective pgvector search works.
- Official source documents live on E: and searchable metadata/indexes live on F:.
- Cognee runs natively on Windows behind `KnowledgeMemoryPort`.
- Cognee uses a separate `cognee_core` database on the PostgreSQL 18 service.
- Only promoted facts, decisions, verified fixes, reusable patterns, and curated documentation concepts enter Cognee.
- Raw transcripts and entire repositories do not enter Cognee.
- Retrieval returns provenance.
- Cognee failure does not break evidence, summaries, exact expansion, STATE generation, or full-text retrieval.
- Mem0 is not installed.

**Rollback point:** PostgreSQL-only retrieval path with Cognee disabled.

---

## M6 — Durable LangGraph Autonomous Workflow

**Outcome:** Autonomous development work resumes safely and verifies its own progress.

**Exit criteria:**

- PostgreSQL-backed LangGraph checkpoints work.
- Workflows resume after process restart.
- Threads and projects remain isolated.
- Project Charter, Milestone, Macro, Micro, checklist, and evidence state persist.
- Requirement, scope, architecture, documentation-version, security, migration, and resource gates work.
- Deterministic tests run before LLM critics.
- Risk-selected critics, scorer, and independent judge work.
- Human pause/resume works for genuine operator decisions.
- Progressive tool disclosure and JIT capability leases are backed by PostgreSQL.
- Concurrent projects cannot change each other’s visible tools, leases, or state.
- Expired leases revoke correctly.
- A/B implementation occurs only when risk or uncertainty justifies it.

**Rollback point:** last accepted LangGraph checkpoint and prior capability profile revision.

---

## M7 — Engineering Knowledge and Templates

**Outcome:** Agents use trusted examples, standards, and repeatable project foundations.

**Exit criteria:**

- Engineering Constitution exists.
- Approved dependency catalog exists.
- Recipes and focused reference implementations exist.
- All knowledge assets retain source, version, license, checksum, and provenance.
- First two Copier templates pass admission:
  - `mcp-server-python`
  - `agent-langgraph-postgres-checkpointer`
- Templates pass build, tests, lint, typecheck, secret scan, vulnerability scan, and rollback documentation.
- Templates remain distinct from reference implementations.
- No arbitrary codebase dump or whole-repository embedding requirement exists.

**Rollback point:** previous approved template/catalog revision.

---

## M8 — Operations, Recovery, Performance, and Cutover

**Outcome:** The platform operates reliably without expert intervention.

**Exit criteria:**

- Native Windows lifecycle ownership for required services.
- Backup to E: and second copy to G:.
- WAL archive and retention rules work.
- Restore tests pass.
- PostgreSQL, Bifrost, memory service, compaction worker, Cognee, and LangGraph restart tests pass.
- Missing Cognee and other optional components degrade safely.
- Context assembly, retrieval, compaction, backup, and restore performance are measured.
- Resource limits prevent workstation exhaustion.
- Security, secret, junk, and dependency scans pass.
- Old PostgreSQL cluster remains preserved for rollback.
- Complete acceptance suite passes.
- Operator quick-start, health, backup, restore-test, and diagnostic commands work.
- Swarm remains untouched.
- Final cutover is reversible.

**Rollback point:** preserved old cluster, previous gateway adapter, verified backups, and last accepted platform release.

---

## 9. Tool Policy

All approved tools may be catalogued and available for activation.

Only tools required for the current project and Milestone should be actively exposed.

Tool states:

```text
catalogued
core_active
milestone_active
jit_leased
dormant
operator_only
forbidden
```

Rules:

- Audit tools at Milestone entry and exit.
- Disable Bootstrap-only tools after M0.
- Disable completed-Milestone and expired JIT tools.
- Keep continuously active tools only when their regular use justifies context and risk.
- Administrative, destructive, whole-drive, secret-bearing, hosted-upload, raw-database, and live-IDE-config tools are operator-only.
- Runtime profiles and leases become PostgreSQL-backed in M6.
- Do not build a competing YAML/JSON lease authority before the database foundation exists.

---

## 10. Security and Boundaries

- Secrets come from Windows User environment variables or approved credential storage.
- No `.env` files for AgentCore.
- No secret values in documentation, contracts, IDE configurations, logs, evidence, or Git.
- Services bind to localhost unless explicitly approved.
- Agents write only to their assigned project/worktree and authorized storage paths.
- Swarm data, configs, databases, tasks, and tools are excluded.
- No whole-drive filesystem roots for normal agents.
- No direct IDE SQL.
- Migration execution uses a dedicated role and evidence gate.
- Destructive migrations require explicit approval.
- Live IDE configs are changed only by their documented IDE-specific installation method.
- Bifrost remains the sole normal non-Swarm MCP front door.

---

## 11. Recovery and Durability

Required recovery coverage:

- PostgreSQL logical backups
- PostgreSQL physical/base backups
- WAL archive
- Bifrost source and sanitized configuration
- AgentCore memory service source and configuration
- Artifact metadata and content-addressed objects
- Cognee database
- LangGraph state
- generated projections
- documentation indexes
- engineering knowledge assets
- templates
- Windows service/task definitions
- environment-variable name manifest without values

A backup is accepted only after a restore succeeds.

No original evidence is deleted merely because a summary exists.

---

## 12. Change Control

Changes requiring explicit operator approval:

- Reordering or removing a locked Milestone
- Weakening any Milestone exit criterion
- Replacing PostgreSQL as canonical authority
- Installing Mem0 in v1
- Replacing Cognee in v1
- Adding another canonical vector, graph, queue, lock, or state system
- Changing Bifrost identities
- Adding a second normal IDE MCP front door
- Combining AgentCore with Swarm
- Formatting a drive outside the authorized E:/F:/H:/I: correction scope
- Formatting any drive without stable physical-disk identification and verified backup
- Moving canonical workload roles between drives
- Allowing IDE agents direct database credentials
- Removing immutable evidence or exact source expansion
- Making STATE files manually edited canonical sources
- Introducing Docker or WSL as a core dependency

Cursor must stop and ask before making one of these changes.

---

## 13. Execution Discipline

At the start of each Milestone:

1. Read the authority chain.
2. Load current `STATE.md`.
3. Verify repository, branch, worktree, and Git state.
4. Run Context Fabric capture and drift check.
5. Confirm machine facts and dependent services.
6. Resolve exact dependency versions through Arabold Docs.
7. Use Serena, Depwire, and Tentra to verify structural assumptions.
8. Refine only the current Milestone’s Macro and Micro steps.
9. Record the entry evidence and rollback point.
10. Begin implementation only after the entry gate passes.

At the end of each Milestone:

1. Verify every exit criterion with evidence.
2. Run tests, lint, type checks, security, secret, and dependency checks.
3. Run Depwire verification and architecture/context drift checks.
4. Regenerate project state and handoff.
5. Audit and reduce active tools.
6. Create the restore point.
7. Commit and push intended source changes.
8. Proceed only when the Milestone passes.

No Milestone is complete because code exists. It is complete only when its exit criteria and rollback proof pass.

---

## 14. Completion Definition

The platform is complete only when:

- All M0–M8 exit criteria pass.
- Lossless append, compact, archive, retrieve, and exact-expand cycles pass.
- Multiple IDE sessions remain isolated and coherent.
- Project `STATE.md` remains current and reproducible.
- PostgreSQL, Bifrost, memory, Cognee, LangGraph, and worker restart tests pass.
- Backup and restore tests pass.
- No stale authority changes agent behavior.
- No IDE requires direct database access.
- No second canonical memory system exists.
- Swarm remains untouched.
- The operator can run health, backup, restore-test, and diagnostics without reconstructing the architecture from chat history.

---

## 15. Immediate Next Action

After the authority-reconciliation task finishes:

1. Add this file to the repository root as `BLUEPRINT.md`.
2. Classify it as current in `DOC_AUTHORITY.md`.
3. Reference it from `PROJECT_ANCHOR.md`, `CONTEXT_BLOCK.md`, and the memory-platform handoff.
4. Start a new Cursor chat in the completed reconciliation worktree.
5. Require Cursor to verify M0, refine M1 Macro/Micro steps from live evidence, and then execute M1.