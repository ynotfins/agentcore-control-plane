# MILESTONES.md — AgentCore Locked Milestones

> **Status:** Locked Milestone outcomes and exit criteria for the AgentCore platform.
> Operator-authored core Milestones M0–M8 preserved; Macro/Micro steps remain adaptable from repository and machine evidence.
> **Updated:** 2026-08-04 — current operational readiness separated from point-in-time Milestone acceptance under `AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION`; Milestone outcomes/order unchanged.

## Ecosystem and Drive Separation — Read First

AgentCore and Swarm are **independent execution control planes**. They share a machine and one explicitly neutral semantic projection service, not authority, canonical evidence, runtime ownership, credentials, or backups.

| Domain | Ownership |
| --- | --- |
| AgentCore repository / design authority | `D:\github\agentcore-control-plane` |
| AgentCore hot runtime / data namespace | `F:\AgentCore\...` |
| AgentCore staging | `I:` (unless later changed by explicit authority) |
| AgentCore cold / backup namespace | `E:\AgentCore\...` only |
| Swarm hot runtime / data | `H:` exclusively (after AgentCore relocation and acceptance cutover) |
| Swarm cold / backup namespace | `E:\Swarm\...` only |

**Hard rules**

- AgentCore must not read, write, index, ingest, summarize, administer, repair, or depend on Swarm-owned runtime, memory, databases, vaults, repositories, MCP servers, credentials, services, schedules, agents, or backups.
- Swarm must not reach AgentCore runtime, AgentCore Memory, Bifrost, `agentcore-gateway`, AgentCore databases, repositories, IDE profiles, credentials, staging, or backups.
- Neutral shared SwarmRecall is the sole bounded exception under `AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE`; AgentCore reaches it only through the server-side `agentcore-memory` adapter, and it owns no canonical evidence/checkpoint state.
- No canonical resource may be jointly owned.
- Cross-ecosystem detail belongs in an operator-carried neutral boundary contract, not in either ecosystem’s automatically ingested context.
- Any historical document that describes AgentCore-owned SwarmRecall, SwarmVault, SwarmClaw, OpenClaw, or shared storage is **historical evidence only**.

---

## Lock rules

These Milestones are locked. The authorized AgentCore execution lead may optimize, add, remove, reorder, or split the Macro and Micro steps inside them based on repository and machine evidence. Bounded IDE specialists, including Cursor subagents, may do so only inside delegated scope.

No execution lead or specialist may change without explicit operator approval:

- Milestone purpose
- Milestone exit criteria
- Milestone ordering
- Core architecture
- Storage authority
- Cognee decision
- Bifrost identity
- Lossless guarantees
- Ecosystem / drive separation rules above

## Status labels used in this file

| Label | Meaning |
| --- | --- |
| **completed (accepted)** | Exit criteria satisfied with repository audit/acceptance evidence; do not reset |
| **current / live** | In production use on CHAOSCENTRAL with current handoff/audit support |
| **transitional** | Partially complete; remaining work is bounded and evidence-gated |
| **target** | Locked destination; not yet fully proven |
| **historical evidence** | Prior facts that must not be re-executed as current instructions |
| **external boundary condition** | Swarm-side readiness AgentCore does not implement; AgentCore only proves it cannot access the Swarm domain |

Milestone acceptance is point-in-time evidence, not a perpetual runtime health claim. `CONTEXT_BLOCK.md` owns current launch readiness and may place an accepted Milestone into operational recertification without changing its locked outcome or exit criteria.

Rendered detailed execution guidance: `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` (BLUEPRINT wins on conflicts). Autonomy / Studio runbooks: `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`, `docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md`.

---

## Delivery summary (AgentCore only)

| Milestone | Status |
| --- | --- |
| M0 — Authority and Execution Foundation | **completed (accepted)** |
| M1 — PostgreSQL 18 Safety Foundation | **completed (accepted)** |
| M2 — Canonical Identity and Immutable Evidence | **completed (accepted)** |
| M3 — Lossless Context and STATE Projections | **completed (accepted)** for the recorded release; Context Engine v0.2.1 operational recertification pending |
| M4 — AgentCore Memory Gateway | **completed (accepted)** / ten-tool surface live |
| M5 — Hybrid Retrieval and Curated Cognee Memory | **completed (accepted)** with ongoing ops restore-test evidence |
| M6 — Durable LangGraph Autonomous Workflow | **completed (accepted)** / live baseline; new post-v0.2.1 production canary pending |
| M7 — Engineering Knowledge and Templates | **completed (accepted)** |
| M8 — Operations, Recovery, Performance, and Cutover | **completed (accepted)** at the recorded release; current PG18 lifecycle-owner recertification pending |
| M9 — AgentCore Relocation and Ecosystem Separation | **transitional / target** — Bifrost runtime already on `F:\AgentCore\runtime` (current); full H: vacation + negative-access acceptance still required |

This file does **not** define Swarm build milestones. Swarm readiness appears only as an external boundary condition after M9 acceptance.

---

## M0 — Authority and Execution Foundation

**Status:** completed (accepted)

**Outcome:** Every agent sees one accurate architecture and execution policy.

**Exit criteria:**

- One authoritative read order.
- Stale Swarm-first and old database instructions neutralized.
- Current machine authority referenced.
- Per-IDE global-rule profiles created.
- New Project, Milestone, Macro/Micro, checklist, Context Fabric, Arabold, and tool-audit policies established.
- This exact memory-platform Milestone plan is the execution authority.
- No live memory/database implementation begins in M0.

---

## M1 — PostgreSQL 18 Safety Foundation

**Status:** completed (accepted)

**Outcome:** A recoverable PostgreSQL 18 + pgvector platform exists beside the preserved old cluster.

**Exit criteria:**

- Existing cluster inventory completed.
- Logical and physical backups created.
- At least one restore test passes.
- PostgreSQL 18 and compatible pgvector run on F:.
- Required databases and least-privilege service roles exist.
- Old PostgreSQL installation remains recoverable.
- Rollback is proven.

---

## M2 — Canonical Identity and Immutable Evidence

**Status:** completed (accepted)

**Outcome:** Every durable operation has an identity and every accepted event is preserved.

**Exit criteria:**

- Machine, user, project, repo, worktree, IDE/client, agent, session, run, and LangGraph thread identities are separate.
- Append-only evidence ledger works.
- Idempotent event writes work.
- Large payloads are externalized by content hash.
- Project A cannot write Project B.
- Normal IDE agents have no database credentials.
- Raw evidence cannot be updated or deleted by normal service roles.

---

## M3 — Lossless Context and STATE Projections

**Status:** completed; Context Engine v0.2.4 exact-installed and live-certified on 2026-08-04

**Outcome:** Long sessions compact without losing recoverability.

**Exit criteria:**

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

---

## M4 — AgentCore Memory Gateway

**Status:** completed (accepted) / current

**Outcome:** All AgentCore / enrolled non-Swarm IDEs use the completed memory system through the existing Bifrost connection.

**Required compact tool surface:**

- memory_status
- startup_context
- retrieve_context
- append_event
- propose_fact
- expand_source
- session_open
- session_close
- build_handoff
- docs_search

**Exit criteria:**

- Existing agentcore-memory Bifrost identity is preserved.
- No IDE configuration change is required for memory-platform cutover.
- Multiple IDEs can use separate sessions safely.
- Append → retrieve → compact → expand works end to end.
- Degraded components are reported clearly.
- No raw database/admin tools are exposed.

---

## M5 — Hybrid Retrieval and Curated Cognee Memory

**Status:** completed (accepted) with continuing restore/ops evidence

**Outcome:** Relevant facts and knowledge are retrieved efficiently without creating a second source of truth.

**Exit criteria:**

- PostgreSQL full-text search and trigram search work.
- Selective pgvector search work.
- Official documents live on E: and indexes live on F:.
- Cognee runs natively behind KnowledgeMemoryPort.
- Cognee uses its own cognee_core database on the PostgreSQL 18 service.
- Only promoted knowledge enters Cognee.
- Raw transcripts and entire repositories do not enter Cognee.
- Cognee failure does not break evidence, summaries, exact expansion, or STATE generation.
- Mem0 is not installed.

---

## M6 — Durable LangGraph Autonomous Workflow

**Status:** completed (accepted) / live baseline; commercial launch recertification pending

**Outcome:** The autonomous developer workflow resumes safely and verifies its work. LangGraph Studio remains the approved interactive autonomy surface for AgentCore-managed arbitrary-project engineering within governed write boundaries.

**Exit criteria:**

- PostgreSQL-backed LangGraph checkpoints.
- Resume after process restart.
- Milestone state and checklist state persist.
- Requirement/scope/architecture drift gates.
- Critic, deterministic scorer, and independent judge.
- A/B implementation only when risk justifies it.
- Human pause/resume for genuine operator decisions.
- Progressive tool disclosure and JIT leases backed by PostgreSQL.
- Concurrent projects cannot change each other’s tools or state.
- Production CLI runs from `D:\github\agentcore-control-plane\scripts` with `D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe -m agentcore workflow …`.
- Studio is localhost-bound, isolated from production thread IDs, and not a persistent Windows service.
- Deep Agents remains a bounded worker harness inside LangGraph nodes only (`docs/decisions/ADR-DEEP-AGENTS-WORKER-HARNESS.md`).
- Workflows operate only on AgentCore and explicitly enrolled non-Swarm projects — never on Swarm-owned repositories through AgentCore continuity.

---

## M7 — Engineering Knowledge and Templates

**Status:** completed (accepted)

**Outcome:** Agents have trusted examples and predictable implementation standards.

**Exit criteria:**

- Engineering Constitution.
- Approved dependency catalog.
- Recipes and focused reference implementations.
- Official-source provenance.
- First two Copier templates pass admission:
  - mcp-server-python
  - agent-langgraph-postgres-checkpointer
- No random codebase dump.
- No whole-repository embedding requirement.

---

## M8 — Operations, Recovery, Performance, and Cutover

**Status:** completed (accepted) at the recorded release; current lifecycle-owner and release recertification tracked in `CONTEXT_BLOCK.md`

**Outcome:** The platform operates reliably without expert intervention.

**Exit criteria:**

- Native Windows lifecycle ownership.
- Backup to AgentCore cold namespace on E: and second copy to G:.
- Restore tests pass.
- PostgreSQL, memory service, Bifrost, Cognee, and LangGraph restart tests pass.
- Resource limits prevent workstation exhaustion.
- Context assembly and retrieval latency measured.
- Security and secret scans pass.
- Old PostgreSQL remains preserved for rollback.
- Complete acceptance suite passes.
- Swarm remains untouched by AgentCore ops.
- AgentCore continues the LangGraph Studio / autonomous arbitrary-project production-readiness trajectory under AgentCore write boundaries only.

---

## M9 — AgentCore Relocation and Ecosystem Separation

**Status:** transitional / target
**Purpose:** Vacate `H:` of AgentCore canonical ownership, lock AgentCore hot runtime/data under `F:\AgentCore\...`, isolate AgentCore cold/backup under `E:\AgentCore\...`, and prove AgentCore cannot access the final Swarm domain. This milestone does **not** build, install, configure, or operate Swarm.

### Current vs target (do not confuse)

| Item | Classification |
| --- | --- |
| Bifrost live root `F:\AgentCore\runtime\bifrost` | **current state** (relocated; commit evidence on main) |
| Historical Bifrost root `H:\AgentRuntime\...` | **historical evidence** / vacated for Bifrost |
| Remaining AgentCore leaves under `H:` (if any) | **transitional** — must be inventoried and vacated under this milestone |
| AgentCore cold namespace `E:\AgentCore\...` | **target**; transitional backup evidence may still use `E:\AgentCore-Backups` until cutover acceptance |
| Swarm hot exclusive use of `H:` | **target** after M9 acceptance |
| Swarm cold namespace `E:\Swarm\...` | **external target / operator intent** — AgentCore does not implement Swarm layout |
| Full negative-access proof AgentCore ↛ Swarm domain | **required exit evidence** for M9 |

### Exit criteria (objective)

1. **Inventory:** Complete inventory of AgentCore-owned paths, services, scheduled tasks, renderers, contracts, runbooks, and validators that still reference `H:\AgentRuntime`, `H:` as AgentCore future-state storage, or Swarm components as AgentCore subsystems.
2. **Relocation:** All authoritative AgentCore runtime/data leaves required for AgentCore operation exist under `F:\AgentCore\...` (and PostgreSQL 18 under its approved F: data directory). No AgentCore canonical runtime, data, WAL, checkpoint, queue, lock, or rollback leaf remains on `H:`.
3. **Cold/backup isolation:** AgentCore backups and cold archives resolve only under `E:\AgentCore\...` (or an explicitly documented transitional path that is retired by acceptance). No AgentCore backup writes under `E:\Swarm\...` or Swarm backup roots.
4. **Contracts / renderers / runbooks:** Source-controlled AgentCore contracts, Bifrost renderers, ops scripts, and primary runbooks no longer instruct agents to treat `H:` as AgentCore runtime/data home. Remaining hits outside the four authority docs are classified and scheduled; they do not block M9 if they are clearly historical evidence only.
5. **Restart / recovery proof:** Bifrost, PostgreSQL 18, agentcore-memory, and LangGraph production restart/recovery succeed from the F:-anchored layout. Backup + restore-test evidence is recorded under `audits/`.
6. **Negative-access tests:** Automated or scripted proofs that AgentCore normal ops, validators, gateway upstreams, memory tools, and project router do **not** read/write Swarm runtime roots, Swarm DBs, Swarm MCP servers, or Swarm backup namespaces.
7. **Context-contamination checks:** AgentCore IDE enrollment package, project router, and memory lifecycle refuse Swarm-owned repositories as AgentCore projects. No AgentCore memory session, projection, or IDE profile persists Swarm work as AgentCore project history.
8. **Git / document acceptance:** Authority docs (`PROJECT_ANCHOR.md`, `BLUEPRINT.md`, `MASTER_CONFIG_AND_PROMPT.md`, this file) are internally consistent; validators pass; intended docs committed and pushed per `docs/GIT_PUSH_ONLY_POLICY.md`.
9. **Rollback gate:** Documented rollback to the last accepted Bifrost/runtime backup exists before declaring H: vacated. Rollback must not reintroduce Swarm-as-AgentCore-subsystem language into live authority.
10. **External boundary condition (not a Swarm build task):** After M9 acceptance, AgentCore has vacated `H:` and cannot access the final Swarm domain. Swarm build/readiness remains entirely outside this milestone.

### Explicit non-goals

- Installing, configuring, repairing, or administering SwarmClaw, SwarmRecall, SwarmVault, SwarmDock, SwarmFeed, SwarmRelay, OpenClaw, or ClawX.
- Prescribing Swarm native internal architecture.
- Claiming Swarm product readiness.
- Resetting or reopening completed M0–M8 AgentCore acceptance.

### Rollback point

Last accepted Bifrost/runtime backup under AgentCore backup namespace, previous gateway adapter/config revision, and the pre-M9 authority document revision set.

---

## Notes for implementers

- Preserve completed AgentCore milestone evidence under `audits/` and handoffs. Do not reset accepted work because separation docs were reconciled.
- LangGraph Studio and the AgentCore autonomous workflow remain the AgentCore autonomy target for arbitrary **AgentCore-enrolled** projects.
- Dual-workspace visibility is read-only for cross-ecosystem collision audits; it is not shared authority and not authorization to mutate Swarm.
