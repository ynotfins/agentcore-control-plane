---
document: CONTEXT_BLOCK.md
project: AgentCore Global Memory, Context, Database, and Governance Platform
authority: current-state-and-implementation-progress (level 4 in DOC_AUTHORITY.md hierarchy)
status: current
verified_at: 2026-07-14
canonical_repository: D:\github\agentcore-control-plane
locked_blueprint: BLUEPRINT.md
implementation_authority: docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md
---

# AgentCore Canonical Context Block

Read `BLUEPRINT.md` before this file. BLUEPRINT.md is the locked implementation authority (architecture, storage roles, lossless guarantees, Milestone exit criteria). This file records current mutable state and implementation progress. Where this file's decisions conflict with BLUEPRINT.md, BLUEPRINT.md wins.

Older plans, reports, prompts, rules, and generated renderers are evidence only until they have been reconciled against BLUEPRINT.md and the live machine.

## 0. Status language

This document uses four labels:

- **VERIFIED FACT** — established from the live-machine evidence, repository evidence, or an authoritative upstream source.
- **ADOPTED DECISION** — the selected architecture for this build.
- **GATED DECISION** — direction is selected, but execution requires a fresh live check or benchmark.
- **OUT OF SCOPE** — do not integrate, migrate, or redesign during this project.

Do not convert a gated decision into a fact.

---

## 1. Repository and path identity

### VERIFIED FACT

The canonical source repository is:

```text
D:\github\agentcore-control-plane
```

The path:

```text
D:\AgentSwarm\runs\agentcore-memory-v1\worktree
```

is an additional Git worktree/check-out of the same `agentcore-control-plane` repository on branch:

```text
ai/global-memory-platform-v1
```

`D:\AgentSwarm` is a run/worktree storage root. It is not the name of this product, not a separate AgentCore repository, and not related to SwarmClaw.

### ADOPTED DECISION

All implementation must remain in `agentcore-control-plane`.

Use an isolated worktree for feature-branch implementation unless the operator explicitly changes the active checkout. Do not independently edit both the main checkout and a feature worktree.

The authority reconciliation (2026-07-14) was performed on branch `task/authority-reconciliation` in the main checkout. The memory-platform build follows `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` and the handoff in `docs/handoffs/MEMORY_PLATFORM_IMPLEMENTATION_HANDOFF_2026-07-14.md`; the pre-existing `ai/global-memory-platform-v1` worktree at `D:\AgentSwarm\runs\agentcore-memory-v1\worktree` predates the locked Milestones and must be reconciled against them before reuse.

The prior plans below are not authoritative because they contain stale drive facts and/or incorrectly make Swarm components part of AgentCore:

```text
agentcore_global_memory_platform_d69b09fd.plan.md
agentcore_memory_platform_4476bf06.plan.md
```

The previous content of `CONTEXT_BLOCK.md` is superseded by this file.

---

## 2. Product objective

### ADOPTED DECISION

Build one local-first AgentCore platform that gives normal IDE agents and LangGraph workflows:

1. Persistent global, user, machine, project, workflow, and session memory.
2. An immutable, recoverable event ledger.
3. A rolling context compiler with a recent raw tail, hierarchical summaries, exact source expansion, and model-specific token budgets.
4. Governed semantic and graph memory through Cognee.
5. Durable LangGraph checkpoints and workflow metadata.
6. Generated read-only state projections.
7. A governed engineering knowledge and template library.
8. One default AgentCore memory/context contract for all supported non-Swarm IDEs and agents.
9. Hard write boundaries, provenance, auditing, backup, restore, degraded mode, and actionable diagnostics.

The system must reduce prompt bloat by retrieving and assembling only the context needed for the current task. Fast storage accelerates persistence, search, indexing, context assembly, and compaction; it does not enlarge a model's native context window.

---

## 3. Canonical architecture

```text
Cursor / Codex / MiniMax / Antigravity / Open Interpreter /
Claude Code / approved MCP clients / LangGraph workflows
                           |
          native lifecycle adapter where available
                or thin MCP stdio bridge
                           |
                           v
                AgentCore persistent daemon
        identity | policy | sessions | event ingestion
        retrieval | context assembly | durable writes
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
 PostgreSQL 18 + pgvector              Cognee API
 canonical state/evidence              semantic/graph memory
          |                                 |
          +----------------+----------------+
                           |
                           v
                  AgentCore worker
       compaction | promotion | projection | archival
                           |
             +-------------+-------------+
             |                           |
             v                           v
     H:\AgentRuntime              E:\AgentCoreArchive
     hot spool/scratch            cold immutable/archive
```

### ADOPTED DECISION — Bifrost composition (completed cutover)

The Bifrost MCP Gateway cutover is **complete and live**. The stable IDE-facing MCP path for every non-Swarm IDE is:

```text
IDE agent
  -> agentcore-gateway (Bifrost, http://127.0.0.1:8080/mcp, Bearer ${env:BIFROST_MCP_VIRTUAL_KEY})
  -> agentcore-memory  (stable Bifrost upstream identity)
```

The AgentCore memory system is exposed to IDEs **through** the existing `agentcore-memory` Bifrost upstream. The "thin MCP stdio bridge" in the diagram above is the `agentcore-memory` stdio server registered behind Bifrost — it is not a new per-IDE MCP entry. IDEs keep exactly one `agentcore-gateway` entry; no IDE configuration change is required when the memory platform lands (Milestone M4 exit criterion).

### ADOPTED DECISION

Normal IDEs do not connect directly to PostgreSQL or Cognee.

Normal IDEs use one AgentCore-owned contract exposed through:

- the `agentcore-memory` upstream behind `agentcore-gateway` (the normal IDE path);
- a local AgentCore client/SDK;
- a localhost API for LangGraph, Cognigent, diagnostics, and administration.

MCP is a transport, not the source of truth.

A persistent AgentCore daemon owns business logic and the governed write path. Per-IDE transport processes contain transport logic only.

A durable AgentCore worker owns background jobs. It does not replace the synchronous hard-threshold context path.

---

## 4. Selected upstream components

The following are the selected components for AgentCore.

### 4.1 PostgreSQL

**VERIFIED FACT — 2026-07-12**

The current PostgreSQL 18 minor release is PostgreSQL 18.4.

Authoritative source:

```text
https://www.postgresql.org/docs/current/release.html
```

### ADOPTED DECISION

PostgreSQL 18 is the canonical AgentCore database platform.

The existing PostgreSQL 16 cluster must be backed up, restore-tested, and migrated side-by-side. PostgreSQL 18 must use a new data directory. Never point PostgreSQL 18 directly at the PostgreSQL 16 data directory.

PostgreSQL owns:

- immutable event envelopes and provenance;
- context sessions and summary graph metadata;
- global/project/session state;
- project, agent, client, and machine identity;
- policies, capabilities, approvals, and audit records;
- durable background jobs, attempts, outbox, and dead-letter records;
- LangGraph checkpoint persistence;
- engineering-library catalog and retrieval audit;
- artifact metadata, hashes, references, and lifecycle state.

### 4.2 pgvector

**VERIFIED FACT — 2026-07-12**

The current official pgvector repository instructions use pgvector `v0.8.5` and include Windows/PostgreSQL 18 build instructions.

Authoritative source:

```text
https://github.com/pgvector/pgvector
```

### ADOPTED DECISION

Use pgvector in PostgreSQL 18. Do not add Qdrant, Weaviate, LanceDB, Chroma, Neo4j, Redis, or another AgentCore database by default.

A separate engine requires a benchmark proving a distinct requirement that PostgreSQL full-text search, pgvector, and Cognee cannot satisfy.

### 4.3 Cognee

**VERIFIED FACT — 2026-07-12**

Cognee is an open-source persistent AI memory platform that builds a self-hosted knowledge graph. Its official repository documents a single-PostgreSQL deployment using:

```text
DB_PROVIDER=postgres
VECTOR_DB_PROVIDER=pgvector
GRAPH_DATABASE_PROVIDER=postgres
CACHE_BACKEND=postgres
```

The upstream release list marks `v1.2.2` as a stable release and newer `v1.2.2.dev*` builds as development releases.

Authoritative sources:

```text
https://github.com/topoteretes/cognee
https://github.com/topoteretes/cognee/releases
```

### ADOPTED DECISION

Use Cognee `v1.2.2` as the initial pinned stable candidate, subject to one final release/security compatibility check immediately before installation.

Cognee is the semantic and graph-memory engine. It is not the immutable raw transcript ledger, not the policy engine, and not the public IDE interface.

Cognee runs behind an AgentCore-owned adapter. No AgentCore package outside that adapter imports Cognee-specific APIs.

Cognee receives curated or high-confidence promoted knowledge. Do not send every terminal line, file read, tool result, or raw transcript event directly to Cognee.

Use a separate PostgreSQL database and role:

```text
database: cognee_core
owner/role: agentcore_cognee
```

AgentCore must not write Cognee-owned tables directly.

### 4.4 LangGraph PostgreSQL checkpointer

**VERIFIED FACT — 2026-07-12**

`langgraph-checkpoint-postgres` 3.1.0 is the current stable package listed on PyPI. It provides `PostgresSaver` and `AsyncPostgresSaver`.

Authoritative sources:

```text
https://pypi.org/project/langgraph-checkpoint-postgres/
https://docs.langchain.com/oss/python/langgraph/persistence
```

### ADOPTED DECISION

Use the official PostgreSQL checkpointer. Do not implement a custom checkpoint serializer unless a tested requirement cannot be met by the official package.

Required hardening:

```text
LANGGRAPH_STRICT_MSGPACK=true
```

Use UUID-based `thread_id` values and keep them under 255 characters.

LangGraph checkpoints are thread-scoped workflow state. They do not replace AgentCore semantic memory, the immutable event ledger, or project state.

### 4.5 Model Context Protocol SDK

**VERIFIED FACT — 2026-07-12**

The official MCP Python SDK identifies v1.x as the stable production line. The repository lists `v1.28.1` as the latest stable release and warns that v2 is still pre-release.

Authoritative source:

```text
https://github.com/modelcontextprotocol/python-sdk
```

### ADOPTED DECISION

Initially pin the stable MCP Python SDK line:

```text
mcp>=1.28.1,<2
```

Re-evaluate only after stable v2 is released and migration tests pass. Do not build production AgentCore against a pre-release MCP SDK.

### 4.6 COMB

**VERIFIED FACT**

`mehmetdemirci/comb-ai` is an MIT-licensed documentation methodology. It separates static from dynamic knowledge, uses hierarchical task-specific loading, favors cache-aware reading order, and archives stale active context.

Authoritative source:

```text
https://github.com/mehmetdemirci/comb-ai
```

### ADOPTED DECISION

Use COMB concepts and selected templates as an AgentCore documentation/projection convention.

COMB is not a daemon, database, queue, memory engine, or separate service.

AgentCore remains the authority. COMB-derived files are generated or curated views.

### 4.7 Internal AgentCore code

The following are AgentCore-owned implementations, not external memory products:

- immutable event ledger contracts;
- context compiler;
- hierarchical compaction and exact expansion;
- artifact tier;
- project/client/agent identity;
- policy and capability engine;
- memory promotion pipeline;
- AgentCore daemon;
- thin MCP bridge;
- background worker;
- state projection;
- IDE lifecycle adapters;
- engineering-library governance and indexing.

### 4.8 Reference-only projects

The following may provide concepts or test cases but are not runtime dependencies:

```text
lossless-claw
lossless-memory4agent
Distill
Hindsight
Graphiti / Zep
Mem0
agentmemory
OpenMemory
claude-changeling-agent
```

Do not copy runtime architecture from these projects without an explicit ADR, license/provenance record, tests, and a clear reduction in complexity.

---

## 5. Explicit exclusions

### OUT OF SCOPE

The vendor repositories under:

```text
D:\github\vendor\swarm\
```

and the SwarmVault Desktop data under:

```text
C:\Users\ynotf\AppData\Roaming\swarmvault-desktop
```

are not part of this AgentCore memory-platform build.

Do not route AgentCore memory through SwarmRecall or SwarmVault.

Do not remove, migrate, reconfigure, or redesign Swarm projects during this build.

The word `AgentSwarm` in the worktree path does not refer to the vendor Swarm ecosystem.

---

## 6. Data planes and source-of-truth boundaries

### 6.1 Immutable evidence plane

**Canonical authority:** PostgreSQL 18 plus content-addressed artifact objects.

Every meaningful session event receives an append-only envelope with at least:

```text
event_id
client_event_id / idempotency_key
session_id
project_id
agent_identity_id
client_id / IDE
machine_id
sequence_number
parent_event_id
correlation_id
tool_call_id
role
event_type
model_id
tokenizer_id
token_count
inline_content or artifact reference
content_sha256
occurred_at
ingested_at
trust_zone
metadata
```

Normal roles cannot update or delete raw events.

Large bodies are externalized by hash; PostgreSQL keeps the authoritative metadata and reference.

### 6.2 Rolling context plane

AgentCore assembles context from:

1. global invariant state;
2. current-project state;
3. current LangGraph workflow/thread state;
4. current task and constraints;
5. recent raw event tail;
6. relevant summary nodes;
7. curated Cognee recall;
8. targeted project/code/document retrieval.

Compaction is evaluated after each appended event and before model calls.

```text
below soft threshold:
    continue normally

above soft threshold:
    enqueue durable compaction job

above hard threshold:
    synchronously compact enough context
    or return a deterministic reduced context with exact source references
```

Summary hierarchy:

```text
L0 raw immutable events
L1 coherent event-span summaries
L2 session summaries
L3 project chronology and decision summaries
```

Every summary must retain source edges and support exact expansion.

Project summaries never become global memory automatically.

### 6.3 Semantic and graph memory plane

Cognee stores:

- approved user preferences;
- stable machine/workflow facts;
- project architecture and decisions;
- verified fixes and failure patterns;
- accepted lessons;
- governed engineering-library concepts and relations.

Cognee does not store the only copy of evidence.

### 6.4 Workflow plane

LangGraph owns:

- graph execution state;
- checkpoints;
- resumability;
- human-review pauses;
- workflow metadata references.

Cognigent is treated as an AgentCore product layer/name for operator experience, routing, approvals, and governance. It is not assumed to be a verified third-party runtime. The AgentCore API must support it without making the core depend on an unverified external package.

### 6.5 Projection plane

PostgreSQL is canonical.

Generated files may include:

```text
GLOBAL_STATE.md
<repo>\.agentcore\STATE.md
INDEX.md
active-context.md
architecture/decision projections
```

Generated projections are:

- read-only to ordinary agents;
- bounded;
- atomically written;
- revisioned;
- content-hashed;
- traceable to source event/state IDs;
- reproducible from PostgreSQL.

### 6.6 Engineering knowledge plane

Canonical source material and cold history live on E:.

Hot metadata, full-text indexes, embeddings, graph relationships, version filters, provenance, and retrieval audit live on F:.

Initial library categories:

```text
official documentation snapshots
approved project templates
focused reference implementations
engineering recipes
dependency catalog
agent skills
agent benchmarks
security and architecture standards
```

Use Copier for updateable governed templates. Do not build a giant uncurated code dump.

---

## 7. Drive assignments

The following role map is the target. Destructive operations still require a fresh physical-disk identity check by model, serial, UniqueId, disk number, capacity, bus type, filesystem, allocation unit, health, BitLocker state, and current dependencies.

### C: — system tier

**VERIFIED FACT**

Approximately 2 TB internal NVMe containing Windows, installed applications, user profile, IDE configuration, and the current Docker Desktop disk image.

### ADOPTED DECISION

- Keep Windows and installed applications.
- Protect from AgentCore data growth.
- Move Docker/WSL runtime data and large active caches away.
- Never reformat as part of this project.

### D: — active development tier

**VERIFIED FACT**

Approximately 2 TB internal NVMe containing active repositories and development data.

### ADOPTED DECISION

Use for:

```text
D:\github\
D:\github_2\
active repositories
Git worktrees
build/test activity
AgentCore source code
template and reference development
```

Do not place canonical databases, long-term backups, model archives, or cold corpora here.

### E: — cold archive and knowledge-source tier

**VERIFIED FACT**

E: is the internal approximately 10 TB, 7200 RPM HGST-class SATA HDD now visible as `Archive_Cold`.

It is not the obsolete 932 GB external-device assumption from an earlier plan.

### ADOPTED DECISION

Use E: for:

```text
E:\AgentCoreArchive\
E:\DatabaseBackups\
E:\ProjectArchives\
E:\KnowledgeCorpus\
E:\TemplateLibrary\
E:\ReferenceImplementations\
E:\EngineeringRecipes\
E:\DependencyCatalog\
E:\ModelArchive\
E:\SystemImages\
```

NTFS 64 KB is appropriate for this large sequential/archive workload and should be retained unless a fresh live scan contradicts the current format.

Do not place active PostgreSQL data, pgvector indexes, LangGraph checkpoints, node_modules, virtual environments, active worktrees, or hot context scratch on E:.

Pack small cold objects into larger compressed segments rather than creating millions of tiny files.

### F: — canonical hot database and index tier

**VERIFIED FACT**

F: is the 4 TB Samsung 990 PRO Gen4 NVMe and already hosts the AgentCore PostgreSQL runtime/data.

### ADOPTED DECISION

F: is the canonical hot data tier for:

```text
PostgreSQL 18 cluster
pgvector indexes
agent_core database
cognee_core database
LangGraph checkpointer tables
global/project/session state
event and summary metadata
durable job/outbox tables
hot engineering-library indexes
retrieval metadata and audit
```

Do not reformat F: during the initial build.

Build PostgreSQL 18 side-by-side in a new F: path, migrate through a tested backup/upgrade procedure, and retain the PostgreSQL 16 cluster during the rollback window.

Keep PostgreSQL WAL with the F: cluster initially. Archive completed WAL copies to E:. Move WAL to another device only after benchmark and recovery evidence proves a net benefit.

No normal IDE or filesystem MCP may access raw F: database directories.

### G: — external backup tier

**VERIFIED FACT**

G: is an external approximately 4 TB Seagate backup drive.

### ADOPTED DECISION

Use only for independent backup copies and restore testing.

G: is not a live database, vector index, context store, or runtime tier.

### H: — high-speed AgentCore runtime tier

**VERIFIED FACT**

H: is the internal 2 TB Crucial P5 Plus NVMe installed through the PCIe expansion path.

**VERIFIED FACT — 2026-07-14 (supersedes any provisioning language)**

H: is **already provisioned and live**. It hosts the running Bifrost MCP Gateway at `H:\AgentRuntime\bifrost` (binary, config, sqlite stores, logs, state) and Tentra data at `H:\AgentRuntime\tentra\data`. **H: must never be formatted, re-provisioned, or repartitioned.** Any earlier "provision H:" instruction is void.

### ADOPTED DECISION

Additional AgentCore runtime directories are created alongside the existing runtime (no formatting, no relocation of the live Bifrost runtime):

```text
H:\AgentRuntime\artifact-hot\
H:\AgentRuntime\context-scratch\
H:\AgentRuntime\compaction-scratch\
H:\AgentRuntime\service-logs\
H:\AgentRuntime\temporary-indexes\
```

Docker Desktop relocation to H: is **not** part of the memory platform (no Docker/WSL dependency for the core platform). Any Docker relocation is a separate operator-approved task.

H: contains no sole canonical copy of durable memory.

### I: — developer cache and staging tier

**VERIFIED FACT**

I: is the internal 1 TB Crucial BX500 SATA SSD.

### GATED DECISION

The role is fixed:

```text
package caches
build intermediates
ingestion staging
temporary exports
compiler caches
non-canonical scratch
```

**BLUEPRINT.md §4 supersedes the ReFS evaluation above.** The target for I: is NTFS with 64 KB allocation units. Live evidence (2026-07-14): I: is currently NTFS with 512-byte allocation units and is empty — correction is authorized by BLUEPRINT.md §4. ReFS Dev Drive evaluation is deferred; the M1 storage step corrects I: to NTFS/64KB.

Do not put PostgreSQL, Cognee canonical data, WAL, LangGraph checkpoints, or the only copy of any artifact on I:.

### J: — personal external device

If J: is present, it is outside AgentCore scope. Provisioning scripts must block it.

---

## 8. PostgreSQL database and role boundaries

### ADOPTED DECISION

Use one PostgreSQL 18 cluster on F: with explicit database ownership boundaries:

```text
agent_core
    AgentCore-owned canonical state, evidence, jobs, governance,
    context metadata, library catalog, and LangGraph persistence

cognee_core
    Cognee-owned graph/vector/session/metadata data
```

Do not place vendor Swarm databases inside the AgentCore logical architecture.

Minimum role separation:

```text
agentcore_read
agentcore_ingest
agentcore_worker
agentcore_admin
agentcore_backup
agentcore_cognee
```

Ordinary IDE agents never receive database credentials.

`LISTEN/NOTIFY` may wake workers, but it is not the durable queue. Durable job rows must exist in PostgreSQL and be claimed transactionally.

---

## 9. AgentCore services

### ADOPTED DECISION

Keep the core topology small:

```text
1. PostgreSQL 18
2. Cognee API/service
3. AgentCore daemon
4. AgentCore worker
5. thin per-IDE MCP stdio bridge processes
```

The daemon owns:

- project/client/agent identity;
- sessions;
- policy;
- event ingestion;
- retrieval;
- context assembly;
- durable write validation;
- health and admin endpoints.

The worker owns:

- summary compaction;
- Cognee promotion;
- generated projections;
- archival;
- maintenance;
- durable retries and dead letters.

The MCP bridge owns only transport and authentication handoff.

Do not start one full database writer or memory service per IDE.

---

## 10. Unified AgentCore contract

The final names may be optimized by Cursor, but the contract must cover:

```text
session.open
session.append_event
session.close

context.get
context.search
context.expand

memory.search
memory.propose
memory.promote        operator/governed
memory.forget         operator/governed soft-delete

state.read
state.propose_change

project.register
project.resolve
project.list

agent.whoami
health.get
```

Normal agents cannot:

- run raw SQL;
- call Cognee directly;
- mutate generated STATE files;
- promote untrusted content to global memory;
- write another project's files;
- delete immutable evidence;
- write raw F: or E: storage paths.

MCP registration does not guarantee event capture. Each IDE requires measured lifecycle hooks, wrappers, extensions, or direct SDK instrumentation.

LangGraph/Cognigent must use direct AgentCore client instrumentation.

---

## 11. Identity and permissions

### ADOPTED DECISION

Every registered repository receives a stable UUID in:

```text
<repo>\.agentcore\project.yaml
```

Git remotes, local paths, Git common directories, worktrees, and archive locations are aliases. A Git remote URL alone is not canonical project identity.

Agents may read approved global knowledge and registered project metadata.

Source-code writes are limited to the assigned active repository/worktree.

Hard enforcement must occur at the tool/process/OS boundary where possible:

- narrow filesystem roots;
- Serena launched against the active project;
- isolated Git worktrees;
- protected database/archive paths;
- sandboxed Open Interpreter;
- dedicated low-privilege autonomous worker identity;
- audited escalation.

A memory policy check alone cannot prevent an IDE terminal or filesystem tool from writing elsewhere.

---

## 12. `context-fabric`

### VERIFIED FACT

`context-fabric` is an existing AgentCore-side project-local context component. It is not part of the vendor Swarm ecosystem.

### GATED DECISION

Inspect and benchmark it before final integration.

It may remain only if it provides a distinct project-local capability such as deterministic repository context, local indexing, or cache management.

It must not become:

- a second global memory authority;
- a duplicate immutable ledger;
- a duplicate semantic database;
- an uncontrolled durable writer.

Choose one disposition through an ADR:

```text
keep behind AgentCore
integrate useful code into AgentCore
retire as superseded
```

---

## 13. Engineering knowledge and template platform

### ADOPTED DECISION

Create a governed library because no existing project is trusted as a house-style authority.

Use:

```text
E: canonical source snapshots and approved template/reference history
F: searchable catalog, embeddings, graph relationships, and retrieval audit
D: active template/reference development and tests
H: active models and runtime cache
I: package/build cache and ingestion staging
```

Start with a small set of high-value approved templates and focused references. Every approved item requires:

- source and license provenance;
- pinned dependencies and lockfiles;
- current stable-version review;
- clean generation/build;
- tests, lint, and type checking;
- secret, dependency, and static-analysis scans;
- architecture, security, operations, and rollback documentation;
- benchmark evidence;
- lifecycle status: candidate, approved, deprecated, or retired.

Use Copier for updateable templates.

Do not add LanceDB or another library database initially.

---

## 14. Implementation order

### ADOPTED DECISION

```text
Phase 0 — repository alignment
    replace stale context
    audit accessible rules, prompts, docs, renderers, MCP descriptions
    classify authority and deprecate contradictions

Phase 1 — live machine and storage baseline
    rescan disks, services, tasks, Docker, WSL, ports, dependencies
    protect active data
    clean abandoned Docker/WSL/software through approved manifests

Phase 2 — storage foundation
    provision H after verification
    test and provision I
    organize E
    relocate Docker Desktop disk image to H
    validate reboot and recovery

Phase 3 — PostgreSQL 18 foundation
    stabilize PostgreSQL 16
    complete backup and restore rehearsal
    install PostgreSQL 18.4 side-by-side
    install pgvector 0.8.5
    test migration/cutover/rollback
    make PostgreSQL 18 canonical

Phase 4 — AgentCore contracts and storage
    identities and project registry
    immutable event ledger
    artifact metadata/tiering
    durable jobs/outbox
    policy and audit

Phase 5 — rolling context
    context compiler
    soft/hard thresholds
    summary DAG
    exact expansion
    replay and recovery tests

Phase 6 — Cognee
    pinned stable deployment
    dedicated database/role
    AgentCore adapter
    governed promotion pipeline
    degraded-mode tests

Phase 7 — LangGraph and Cognigent interface
    official Postgres checkpointer
    workflow metadata and AgentCore context nodes
    operator/governance API

Phase 8 — unified gateway and client capture
    persistent daemon
    thin MCP bridges
    per-IDE lifecycle adapters
    measured capture and context-injection tests

Phase 9 — state projections and engineering library
    generated state
    COMB-derived conventions
    approved templates/references/recipes/dependencies
    AgentBench

Phase 10 — rollout
    shadow mode
    per-project activation
    backup/restore/degraded-mode testing
    retire only proven duplicate AgentCore components
```

Do not apply production AgentCore schemas to PostgreSQL 16 and then immediately migrate them to PostgreSQL 18.

---

## 15. Acceptance criteria

The platform is not complete until all of the following pass:

1. A long synthetic session is compacted repeatedly and an exact early event is recoverable by hash/source ID.
2. AgentCore continues in degraded mode when Cognee is unavailable.
3. LangGraph resumes a workflow after process and PostgreSQL restart.
4. Duplicate client events are rejected idempotently.
5. Cursor and another IDE can work concurrently without cross-project memory leakage.
6. A source write outside the assigned worktree is blocked by the actual tool/process boundary.
7. `GLOBAL_STATE.md` and project `STATE.md` can be deleted and reproduced from PostgreSQL.
8. PostgreSQL 18 backup, point-in-time recovery, and clean restore are demonstrated.
9. Hot artifacts tier from H: to E: without losing hashes or exact expansion.
10. No normal IDE receives direct PostgreSQL or Cognee credentials.
11. Every retrieval item carries source, scope, trust, timestamp, and provenance.
12. Per-IDE capture behavior is measured rather than assumed.
13. The engineering library improves deterministic AgentBench results.
14. One health command and one diagnostic bundle identify failures and corrective actions.
15. The main checkout and worktree cannot silently diverge in architectural authority.

---

## 16. Hard stops

Stop and request operator review if:

- the active checkout/branch is ambiguous;
- a stale plan is being treated as authority;
- live drive identity conflicts with this role map;
- a destructive command identifies a drive only by letter;
- PostgreSQL backup or restore rehearsal fails;
- the implementation uses a development Cognee release;
- MCP SDK v2 pre-release is selected for production;
- a custom LangGraph checkpointer is proposed without a proven gap;
- a second AgentCore vector/database engine is proposed without benchmark evidence;
- project context is promoted globally without approval;
- event capture is claimed without a client-specific integration test;
- AgentCore is coupled to vendor Swarm memory;
- normal agents can reach raw F: database paths or write E: archive paths;
- recovery depends on the operator manually repairing code or data.

---

## 17. Open facts that must be verified, not guessed

- The exact current filesystem, allocation unit, free space, BitLocker state, and health of every drive.
- The exact active PostgreSQL 16 state and cause of prior process termination.
- I: allocation-unit correction (512B → 64KB) is authorized by BLUEPRINT.md §4; I: is confirmed empty (2026-07-14 live check); execution is part of M1.
- H: is live with Bifrost runtime and must never be formatted; its allocation unit is already 64KB (verified 2026-07-14).
- The distinct value and final disposition of `context-fabric`.
- The lifecycle hooks available in each IDE and the measured capture percentage.
- The final localhost port allocation from the existing port registry.
- The final Cognee image/package digest and full transitive compatibility lock.
- Whether Cognigent already exists as local code or remains an AgentCore product-layer name.
- The off-machine/cloud backup target beyond E: and G:.

These are explicit work items. They must not be filled with assumptions.

