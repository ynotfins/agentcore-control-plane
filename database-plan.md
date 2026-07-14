# AgentCore Unified Memory Catalog and Context Router

**Document type:** Source-controlled design specification  
**Status:** Pre-migration — does not authorize live DB mutation  
**Sequencing:** Post-native-stability and pre-migration. Apply only AFTER native SwarmRecall/SwarmVault are green and AgentCore gateway/projector wrapper verification passes. `memory_catalog` and the `agentcore_*` tools described here do NOT exist yet; they are created only by the gated migration in §13 with operator sign-off.  
**Authority:** `D:\github\agentcore-control-plane` (canonical source)  
**Live ops root:** `D:\MCP-Control-Plane` (compatibility/evidence only)  
**Schema version:** 2026-06-30  
**Prerequisite reads:** `contracts/global-memory-database-contract.json`, `docs/database_overview.md`, `AGENTS.md`

> **HISTORICAL SCHEMA EVIDENCE ONLY — SUPERSEDED (2026-07-14). DO NOT IMPLEMENT.**
> This 2026-06-30 design targets PostgreSQL 16.6 + pgvector 0.8.2, keeps SwarmRecall/SwarmVault as
> active memory planes, mandates Swarm MCP in every IDE (§15.1, §18.10), and defines `memory_append`/
> `memory_search`/`memory_state` plus `agentcore_*` tool contracts that were never built.
> **The current implementation authority is `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`**
> (PostgreSQL 18 + pgvector, Cognee behind an AgentCore adapter, lossless evidence/context, locked
> Milestones M0–M8). The current non-Swarm IDE route is `agentcore-gateway` → `agentcore-memory` via
> Bifrost. Do not apply this document's schema, migrations, tool names, or Swarm memory planes.
> Retained as historical schema design evidence only.

---

## 1. Purpose and Scope

This document is the single source-controlled design authority for the AgentCore Unified Memory Catalog and Context Router.

### Problem Statement

Agents operating on CHAOSCENTRAL store knowledge across multiple independent backends: PostgreSQL/pgvector (`agent_core`), SwarmRecall (`swarmrecall` DB + Meilisearch), SwarmVault (local file/wiki/graph), and Obsidian. Without a unified catalog and retrieval gateway, a future agent cannot discover that related knowledge exists in another backend. It must know where to look before it can look.

### Goal

Design the future governed memory catalog/router (historically named `global-memory-gateway` in this pre-migration spec) as the canonical front door for memory reads and writes. Current non-Swarm IDE agents use `agentcore-gateway` → `agentcore-memory` until that migration is explicitly approved and implemented.

### Scope of This Document

- Proposed schema additions to `agent_core` PostgreSQL (DDL is specification only — not yet applied)
- Gateway tool contracts: confirmed current tools and target-contract tools to implement
- Source-system registry design
- Retrieval algorithm and fan-out order
- Catalog mirroring rules
- Fallback and pending-memory queue contracts
- Migration strategy with gates
- Validation strategy
- Agent rule contract
- Rollout-phase relationship

### Out of Scope for This Document

See Section 2 (Non-Goals).

---

## 2. Non-Goals

The following are explicitly out of scope for this specification and for any work that cites this document as authority:

- **No live DB mutation.** This document does not authorize SQL execution against `agent_core` or `swarmrecall`. All DDL shown is proposed design.
- **No migration files created.** Migration scripts are a future task.
- **No SwarmVault in Postgres.** SwarmVault primary state (`raw/`, `wiki/`, `state/`, `state/graph.json`, `state/retrieval/`, `state/context-packs/`, `state/memory/tasks/`) remains file-based on F:.
- **No collapse of** `agent_core` **and** `swarmrecall`**.** They are separate databases in the same cluster and must stay separate.
- **No primary SQL on E:.** E: is archive, cold storage, WAL backup target, and emergency memory spool only.
- **No LCM/lossless active backend.** LCM is a future source-system type only.
- **No monitor automations.** Drift checks and health checks are manual-validator-driven in this pass. No background polling, continuous re-audit loops, or automated projection monitors.
- **No hosted Swarm services.** All components are local-only.
- **No** `.env` **files.** Credentials are Windows environment variables only.
- **No dual-write by normal agents.** Normal IDE agents do not write independently to both `agent_core` and `swarmrecall`.

---

## 3. Authoritative Runtime/Storage Model

### 3.1 Machine Identity

```
Hostname:  CHAOSCENTRAL
OS:        Windows 11 Pro 10.0.26200
CPU:       Intel Core i9-14900KF, 24 cores / 32 threads
RAM:       128 GB DDR5
GPU:       NVIDIA RTX 4070 SUPER, 12 GB GDDR6X

```

### 3.2 Drive Role Map


| Drive | Role                                                      | Relevant paths                                         |
| ----- | --------------------------------------------------------- | ------------------------------------------------------ |
| C:    | OS, apps, user profile, IDE configs                       | `C:\Users\ynotf\.cursor\mcp.json` (live Cursor config) |
| D:    | Source repos, project folders, build evidence             | `D:\github\agentcore-control-plane` (source authority) |
| F:    | Hot local memory / RAG / database tier                    | All AgentCore runtime paths below                      |
| E:    | Archive, WAL, base backups, cold storage, emergency spool | `E:\AgentCoreArchive\`                                 |
| G:    | Backup target only                                        | —                                                      |


**Critical rule:** Do not create primary SQL databases on E:. Do not add hot AgentCore runtime data to C:. D: is source/code only; no DB cluster data on D:.

### 3.3 Active Runtime Services


| Component                        | Location                                                | Endpoint                              | Purpose                                                   |
| -------------------------------- | ------------------------------------------------------- | ------------------------------------- | --------------------------------------------------------- |
| PostgreSQL 16.6 + pgvector 0.8.2 | `F:\AgentCore\database_cluster\`                        | `127.0.0.1:55432`                     | Canonical structured memory spine                         |
| `agent_core` database            | same cluster                                            | port 55432                            | AgentCore canonical DB — governed memory                  |
| `swarmrecall` database           | same cluster                                            | port 55432                            | SwarmRecall local runtime DB — **separate, do not merge** |
| SwarmRecall API                  | `D:\github\vendor\swarm\swarmrecall`                    | `http://127.0.0.1:3300`               | Memory runtime API                                        |
| SwarmRecall health               | —                                                       | `http://127.0.0.1:3300/api/v1/health` | Liveness check                                            |
| Meilisearch                      | `F:\AgentCore\agentmemory\swarmrecall\meilisearch\data` | `http://127.0.0.1:7700`               | Full-text search for SwarmRecall                          |
| SwarmVault                       | `F:\AgentCore\agentmemory\swarmvault`                   | file-based (MCP stdio)                | Local-first RAG/wiki/graph/context-packs/task-ledger      |
| Projection state                 | `F:\AgentCore\agentmemory\projection-state\`            | —                                     | Fan-out checkpoint and per-entry status ledger            |
| global-memory-gateway            | `D:\Codex_Managed\.venv\...\global_memory_gateway.py`   | MCP stdio                             | Governed memory policy broker                             |
| Obsidian REST                    | `D:\Obsidian\Dungeon Vault\`                            | `https://127.0.0.1:27124`             | Human-authored notes (read via MCP)                       |


### 3.4 PostgreSQL Runtime Paths


| Item                   | Path                                                            |
| ---------------------- | --------------------------------------------------------------- |
| Cluster data directory | `F:\AgentCore\database_cluster\`                                |
| Engine binaries        | `F:\AgentCore\postgres_runtime_engine\pgsql\bin\`               |
| psql                   | `F:\AgentCore\postgres_runtime_engine\pgsql\bin\psql.exe`       |
| pg_isready             | `F:\AgentCore\postgres_runtime_engine\pgsql\bin\pg_isready.exe` |
| WAL archive            | `E:\AgentCoreArchive\backups_cold\pgvector\wal\`                |
| Base backup            | `E:\AgentCoreArchive\backups_cold\pgvector\base\`               |
| Startup task           | `\AgentCore\PostgresRuntime` (Task Scheduler, on logon)         |


### 3.5 PostgreSQL Roles


| Role           | Direct SQL       | Privileges                                    | Used by                                          |
| -------------- | ---------------- | --------------------------------------------- | ------------------------------------------------ |
| `agent_read`   | Yes, read-only   | `SELECT` only on approved tables              | Validators, projector reads                      |
| `agent_ingest` | Yes, constrained | `SELECT` + `INSERT` on approved memory tables | `global-memory-gateway`, approved ingest runners |
| `agent_admin`  | Yes, superuser   | Full                                          | Migrations, schema maintenance, backup/restore   |
| `postgres`     | Yes, superuser   | Full                                          | Break-glass maintenance only                     |


**Normal IDE agents must not connect directly to PostgreSQL.** Current non-Swarm IDE agents use `agentcore-gateway` → `agentcore-memory`; future memory catalog/router writes remain gated by this migration plan.

### 3.6 Credential Policy

AgentCore does not use `.env` files. All credentials are Windows User-scope environment variables.


| Variable                                  | Purpose                                                  |
| ----------------------------------------- | -------------------------------------------------------- |
| `AGENT_CORE_AGENT_READ_PASSWORD`          | `agent_read` role password                               |
| `AGENT_CORE_AGENT_INGEST_PASSWORD`        | `agent_ingest` role password                             |
| `AGENT_CORE_AGENT_ADMIN_PASSWORD`         | `agent_admin` role password                              |
| `AGENT_CORE_POSTGRES_PASSWORD`            | `postgres` superuser password                            |
| `AGENT_CORE_SWARMRECALL_API_KEY`          | SwarmRecall API bearer key                               |
| `AGENT_CORE_SWARMRECALL_MEILI_MASTER_KEY` | Meilisearch master key                                   |
| `OPENAI_API_KEY`                          | Embedding provider (preferred: `text-embedding-3-small`) |


Documentation may list variable names only — never values.

---

## 4. Memory Planes


| Plane                       | Backend                                      | Location                              | Write Policy                                               | Status                       |
| --------------------------- | -------------------------------------------- | ------------------------------------- | ---------------------------------------------------------- | ---------------------------- |
| Working context             | Gateway/agent session state                  | In-process                            | Session only; not persisted                                | Active                       |
| Canonical structured memory | PostgreSQL `agent_core`                      | `F:\AgentCore\database_cluster\`      | `global-memory-gateway` via `agent_ingest` only            | Active                       |
| Vector catalog              | pgvector `global_vector_memory_store`        | `agent_core`                          | Gateway write via `memory_append`                          | Active                       |
| Semantic recall             | SwarmRecall (`swarmrecall` DB + Meilisearch) | F: cluster + F: Meilisearch data      | Projector → SwarmRecall API; no direct agent write         | Active                       |
| Local RAG / knowledge       | SwarmVault file system                       | `F:\AgentCore\agentmemory\swarmvault` | Projector curated ingest; no direct agent filesystem write | Active                       |
| Human notes                 | Obsidian                                     | `D:\Obsidian\Dungeon Vault\`          | `obsidian-vault` MCP REST only (`:27124`); single writer   | Active                       |
| Unified memory catalog      | PostgreSQL `agent_core` (new tables)         | `agent_core`                          | Gateway write; projector updates                           | **Target — not yet created** |
| LCM/lossless history        | —                                            | —                                     | —                                                          | **Deferred**                 |


### Memory Plane Rules

1. Normal agents write only through `global-memory-gateway`.
2. The projector is the only component that fans canonical `agent_core` memory into SwarmRecall and SwarmVault.
3. SwarmVault state must not be replicated into Postgres as primary storage.
4. `agent_core` and `swarmrecall` databases must not be merged.
5. Obsidian writes must go through the `obsidian-vault` MCP REST path only — never via filesystem MCP while Obsidian is running.

---

## 5. Canonical Write/Read Flow

### 5.1 Write Flow (Current — Active)

```
Normal IDE Agent
  │
  ▼
global-memory-gateway MCP
  │  (memory_append tool — existing)
  ▼
agent_ingest role → agent_core.global_vector_memory_store
  │
  ▼  (scheduled every 2 hours)
Invoke-AgentCoreMemoryProjector.ps1
  ├─► SwarmRecall API  http://127.0.0.1:3300  POST /api/v1/memory
  │     └─► swarmrecall database (separate) + Meilisearch :7700
  └─► SwarmVault curated ingest (governed subset only)
        └─► F:\AgentCore\agentmemory\swarmvault  (file-based)

```

**What is forbidden — normal agent path:**

- Normal agent → SwarmRecall API directly (bypasses governance)
- Normal agent → raw SQL `INSERT`/`UPDATE` on `agent_core` or `swarmrecall`
- Normal agent dual-writing to both `agent_core` and `swarmrecall` independently
- Collapsing `agent_core` and `swarmrecall` into one database
- Any agent write to `F:\AgentCore\agentmemory\` filesystem paths directly

### 5.2 Write Flow (Target — Requires New Tables and Tool Implementation)

```
Normal IDE Agent
  │
  ▼
global-memory-gateway MCP
  │  (agentcore_store_memory tool — TARGET; wraps memory_append)
  ▼
agent_ingest role
  ├─► agent_core.global_vector_memory_store  (existing)
  └─► agent_core.memory_catalog              (target — pointer record)
        │
        ▼  (projector, every 2h)
  ├─► SwarmRecall API → swarmrecall DB + Meilisearch
  └─► SwarmVault curated ingest

```

### 5.3 Read Flow (Current — Active)

```
Normal IDE Agent
  ├─► memory_search (gateway, existing) → global_vector_memory_store pgvector
  ├─► swarmrecall MCP → SwarmRecall API → swarmrecall DB + Meilisearch
  └─► swarmvault MCP → SwarmVault query/context-pack

```

### 5.4 Read Flow (Target — Requires New Tables and Tool Implementation)

```
Normal IDE Agent
  │
  ▼
agentcore_retrieve_context(project_id, query, task_type, privacy_zone, token_budget)
  [TARGET TOOL — not yet implemented]
  │
  ├─► 1. agent_core.system_info          global static facts (exists)
  ├─► 2. agent_core.project_facts        project-scoped facts (exists)
  ├─► 3. agent_core.global_vector_memory_store  pgvector cosine search (exists)
  ├─► 4. agent_core.memory_catalog       pointer lookup → backend discovery (target)
  ├─► 5. SwarmRecall API :3300           semantic recall search (exists)
  ├─► 6. SwarmVault MCP                  RAG / context-pack / graph query (exists)
  └─► 7. Obsidian MCP :27124             handoff note search (exists)
        │
        ▼
  rerank by: relevance score, recency decay, confidence, source authority, privacy zone
        │
        ▼
  deduplicate by source_uri / external_id
        │
        ▼
  trim to token_budget
        │
        ▼
  bounded context pack → agent
  memory_retrieval_events row written (target)

```

Until `memory_catalog` exists and `agentcore_retrieve_context` is implemented, agents use `memory_search` and SwarmRecall/SwarmVault MCP tools directly.

---

## 6. Schema Design

### 6.1 Existing Tables (Preserved Unchanged)


| Table                           | Description                                                                            |
| ------------------------------- | -------------------------------------------------------------------------------------- |
| `global_vector_memory_store`    | Canonical current vector memory; written by `global-memory-gateway` via `agent_ingest` |
| `agent_cross_project_telemetry` | Gateway, ingest, and validation telemetry                                              |
| `system_info`                   | Keyed local system facts (PC hardware, drive roles, env-var policy)                    |
| `projects`                      | Project identity and root paths                                                        |
| `project_facts`                 | Versioned immutable project facts and drift records                                    |
| `messages`                      | Episodic events and summaries                                                          |
| `embeddings`                    | Normalized embedding records linked to projects/messages                               |


These tables must not be altered by migrations implementing this specification. New tables are additive only.

### 6.2 Embedding Contract


| Setting            | Value                                                                              |
| ------------------ | ---------------------------------------------------------------------------------- |
| Default provider   | `auto`                                                                             |
| Preferred provider | `openai_text_embedding_3_small` (when `OPENAI_API_KEY` available)                  |
| Preferred model    | `text-embedding-3-small`                                                           |
| Dimensions         | 1536                                                                               |
| Index type         | HNSW                                                                               |
| Distance metric    | Cosine                                                                             |
| Fallback provider  | `local_hash_v1` (offline fallback only)                                            |
| Upgrade path       | Replace provider behind the governed gateway without changing agent tool contracts |


### 6.3 New Tables (Proposed — DDL is Specification Only)

All new tables live in the `agent_core` database. All migrations are additive and must not modify existing tables.

---

#### `memory_source_systems`

Registry of all known backend stores. Each source system is identified by a stable slug.

```sql
CREATE TABLE memory_source_systems (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            text        NOT NULL UNIQUE,   -- 'postgres', 'swarmrecall', 'swarmvault', etc.
    display_name    text        NOT NULL,
    endpoint_uri    text,                          -- base URL or path; no credentials
    adapter_notes   text,                          -- implementation notes for the gateway adapter
    is_active       boolean     NOT NULL DEFAULT true,
    is_deferred     boolean     NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_mss_slug ON memory_source_systems (slug);

```

---

#### `memory_catalog`

Pointer and provenance record for every cataloged artifact across all backends. Postgres stores the pointer, summary, and embedding — not the raw artifact itself.

```sql
CREATE TABLE memory_catalog (
    id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id       uuid        REFERENCES projects(id) ON DELETE SET NULL,
                                 -- nullable for global/cross-project facts
    source_system    text        NOT NULL REFERENCES memory_source_systems(slug),
    source_uri       text        NOT NULL,  -- exact path / memory-id / URL / tool ref in the backend
    external_id      text,                  -- backend-native ID (e.g. SwarmRecall memory UUID)
    memory_type      text        NOT NULL,  -- 'fact' | 'decision' | 'source' | 'context_pack' |
                                            -- 'transcript' | 'run' | 'incident' | 'doc' | 'handoff'
    title            text        NOT NULL,
    summary          text,                  -- short distillation; Postgres does NOT store raw content
    tags             text[]      NOT NULL DEFAULT '{}',
    privacy_zone     text        NOT NULL DEFAULT 'project-private',
                                            -- 'public' | 'project-private' | 'operator-only'
    confidence       numeric(4,3) NOT NULL DEFAULT 0.8
                                    CHECK (confidence BETWEEN 0 AND 1),
    content_hash     text,                  -- SHA-256 of source content when available
    embedding        vector(1536),          -- pgvector embedding of summary
    embedding_provider text,               -- 'openai_text_embedding_3_small' | 'local_hash_v1'
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now(),
    last_verified_at timestamptz,

    CONSTRAINT ck_mc_privacy_zone
        CHECK (privacy_zone IN ('public', 'project-private', 'operator-only')),
    CONSTRAINT ck_mc_memory_type
        CHECK (memory_type IN (
            'fact', 'decision', 'source', 'context_pack',
            'transcript', 'run', 'incident', 'doc', 'handoff', 'skill'
        )),
    CONSTRAINT uq_mc_source
        UNIQUE (source_system, source_uri)
);

CREATE INDEX idx_mc_project_id       ON memory_catalog (project_id);
CREATE INDEX idx_mc_source_system    ON memory_catalog (source_system);
CREATE INDEX idx_mc_memory_type      ON memory_catalog (memory_type);
CREATE INDEX idx_mc_privacy_zone     ON memory_catalog (privacy_zone);
CREATE INDEX idx_mc_created_at       ON memory_catalog (created_at DESC);
CREATE INDEX idx_mc_embedding        ON memory_catalog
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

```

**Key design rules:**

- Postgres stores pointers, summaries, provenance, hashes, confidence, privacy zones, and embeddings.
- Postgres must not duplicate raw SwarmVault pages, Obsidian note bodies, or full SwarmRecall memory content.
- One row per `(source_system, source_uri)` pair — the unique constraint enforces this.

---

#### `memory_retrieval_events`

Audit record for each context retrieval call. Provides the learning loop for quality improvement.

```sql
CREATE TABLE memory_retrieval_events (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid        REFERENCES projects(id) ON DELETE SET NULL,
    agent_id            text,
    run_id              text,
    query_text          text,
    task_type           text,       -- 'general' | 'architecture' | 'debug' | 'cross_project_research'
    privacy_zone        text        NOT NULL DEFAULT 'project-private',
    token_budget        int,
    sources_searched    text[]      NOT NULL DEFAULT '{}',  -- slugs of backends queried
    sources_used        text[]      NOT NULL DEFAULT '{}',  -- slugs that contributed items
    items_returned      int         NOT NULL DEFAULT 0,
    token_count_used    int,
    retrieval_latency_ms int,
    context_pack_id     uuid        REFERENCES context_packs(id) ON DELETE SET NULL,
    embedding_provider  text,
    embedding_fallback  boolean     NOT NULL DEFAULT false,
    missing_info_flags  text[],
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_mre_project_id  ON memory_retrieval_events (project_id);
CREATE INDEX idx_mre_agent_id    ON memory_retrieval_events (agent_id);
CREATE INDEX idx_mre_run_id      ON memory_retrieval_events (run_id);
CREATE INDEX idx_mre_created_at  ON memory_retrieval_events (created_at DESC);

```

---

#### `context_packs`

Named, bounded context assemblies built by the retrieval algorithm or by `agentcore_build_handoff_pack`.

```sql
CREATE TABLE context_packs (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      uuid        REFERENCES projects(id) ON DELETE SET NULL,
    name            text,                   -- optional human label, e.g. 'handoff-20260630'
    task_type       text,
    privacy_zone    text        NOT NULL DEFAULT 'project-private',
    token_count     int,
    build_latency_ms int,
    sources_used    text[]      NOT NULL DEFAULT '{}',
    quality_score   numeric(4,3),           -- populated by agent_quality_scores join or inline
    created_by      text,                   -- 'gateway' | 'projector' | 'operator'
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_cp_project_id ON context_packs (project_id);
CREATE INDEX idx_cp_created_at ON context_packs (created_at DESC);

```

---

#### `context_pack_items`

Individual items composing a context pack, with source attribution.

```sql
CREATE TABLE context_pack_items (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    context_pack_id uuid        NOT NULL REFERENCES context_packs(id) ON DELETE CASCADE,
    catalog_id      uuid        REFERENCES memory_catalog(id) ON DELETE SET NULL,
    source_system   text        NOT NULL,
    source_uri      text        NOT NULL,
    memory_type     text,
    title           text,
    excerpt         text,           -- brief excerpt injected into context; not full content
    relevance_score numeric(5,4),
    rank_position   int,
    token_count     int,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_cpi_pack_id    ON context_pack_items (context_pack_id);
CREATE INDEX idx_cpi_catalog_id ON context_pack_items (catalog_id);

```

---

#### `agent_run_ledger`

Per-agent-run audit entry. Records task, tools used, files changed, tests run, errors, result, and follow-up flags.

```sql
CREATE TABLE agent_run_ledger (
    id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id           text        NOT NULL UNIQUE,
    project_id       uuid        REFERENCES projects(id) ON DELETE SET NULL,
    agent_id         text,
    ide_platform     text,           -- 'cursor' | 'codex' | 'openclaw' | 'minimax' | 'claude' | etc.
    task_summary     text,
    tools_used       text[]      NOT NULL DEFAULT '{}',
    files_changed    text[]      NOT NULL DEFAULT '{}',
    tests_run        text[]      NOT NULL DEFAULT '{}',
    errors           text[],
    result           text,           -- 'completed' | 'partial' | 'failed' | 'blocked'
    pr_url           text,
    follow_up_needed boolean     NOT NULL DEFAULT false,
    durable_lessons  text[],
    source_evidence  text[],         -- paths to evidence files in D:\AgentSwarm\runs\<run_id>\
    created_at       timestamptz NOT NULL DEFAULT now(),
    completed_at     timestamptz
);

CREATE INDEX idx_arl_project_id ON agent_run_ledger (project_id);
CREATE INDEX idx_arl_agent_id   ON agent_run_ledger (agent_id);
CREATE INDEX idx_arl_created_at ON agent_run_ledger (created_at DESC);

```

---

#### `agent_quality_scores`

Retrieval and context quality scoring. Feeds the learning loop for improving retrieval ranking.

```sql
CREATE TABLE agent_quality_scores (
    id                   uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    context_pack_id      uuid        REFERENCES context_packs(id) ON DELETE CASCADE,
    retrieval_event_id   uuid        REFERENCES memory_retrieval_events(id) ON DELETE CASCADE,
    run_id               text        REFERENCES agent_run_ledger(run_id) ON DELETE SET NULL,
    answer_usefulness    numeric(4,3),   -- 0.0–1.0 if available; null if not assessed
    hallucination_flag   boolean     NOT NULL DEFAULT false,
    drift_flag           boolean     NOT NULL DEFAULT false,
    missing_info_flag    boolean     NOT NULL DEFAULT false,
    notes                text,
    scored_by            text,           -- 'agent_self' | 'validator' | 'operator'
    created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_aqs_pack_id           ON agent_quality_scores (context_pack_id);
CREATE INDEX idx_aqs_retrieval_event   ON agent_quality_scores (retrieval_event_id);

```

---

## 7. Source-System Registry

Initial seed rows for `memory_source_systems`. Applied as part of the same migration transaction that creates the table; does not constitute a separate migration.


| slug             | display_name          | endpoint_uri                          | is_active | is_deferred | notes                                                               |
| ---------------- | --------------------- | ------------------------------------- | --------- | ----------- | ------------------------------------------------------------------- |
| `postgres`       | AgentCore PostgreSQL  | `127.0.0.1:55432/agent_core`          | true      | false       | Canonical `agent_core` DB; adapter uses `agent_read` role           |
| `swarmrecall`    | SwarmRecall Local API | `http://127.0.0.1:3300`               | true      | false       | `swarmrecall` DB + Meilisearch; accessed via API, not direct SQL    |
| `swarmvault`     | SwarmVault Local      | `F:\AgentCore\agentmemory\swarmvault` | true      | false       | File-based; accessed via SwarmVault MCP or CLI                      |
| `obsidian`       | Obsidian Vault REST   | `https://127.0.0.1:27124`             | true      | false       | `OBSIDIAN_API_KEY` env var; single-writer REST                      |
| `context-fabric` | Context Fabric        | repo-local `.context-fabric/`         | true      | false       | Repo continuity; accessed via context-fabric MCP                    |
| `git`            | Git Source            | repo-local                            | true      | false       | Current source state; read via filesystem or context-fabric         |
| `manual`         | Operator-Authored     | —                                     | true      | false       | Human-written facts ingested through `agentcore_store_project_fact` |
| `lcm`            | LCM / Lossless Memory | —                                     | false     | true        | **Deferred** — no live service; schema reserves the slug            |


---

## 8. Gateway Tool Contracts

### 8.1 Current Confirmed Tools (Exist Now)

These tools are live in `global-memory-gateway` and available to all managed IDE agents.

#### `memory_append`

Governed write to `global_vector_memory_store` via `agent_ingest` role.

```
Input:
  content        string   -- concise summary or fact; not raw transcript
  metadata       object   -- must include: user_id, app_id, agent_id, run_id, platform,
                             associated_project_path, document_source, source_kind, storage_contract
Output:
  id             uuid     -- row ID in global_vector_memory_store
  created_at     timestamptz

```

**Rules:**

- `storage_contract` must be `"mcp-control-plane.global-memory.v1"`
- Content must not include raw secrets, tokens, passwords, or credentials
- Content must be concise; full transcripts must be summarized before append

#### `memory_search`

Vector search against `global_vector_memory_store` using pgvector cosine similarity.

```
Input:
  query          string   -- natural language search query
  limit          int      -- default 10; max 50
  project_path   string   -- optional; filters by associated_project_path
Output:
  results[]
    id           uuid
    content_chunk string
    agent_signature string
    associated_project_path string
    document_source string
    similarity   float
    created_at   timestamptz

```

#### `memory_state`

Returns gateway health and connection status.

```
Input:  (none)
Output:
  status         string   -- 'ok' | 'degraded' | 'error'
  postgres       object   -- { connected: bool, host, port, database }
  embedding      object   -- { provider, model, dimensions, fallback_active: bool }

```

---

### 8.2 Target-Contract Tools (To Implement)

These tools do not yet exist as confirmed gateway tools. They are the implementation target for the gateway enhancement described in this specification. All require the new tables in Section 6 to be created first.

---

#### `agentcore_get_startup_context(project_id)`

Returns a structured startup context block for the given project. Called at the start of every non-trivial agent task.

```
Input:
  project_id     string   -- project slug or UUID; required

Output:
  pc_facts       object
    hostname     string            -- "CHAOSCENTRAL"
    drive_layout object            -- C/D/E/F/G roles
    ram_gb       int               -- 128
    cpu          string
    env_var_policy string          -- "Windows environment variables only; no .env files"
  memory_architecture object
    canonical_db string            -- "agent_core @ 127.0.0.1:55432"
    swarmrecall_api string         -- "http://127.0.0.1:3300"
    swarmvault_root string         -- "F:\AgentCore\agentmemory\swarmvault"
    embedding_provider string
  project_facts  object[]          -- current is_current=true rows from project_facts
    fact_key     string
    fact_value   object
    source       string
    confidence   float
  privacy_rules  object
    privacy_zone string
    cross_project_allowed bool     -- always false unless operator policy overrides
  agent_rules    string[]          -- required behavior rules for this agent session

```

**Behavior:**

- Reads `system_info`, `projects`, and `project_facts` from `agent_core` via `agent_read`
- Never performs a write
- Does not call external services; reads only from Postgres
- Returns static facts that anchor every agent session to the correct machine topology

---

#### `agentcore_retrieve_context(project_id, query, task_type, privacy_zone, token_budget)`

Fan-out retrieval across all active backends. Reranks, deduplicates, trims to token budget, and returns a bounded context pack.

```
Input:
  project_id     string           -- required; scopes retrieval to this project
  query          string           -- natural language description of what the agent needs
  task_type      string           -- 'general' | 'architecture' | 'debug' |
                                     'cross_project_research'
  privacy_zone   string           -- 'public' | 'project-private' | 'operator-only'
                                  -- agent receives only items at or below this zone
  token_budget   int              -- max tokens to include in returned context pack

Output:
  context_pack_id uuid            -- ID in context_packs table
  items          object[]
    source_system  string
    source_uri     string
    memory_type    string
    title          string
    excerpt        string
    relevance_score float
    rank_position  int
  sources_searched string[]
  sources_used     string[]
  token_count      int
  retrieval_latency_ms int
  embedding_fallback bool

```

**Behavior:**

- Step 1: Load `system_info` global static facts
- Step 2: Load `project_facts` for `project_id`
- Step 3: pgvector cosine search on `global_vector_memory_store` with project filter
- Step 4: pgvector cosine search on `memory_catalog` with project and privacy filter
- Step 5: Fan out to backends indicated by catalog pointers (SwarmRecall API search, SwarmVault MCP query, Obsidian MCP search)
- Step 6: Deduplicate by `(source_system, source_uri)`
- Step 7: Rerank by: pgvector similarity score, recency decay (log scale), confidence, source authority tier (postgres > swarmrecall > swarmvault > obsidian > git), privacy zone enforcement
- Step 8: Trim to `token_budget`; prefer higher-ranked items
- Step 9: Write `context_packs` and `context_pack_items` rows
- Step 10: Write `memory_retrieval_events` row

**Privacy enforcement:**

- Items tagged `project-private` for project B are never returned when `project_id` = project A
- Items tagged `operator-only` are never returned to any normal agent tool call
- `cross_project_research` task_type required to receive results from projects other than `project_id`

---

#### `agentcore_store_memory(project_id, concise_summary, memory_type, sources, privacy_zone)`

Gateway-routed durable memory write. Wraps and extends `memory_append` with richer routing logic.

```
Input:
  project_id       string     -- required; null only for global static facts
  concise_summary  string     -- 1–5 sentence distillation; not raw transcript
  memory_type      string     -- 'fact' | 'decision' | 'doc' | 'run' | 'handoff' | 'skill'
  sources          string[]   -- source slugs where this memory originated
  privacy_zone     string     -- 'public' | 'project-private' | 'operator-only'

Output:
  memory_id        uuid       -- ID in global_vector_memory_store
  catalog_id       uuid       -- ID in memory_catalog (target)
  status           string     -- 'stored' | 'pending' | 'failed'
  embedding_provider string

```

**Behavior:**

- Pre-checks: scan for secrets (API keys, bearer tokens, passwords, private keys) — refuse if detected
- Writes to `global_vector_memory_store` via `agent_ingest`
- Creates or updates `memory_catalog` pointer row
- Does not write directly to SwarmRecall API; the projector handles downstream fan-out
- If Postgres is unavailable: writes to local pending-memory spool (`F:\AgentCore\agentmemory\pending-memory\`) and returns `status: 'pending'`

---

#### `agentcore_store_project_fact(project_id, fact, confidence, source)`

Versioned write to `project_facts`. Supersedes any existing fact with the same `fact_key`.

```
Input:
  project_id   string     -- required
  fact         object     -- { key: string, value: any }
  confidence   float      -- 0.0–1.0
  source       string     -- 'agent' | 'operator' | 'validator' | 'contract'

Output:
  fact_id      uuid       -- new fact row ID
  superseded   uuid       -- previous fact row ID, if any

```

**Behavior:**

- Sets `is_current = false` on previous fact with same `fact_key` for this project
- Inserts new row with `is_current = true`
- Writes only through `agent_ingest`

---

#### `agentcore_build_handoff_pack(project_id, task)`

Builds a named, saved context pack for handoff to another agent or session.

```
Input:
  project_id   string     -- required
  task         string     -- description of the task the receiving agent will continue

Output:
  context_pack_id uuid
  name            string   -- auto-generated, e.g. 'handoff-20260630-task-slug'
  items           object[] -- same structure as agentcore_retrieve_context items
  token_count     int

```

**Behavior:**

- Calls retrieval algorithm internally with `task_type='general'` and broad token budget
- Adds project facts, active run ledger entries, and recent retrieval events
- Saves result as a named `context_packs` row for later retrieval by `agentcore_explain_sources`

---

#### `agentcore_find_related_projects(query)`

Cross-project vector search. Returns projects whose facts and catalog entries match the query.

```
Input:
  query        string     -- natural language description of the capability or pattern sought

Output:
  projects     object[]
    project_id   uuid
    project_key  string
    root_path    string
    match_score  float
    matched_facts object[]
    matched_catalog_items object[]

```

**Behavior:**

- Requires `task_type = 'cross_project_research'` intent; blocked by default for normal queries
- Searches `memory_catalog` with no project_id filter but with `privacy_zone = 'public'` only
- Never returns `project-private` or `operator-only` data from another project
- Result is informational only; the calling agent must then call `agentcore_retrieve_context` scoped to the target project

---

#### `agentcore_explain_sources(context_pack_id)`

Returns full provenance chain for every item in a context pack.

```
Input:
  context_pack_id  uuid

Output:
  pack             object     -- context_packs row
  items            object[]
    rank_position  int
    source_system  string
    source_uri     string
    catalog_id     uuid
    memory_type    string
    title          string
    excerpt        string
    relevance_score float
    last_verified_at timestamptz
    confidence     float
    tags           string[]
  retrieval_event  object     -- linked memory_retrieval_events row if present

```

---

## 9. Retrieval Algorithm

### 9.1 Fan-Out Order

The following ordered fan-out applies to `agentcore_retrieve_context`. Steps execute in parallel where possible; steps that require preceding results (e.g., catalog pointer lookup before backend fan-out) are sequential.


| Step | Source                       | Method                                           | Existing?  |
| ---- | ---------------------------- | ------------------------------------------------ | ---------- |
| 1    | `system_info`                | Direct SQL read                                  | Yes        |
| 2    | `project_facts`              | Direct SQL read                                  | Yes        |
| 3    | `global_vector_memory_store` | pgvector cosine search, project filter           | Yes        |
| 4    | `memory_catalog`             | pgvector cosine search, project + privacy filter | Target     |
| 5a   | SwarmRecall API              | `POST /api/v1/memory/search`                     | Yes        |
| 5b   | SwarmVault MCP               | `query_vault` / `build_context_pack`             | Yes        |
| 5c   | Obsidian MCP                 | Note search via REST                             | Yes        |
| 6    | Deduplication                | By `(source_system, source_uri)`                 | In-gateway |
| 7    | Reranking                    | Weighted score (see 9.2)                         | In-gateway |
| 8    | Token trimming               | Greedy fill to `token_budget`                    | In-gateway |
| 9    | Write context pack           | `context_packs` + `context_pack_items`           | Target     |
| 10   | Write retrieval event        | `memory_retrieval_events`                        | Target     |


### 9.2 Reranking Formula

```
final_score = (0.40 * semantic_similarity)
            + (0.25 * recency_score)
            + (0.20 * confidence)
            + (0.15 * source_authority)

```

**Semantic similarity:** pgvector cosine similarity (0.0–1.0) or SwarmRecall relevance score normalized to 0–1.

**Recency score:** `1 / (1 + log(1 + days_since_created))` — decays slowly; recent items score higher.

**Confidence:** value from `memory_catalog.confidence` (0.0–1.0); defaults to 0.8 for items without a catalog record.

**Source authority tier:**


| Source                                  | Authority score |
| --------------------------------------- | --------------- |
| `postgres` (project_facts, system_info) | 1.00            |
| `swarmrecall`                           | 0.80            |
| `swarmvault`                            | 0.75            |
| `obsidian`                              | 0.70            |
| `context-fabric` / `git`                | 0.65            |
| `manual`                                | 0.60            |
| `lcm` (deferred)                        | 0.50            |


### 9.3 Privacy Filter (Applied Before Reranking)

Privacy filtering is not optional and applies before any scoring:

1. Items with `privacy_zone = 'operator-only'` are always excluded from normal agent tool responses.
2. Items with `privacy_zone = 'project-private'` where `project_id != requesting_project_id` are excluded unless `task_type = 'cross_project_research'`.
3. Cross-project research is disabled by default; enabling it requires explicit `task_type` value and is logged in `memory_retrieval_events`.

---

## 10. Project Isolation and Privacy

### 10.1 Isolation Rules

- Every catalog query, retrieval call, and stored memory must include a `project_id` unless the item is explicitly a global static fact (`project_id IS NULL`).
- Global static facts (`privacy_zone = 'public'`, `project_id IS NULL`) are available to all agents.
- Project-private facts are scoped to the owning project only.
- Operator-only data is never exposed through any normal agent tool.

### 10.2 Privacy Zone Definitions


| Zone              | Description                                                     | Accessible by                              |
| ----------------- | --------------------------------------------------------------- | ------------------------------------------ |
| `public`          | Global facts, architecture docs, system topology                | All agents, all projects                   |
| `project-private` | Project-specific decisions, facts, run history                  | Agents operating on the same project       |
| `operator-only`   | Sensitive operational data, incident records, security findings | Admin paths only; never normal agent tools |


### 10.3 Cross-Project Research Policy

- Disabled by default.
- Enabled per-call when `task_type = 'cross_project_research'`.
- Even when enabled: only `public` items from other projects are returned.
- All cross-project retrievals are logged in `memory_retrieval_events` with `task_type = 'cross_project_research'`.

### 10.4 First-Responder / Sensitive Domain Data

Structured private incident data (unit status, dispatch workflow templates, jurisdiction rules, audit logs) belongs in relational Postgres tables with `privacy_zone = 'operator-only'`. It must never be placed in SwarmVault RAG files or `memory_catalog` rows accessible to normal agents.

---

## 11. Catalog Mirroring Rules

The memory catalog is kept consistent by the following mirroring rules. These rules describe how `memory_catalog` rows are created or updated when backend artifacts are written.

### 11.1 `global_vector_memory_store` → `memory_catalog`

**Trigger:** Projector run (`Invoke-AgentCoreMemoryProjector.ps1`), every 2 hours.

**Action:** For each row in `global_vector_memory_store` that the projector processes, create or upsert a `memory_catalog` row with:

- `source_system = 'postgres'`
- `source_uri = 'agent_core.global_vector_memory_store:' || id::text`
- `external_id = id::text`
- `summary` = first 500 chars of `content_chunk`
- `tags` derived from `agent_signature`, `associated_project_path`, `document_source`, `metadata.source_kind`
- `embedding` re-used from existing pgvector row if available

### 11.2 SwarmRecall → `memory_catalog`

**Trigger:** Projector run, after successful `POST /api/v1/memory` response.

**Action:** Create or upsert `memory_catalog` row with:

- `source_system = 'swarmrecall'`
- `source_uri = 'swarmrecall:' || returned_memory_id`
- `external_id = returned_memory_id`
- `summary` from projected content
- `project_id` from metadata if available

### 11.3 SwarmVault → `memory_catalog`

**Trigger:** Projector run, after successful SwarmVault ingest.

**Action:** Create or upsert `memory_catalog` row with:

- `source_system = 'swarmvault'`
- `source_uri = 'swarmvault:' || relative_vault_path`
- `memory_type` = `'source'` for raw ingest; `'doc'` for wiki pages
- `summary` from frontmatter or first paragraph

### 11.4 Obsidian → `memory_catalog`

**Trigger:** Manual / operator-triggered. The Obsidian adapter does not run automatically.

**Action:** Operator calls `agentcore_store_memory(...)` with `sources=['obsidian']` after writing an Obsidian handoff note. The gateway creates the `memory_catalog` row with:

- `source_system = 'obsidian'`
- `source_uri = 'obsidian:' || vault_relative_path`
- `memory_type = 'handoff'`

Automatic Obsidian mirroring is a **deferred** enhancement.

### 11.5 LCM → `memory_catalog`

**Deferred.** The `memory_catalog` schema reserves `source_system = 'lcm'` and `memory_source_systems` seeds a `is_deferred = true` row. No mirroring logic is implemented until a live LCM service is confirmed.

---

## 12. Local Fallback and Pending-Memory Queue

Three distinct fallback layers are defined. Each has a different status.

### 12.1 Projection-State Retry (Existing — Live Behavior)

`Invoke-AgentCoreMemoryProjector.ps1` maintains a checkpoint/entry ledger at:

```
F:\AgentCore\agentmemory\projection-state\
  summary.json           -- checkpoint cursor and aggregate totals
  entries\<uuid>.json    -- per-row status: pending | projected | skipped | failed

```

If the SwarmRecall API (`http://127.0.0.1:3300`) is unreachable during a projection run:

- The row entry status remains `pending` or transitions to `failed`
- The projector does not advance the checkpoint cursor past the failed entry
- The next scheduled run (every 2 hours) retries from the last successful checkpoint
- Failures are not silently discarded

If SwarmVault ingest fails:

- The row entry `swarmvault.status` = `failed`
- Projector continues with SwarmRecall projection for other rows
- SwarmVault retry occurs on next run via the same checkpoint mechanism

This is **current live behavior**, not a new design.

### 12.2 Pending-Memory Local Spool (Planned Fallback Contract — Not Yet Implemented)

```
Path:    F:\AgentCore\agentmemory\pending-memory\
Format:  One JSON file per pending event; filename = <uuid>.json

```

**Scenario:** `global-memory-gateway` receives a `memory_append` / `agentcore_store_memory` call but `agent_core` Postgres is momentarily unavailable (e.g., startup race condition, brief maintenance) while F: is healthy.

**Contract (target behavior when implemented):**

- Gateway writes a pending event JSON file with full provenance to `F:\AgentCore\agentmemory\pending-memory\`
- Returns `status: 'pending'` to the calling agent
- Events in this spool are **not committed to canonical memory** — they are queued
- Replay occurs only through the governed gateway path once Postgres is available — never by direct agent action
- No agent may read or alter files in `pending-memory\` directly
- Pending events older than a configurable retention period (default: 72 hours) without successful replay must be flagged for operator review

### 12.3 Emergency Archive Spool (Planned Fallback Contract — Not Yet Implemented)

```
Path:    E:\AgentCoreArchive\memory-spool\pending\
Format:  One JSON file per event; filename = <uuid>.json

```

**Scenario:** Both Postgres (F:) and the F: pending-memory spool are unavailable (e.g., F: drive failure during a write).

**Contract (target behavior when implemented):**

- E: is archive/cold storage — this path is emergency overflow only, never primary
- Events spooled here require explicit operator review and governed replay before becoming canonical
- The spool directory must never be used for normal write buffering
- Replay through governed services is mandatory; no direct SQL import from spool files

### 12.4 Embedding Fallback (Existing — Live Behavior)

- If `OPENAI_API_KEY` is not available: gateway uses `local_hash_v1` embedding provider
- Retrieval events and catalog rows are flagged with `embedding_provider = 'local_hash_v1'`
- Quality of vector search is degraded when using hash fallback; operator should be notified

### 12.5 Meilisearch Unavailability (Existing SwarmRecall Behavior)

- SwarmRecall falls back to Postgres-only search within its `swarmrecall` database when Meilisearch is unreachable
- Does not affect `agent_core` writes
- `memory_retrieval_events` should flag `sources_used` as excluding `meilisearch` in this condition

---

## 13. Migration Strategy

**This document does not authorize live DB mutation.**

All DDL in Section 6 is proposed design. No migration files are created in this pass. No SQL is applied against any running database.

### 13.1 Pre-Migration Gates

All gates must pass before any migration file is written or executed.


| Gate                 | Action                                                        | Tool                                 |
| -------------------- | ------------------------------------------------------------- | ------------------------------------ |
| Backup gate          | Run full base backup                                          | `Backup-AgentCorePostgres.ps1`       |
| Restore verification | Verify backup restores cleanly into `agent_core_restore_test` | `Test-AgentCorePostgresRestore.ps1`  |
| Service health       | Confirm Postgres, SwarmRecall API, Meilisearch all healthy    | `Test-AgentCoreSwarmRecall.ps1`      |
| Dirty-state check    | Confirm no active write sessions or pending projector runs    | `Test-AgentCoreMemoryProjection.ps1` |


### 13.2 Migration Execution Protocol (Future)

When a future operator is ready to execute:

1. **Dry-run gate:** Run each migration SQL block in a transaction ending with explicit `ROLLBACK`. Verify syntax, constraint compatibility, index creation messages, and no error output.
2. **Human approval gate:** Operator reviews dry-run output, confirms expected table count and constraint list, and provides explicit sign-off in the commit message or a linked approval record.
3. **Execute gate:** Run migration in a transaction. After all DDL succeeds, verify:
  - All new tables exist: `\dt memory_`*, `\dt context_*`, `\dt agent_*`
  - All indexes exist: `\di idx_mc_*`, `\di idx_mre_*`, etc.
  - Row counts on existing tables are unchanged
  - `COMMIT` only after all verifications pass.
4. **Post-migration validation:** Run `Test-AgentCoreMemoryProjection.ps1` and `Test-AgentCoreSwarmRecall.ps1` to confirm existing functionality is unaffected.
5. **Rollback:** Each migration file must include a `-- down:` block. The down block must be tested in `agent_core_restore_test` before the up block is applied to production.

### 13.3 Migration File Convention (Future Task)

Migration files will live at `D:\github\agentcore-control-plane\migrations\` and will be named:

```
migrations/
  0001_up_memory_source_systems.sql
  0001_down_memory_source_systems.sql
  0002_up_memory_catalog.sql
  0002_down_memory_catalog.sql
  0003_up_retrieval_events_context_packs.sql
  0003_down_retrieval_events_context_packs.sql
  0004_up_agent_run_ledger_quality_scores.sql
  0004_down_agent_run_ledger_quality_scores.sql
  0005_seed_source_systems.sql

```

Migration files are not created by editing this specification.

### 13.4 Execution Order Dependency

```
0001 memory_source_systems
  └─► 0002 memory_catalog (FK to memory_source_systems.slug)
        └─► 0003 retrieval_events + context_packs + context_pack_items
              └─► 0004 agent_run_ledger + agent_quality_scores
                    └─► 0005 seed source system rows

```

---

## 14. Validation Strategy

### 14.1 Existing Validation Scripts


| Script                                   | What it validates                                                                                                                                                                                    |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ops/Test-AgentCoreSwarmRecall.ps1`      | SwarmRecall config file, API endpoint `:3300`, Meilisearch `:7700`, Postgres dependency, MCP tool discovery (`memory_search`, `knowledge_search` at minimum), no `.env` files, loopback-only binding |
| `ops/Test-AgentCoreSwarmVault.ps1`       | SwarmVault directory structure (`raw/`, `wiki/`, `state/`, `agent/`), built CLI, config file, schema file, no `.env` files, `heuristic` provider, `sqlite` retrieval, `doctor` pass, `query` pass    |
| `ops/Test-AgentCoreMemoryProjection.ps1` | Projection state root and summary exist, checkpoint timestamp valid, canonical memory row count, projection backlog, SwarmRecall API health, SwarmVault query, projected entry counts                |
| `validators/validate-control-plane.ps1`  | Full control-plane schema and config validation (run with `-DryRun`)                                                                                                                                 |


### 14.2 Future Validation Script

`ops/Test-AgentCoreUnifiedRetrieval.ps1` — to be created after `memory_catalog` and `agentcore_retrieve_context` are implemented.

Acceptance criteria for that script:

- `memory_source_systems` table exists with all 8 seed rows
- `memory_catalog` table exists with correct columns and HNSW index
- `memory_retrieval_events`, `context_packs`, `context_pack_items`, `agent_run_ledger`, `agent_quality_scores` tables exist
- Project-scoped query returns results from at least: pgvector (`postgres`), SwarmRecall (`swarmrecall`), SwarmVault (`swarmvault`)
- Cross-project retrieval blocked when `task_type != 'cross_project_research'`
- Retrieval event row written to `memory_retrieval_events`
- No `.env` files in `F:\AgentCore\agentmemory\`
- No raw secrets in catalog rows

### 14.3 Acceptance Gates for Schema Release

Before any migration is applied to the production `agent_core` database, all of the following must be green:

- `Test-AgentCoreSwarmRecall.ps1` passes
- `Test-AgentCoreSwarmVault.ps1` passes
- `Test-AgentCoreMemoryProjection.ps1` passes
- `validate-control-plane.ps1 -DryRun` passes
- Backup-and-restore cycle verified within 24 hours of migration window
- Dry-run of each migration SQL block produces no errors
- Human operator sign-off recorded

---

## 15. Agent Rule Contract

### 15.1 Current Binding Rules (Using Confirmed Existing Tools)

These rules apply immediately to all managed IDE agents. They use tools that exist today.

1. **Use** `memory_append` **for all durable memory writes.** Never issue raw `INSERT` SQL against `agent_core` or `swarmrecall`.
2. **Use** `memory_search` **for memory retrieval.** Never issue raw `SELECT` SQL against memory tables.
3. **Use** `swarmrecall` **MCP** for session memory, knowledge-graph queries, and SwarmRecall-native retrieval against the local service at `http://127.0.0.1:3300`.
4. **Use** `swarmvault` **MCP** for RAG, wiki, context-pack, graph queries against `F:\AgentCore\agentmemory\swarmvault`.
5. **Use** `obsidian-vault` **MCP REST** for Obsidian note reads and writes. Never write to Obsidian vault via filesystem MCP while Obsidian is running.
6. **Never call the SwarmRecall API directly** from a normal agent. All calls must go through the gateway or SwarmRecall MCP.
7. **Never call SwarmVault CLI or filesystem** directly from a normal agent. Use the SwarmVault MCP only.
8. **Use the approved AgentCore memory gateway path as the single canonical memory write path.** Today that is `agentcore-gateway` → `agentcore-memory`; the historical `global-memory-gateway` name in this spec remains pre-migration terminology.
9. **Store only concise, source-attributed, non-secret summaries.** Do not store raw transcripts, credentials, API keys, tokens, passwords, or personally identifiable data.
10. **Always include** `project_id` **/** `associated_project_path` **metadata** in every memory write.

**Always forbidden for normal IDE agents:**

- Raw SQL `INSERT`, `UPDATE`, `DELETE` against `agent_core` or `swarmrecall` databases
- Direct filesystem writes to `F:\AgentCore\agentmemory\` paths
- Direct writes to `D:\Obsidian\` filesystem while Obsidian is running
- Background drift checks or continuous audit loops
- Storing or logging secret values in any memory or catalog record

### 15.2 Target Rules (Once `agentcore_`* Tools Are Implemented)

These rules become binding after the target-contract tools in Section 8.2 are implemented and validated.

1. **Call** `agentcore_get_startup_context(project_id)` **at the start of every non-trivial task** before planning, architecture decisions, code changes, or debugging.
2. **Call** `agentcore_retrieve_context(project_id, query, task_type, privacy_zone, token_budget)` **before making architecture decisions, code changes, or debugging** on an unfamiliar or complex topic.
3. **Call** `agentcore_store_memory(...)` **after completing any task that produced reusable knowledge.** Memory writes must be concise, non-secret, and source-attributed.
4. **Call** `agentcore_store_project_fact(...)` **when a locked project fact changes** (e.g., framework decision updated, database choice changed, deployment target confirmed).
5. **Call** `agentcore_explain_sources(context_pack_id)` **when provenance** of retrieved context is needed for audit or debugging.
6. **Never assume SwarmVault is the only RAG source.** The gateway fans out to all backends.
7. **Never assume SwarmRecall is the only memory source.** The catalog indexes all backends.

### 15.3 IDE-Specific Notes


| IDE              | Memory write tool                                   | Read tool                                               | Notes                                          |
| ---------------- | --------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------- |
| Cursor           | `memory_append` / `agentcore_store_memory` (target) | `memory_search` / `agentcore_retrieve_context` (target) | Primary operator surface                       |
| Codex            | Same as Cursor                                      | Same as Cursor                                          | Source authority IDE                           |
| OpenClaw         | `memory_append`                                     | `memory_search`                                         | Read-mostly until policy proven                |
| MiniMax / Mavis  | `memory_append`                                     | `memory_search`                                         | Read-mostly until policy proven                |
| Claude Code      | `memory_append`                                     | `memory_search`                                         | Config at `C:\Users\ynotf\.claude\config.json` |
| Open Interpreter | **None by default**                                 | `memory_search` read-only                               | High risk; quarantine from write paths         |
| Antigravity      | `memory_append`                                     | `memory_search`                                         | Limited tool surface                           |


---

## 16. Rollout-Phase Relationship

This specification is the design authority for Phase 3 of the AgentCore Swarm Full Automation Rollout (defined in `CONTEXT_BLOCK.md`).

```
Phase 1  Repo audit / preflight
  └─► Confirm live endpoints: :55432, :3300, :7700
  └─► Confirm SwarmVault root and doctor status
  └─► Confirm global-memory-gateway connects to agent_core

Phase 2  Renderers / MCP baseline / validators
  └─► All managed IDEs get mandatory MCP baseline
  └─► Forbidden routes removed from active rules
  └─► Validators green: swarmrecall, swarmvault, memory projection

Phase 3  THIS SPECIFICATION
  └─► database-plan.md becomes source-controlled design artifact
  └─► Schema DDL reviewed and approved (no execution yet)
  └─► Gateway target-contract interface documented
  └─► Agent rule contract adopted in managed IDE rules

Phase 4  SwarmRecall completion
  └─► Requires Phase 2 green
  └─► Projection layer fan-out verified end-to-end
  └─► memory_catalog mirroring logic implementable

Phase 5  SwarmVault completion
  └─► Requires Phase 4 green
  └─► Context-pack build verified
  └─► Task ledger operational

Phase 6  Client config / rule contract
  └─► Agent rule contract (Section 15) adopted in all IDE configs
  └─► agentcore_* target tools implemented in gateway (if resources allow)
  └─► Test-AgentCoreUnifiedRetrieval.ps1 created and passing

Migration window (after Phase 6 acceptance)
  └─► All pre-migration gates in Section 13.1 green
  └─► Human operator sign-off
  └─► Migration execution per Section 13.2 protocol

```

### Monitor Automation Policy for This Pass

**No background monitor automations are included in this rollout.**

Removed for this pass:

- `agentcore-context-window-optimizer`
- `agentcore-pgvector-database-monitor`
- `agentcore-rag-runtime-monitor`
- `agentcore-memory-projection-monitor`
- `agentcore-mcp-drift-monitor`
- `agentcore-live-client-adoption-monitor`
- Any background polling, re-audit, or projection-scan automations

Retained:

- `\AgentCore\PostgresRuntime` scheduled task (startup ownership)
- `\AgentCore\NightlyBackup` scheduled task
- `\AgentCore\NightlyRestoreTest` scheduled task
- `\AgentCore\MemoryProjection` scheduled task (every 2 hours)
- Manual validators (`Test-AgentCore*.ps1`, `validate-control-plane.ps1`)

---

## 17. Deferred Items

The following items are explicitly out of scope for this specification pass. They are documented here so future rollout agents can discover them without needing the original design chat.


| Item                                                                        | Reason deferred                                                            | Prerequisite                                |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------- |
| **LCM / lossless conversation history backend**                             | No live LCM service exists on CHAOSCENTRAL                                 | Live LCM service confirmed and local-only   |
| **Obsidian automatic catalog mirroring**                                    | Requires Obsidian webhook or polling adapter                               | Gateway webhook/adapter implementation      |
| `agentcore_check_drift` **gateway tool**                                    | Drift is validator-driven, not agent-driven; excluded from gateway surface | None — by policy decision                   |
| **Pending-memory local spool** (`F:\AgentCore\agentmemory\pending-memory\`) | Planned fallback contract; gateway must be enhanced                        | Gateway fallback implementation             |
| **Emergency archive spool** (`E:\AgentCoreArchive\memory-spool\pending\`)   | Planned fallback contract; requires pending-memory spool first             | Pending-memory spool implementation         |
| **Monitor automations of any kind**                                         | Removed for this rollout pass; system must be stable first                 | Stable Phase 4–5 rollout                    |
| **Context quality scoring automation**                                      | Schema columns defined; requires stable retrieval first                    | `agentcore_retrieve_context` implementation |
| `Test-AgentCoreUnifiedRetrieval.ps1`                                        | Schema and gateway target tools must exist first                           | Phase 6                                     |
| **Cross-project research policy enforcement**                               | Requires `memory_catalog` table to exist                                   | Migration execution                         |
| `agentcore_`* **tool implementation**                                       | Target contracts defined here; implementation is future gateway work       | Migration execution                         |
| **Migration file creation** (`migrations/*.sql`)                            | Future task; requires Phase 6 acceptance and operator sign-off             | This spec approved; Phase 6 complete        |


---

## 18. Acceptance Checklist

This checklist must be completed by a human operator before any migration work begins. Check each item by running the referenced validator or by direct inspection.

### Pre-Migration Acceptance (Before Any DDL Is Applied)

- **18.1** `database-plan.md` is committed to `D:\github\agentcore-control-plane` and passes `git status` as a tracked, committed file.
- **18.2** `contracts/global-memory-database-contract.json` `schema_version` matches or is consistent with this specification.
- **18.3** `docs/database_overview.md` confirms existing tables match Section 6.1.
- **18.4** PostgreSQL listens on `127.0.0.1:55432` only (not `0.0.0.0`). Verified by: `netstat -ano | findstr :55432`
- **18.5** SwarmRecall API listens on `127.0.0.1:3300`. Health response: `{"status":"ok"}`. Verified by: `Test-AgentCoreSwarmRecall.ps1`
- **18.6** Meilisearch listens on `127.0.0.1:7700`. Verified by: `Test-AgentCoreSwarmRecall.ps1`
- **18.7** SwarmVault root `F:\AgentCore\agentmemory\swarmvault` exists and `doctor` passes. Verified by: `Test-AgentCoreSwarmVault.ps1`
- **18.8** Projection state root `F:\AgentCore\agentmemory\projection-state\` exists with valid `summary.json`. Verified by: `Test-AgentCoreMemoryProjection.ps1`
- **18.9** `global-memory-gateway` connects to `agent_core` and `memory_state` returns `status: ok`. Verified by: calling `memory_state` tool in any managed IDE.
- **18.10** All managed IDEs have the mandatory MCP baseline including `global-memory-gateway`, `swarmrecall`, `swarmvault`. Verified by: `Test-AgentCoreLiveClientAdoption.ps1`
- **18.11** No active IDE rule or config references forbidden routes (`context7`, `raw mem0`, `hosted SwarmRecall`, `hosted SwarmVault`, `direct SQL normal memory`, `:65432`).
- **18.12** No `.env` files exist in `F:\AgentCore\agentmemory\`. Verified by: `Test-AgentCoreSwarmRecall.ps1` (`no env files` check).
- **18.13** A successful base backup completed within 24 hours of the migration window. Verified by: `\AgentCore\NightlyBackup` last result = 0 and backup file present in `E:\AgentCoreArchive\backups_cold\pgvector\base\`.
- **18.14** Restore test verified: `agent_core_restore_test` database created, `global_vector_memory_store` validated, test database dropped. Verified by: `Test-AgentCorePostgresRestore.ps1`

### DDL Dry-Run Acceptance (Before Execute)

- **18.15** Migration `0001_up_memory_source_systems.sql` dry-run (transaction + ROLLBACK) produces no errors.
- **18.16** Migration `0002_up_memory_catalog.sql` dry-run produces no errors; HNSW index creation message confirmed.
- **18.17** Migration `0003_up_retrieval_events_context_packs.sql` dry-run produces no errors.
- **18.18** Migration `0004_up_agent_run_ledger_quality_scores.sql` dry-run produces no errors.
- **18.19** Seed `0005_seed_source_systems.sql` dry-run inserts 8 rows into `memory_source_systems` and produces no constraint errors.
- **18.20** Human operator sign-off: all dry-runs reviewed and approved. Record: `[operator] [timestamp] [commit or ticket reference]`

### Post-Migration Acceptance (After DDL Applied)

- **18.21** All 7 new tables exist in `agent_core`: `memory_source_systems`, `memory_catalog`, `memory_retrieval_events`, `context_packs`, `context_pack_items`, `agent_run_ledger`, `agent_quality_scores`.
- **18.22** `memory_source_systems` contains 8 seed rows with correct slugs.
- **18.23** HNSW index on `memory_catalog.embedding` exists and is valid.
- **18.24** Existing table row counts unchanged: `global_vector_memory_store`, `projects`, `project_facts`, `messages`, `embeddings`, `system_info`, `agent_cross_project_telemetry`.
- **18.25** `Test-AgentCoreMemoryProjection.ps1` passes after migration.
- **18.26** `Test-AgentCoreSwarmRecall.ps1` passes after migration.
- **18.27** `validate-control-plane.ps1 -DryRun` passes after migration.
- **18.28** `memory_append` tool continues to work correctly (no regression).
- **18.29** `memory_search` tool continues to work correctly (no regression).
- **18.30** No secret values appear in any `memory_catalog` or `agent_run_ledger` row.

---

*End of specification. This document is the source-controlled design artifact for the AgentCore Unified Memory Catalog and Context Router. It does not authorize live DB mutation by itself. All migration work requires the acceptance gates in Section 18 and explicit operator sign-off.*