> **HISTORICAL RESEARCH INPUT — DO NOT EXECUTE (2026-07-14).**
> This essay fed the rewritten `CONTEXT_BLOCK.md` and is preserved as research evidence only.
> Known errors: wrong hardware/drive facts (RTX 5070, wrong drive map — actual machine facts live in
> `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md`); a storage plan that contradicts `PROJECT_ANCHOR.md`
> drive roles; and an embedded "Memory Broker" prompt that bypasses the Bifrost `agentcore-gateway`.
> **Do not execute the embedded Cursor master prompt.** Current authority:
> `CONTEXT_BLOCK.md` → `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`.

# Master Blueprint for a Global Agent Memory and Context System

## Executive recommendation

The best answer is **not** to treat any one repo as “the” whole system. For your workstation, the strongest design is a **dual-plane architecture**: an **immutable evidence plane** that keeps the original raw events and transcripts, plus a **semantic memory plane** that turns those events into retrieval-ready graph memory and rolling context. That distinction matters because the products you researched optimize, summarize, compact, or transform memory in different ways; none of them, by itself, is a true lossless ledger in the “keep every original and still stay fast” sense. The closest conceptual model to what you want is the LCM pattern of recursive compression with lossless pointers back to originals, which strongly suggests pairing a raw append-only log with a higher-level memory engine rather than expecting one engine to do both jobs. citeturn0academia2turn10view6turn19view2turn30view6

My final recommendation is: **Cognee as the canonical long-term semantic memory layer, COMB as the plain-markdown projection and context protocol, and a thin custom Memory Broker inside `D:\github\agentcore-control-plane` that exposes one MCP surface to every IDE and LangGraph workflow.** For rolling-context behavior, either embed Distill’s ideas directly into that broker or run Distill behind the broker as a session-budget sidecar. That gives you one stable “front door” for agents while still getting graph memory, session compaction, and cross-IDE plain-text projections. Cognee is the best fit because it already supports MCP, Cursor, Codex, LangGraph, and OpenClaw-class integrations, and it can run its full memory layer on a single Postgres instance with pgvector instead of forcing you into a multi-database stack. COMB is a strong complement because it is explicitly a cross-tool markdown methodology, not another service. Distill is the best short-term context component because it already implements token-budgeted sessions, hierarchical compression, and MCP integration with no LLM calls in the compression path. citeturn12view0turn13view0turn13view1turn16view1turn20view0turn20view2turn19view2turn19view3

Your assumption that **“Cognee + COMB” is the right direction** is **mostly correct**, but it is incomplete. Cognee should be the semantic memory core. COMB should **not** be treated as the database; it should be the filesystem-facing projection layer that keeps every IDE and MCP client aligned. You still need a broker/governance layer to enforce read/write scope, maintain a generated global `STATE.md`, and preserve raw lossless evidence separately from summaries and graph facts. citeturn20view2turn20view3turn13view1turn17view0

Based on your uploaded machine inventory, you have enough local compute and storage to do this properly: an i9-14900KF, 128 GB RAM, RTX 5070, a 4 TB Samsung 990 Pro on `D:`, a 10 TB WD_BLACK on `F:`, a 16 TB Seagate Exos on `H:`, and two 2 TB Samsung 970 EVO Plus drives on `E:` and `I:`. Your inventory also notes an existing Qdrant exposure on `0.0.0.0` without auth, which is exactly the kind of thing you should **not** expand into the new global memory plane. fileciteturn0file3

## Mental models of the repos you researched

### Cognee

**Mental model:** Cognee is a **memory platform for agents**, not just a vector DB wrapper. Its docs and repo position it as a system that ingests data, builds a self-hosted knowledge graph, and exposes that memory through first-party integrations and MCP. It supports Cursor, Codex, LangGraph, OpenClaw, and MCP clients, and its MCP package supports both **Standalone Mode** and **API Mode**. API Mode is the key piece for your design because multiple MCP instances can share one centralized Cognee backend and one knowledge graph, which is exactly what you need when several IDEs and agent runtimes are active at once. citeturn12view1turn12view2turn13view0turn13view1turn16view5

Cognee’s strongest advantage for your case is that in current releases it can run the **entire memory layer on one Postgres instance**: graph backend, pgvector embeddings, SQL session cache, and metadata in one place. The repo explicitly contrasts that with the usual “graph DB + vector DB + Redis + relational metadata” stack and says Postgres is the default they recommend for most deployments; they also report their CI benchmarks showed Postgres search about 10% faster than the separate graph-plus-vector setup. Since you already wanted PostgreSQL 18 with pgvector and want fewer moving parts, that is a very strong fit. citeturn16view1turn16view2turn16view3

Cognee also fits your governance requirements better than most of the other repos because it exposes **custom ontologies**, **custom data models**, and **permissions / access control** concepts, and its docs describe user/dataset isolation. In other words, Cognee is not just retrieval; it is a memory substrate you can shape around your organization of “global facts,” “project datasets,” “templates,” and “libraries.” That matters for your requirement that some information should be globally available while write access remains constrained. citeturn17view0turn17view1turn17view2

The important limitation is that Cognee is still **not** a full lossless event ledger by itself. It is the best **semantic memory** core in your stack, but it should sit on top of an append-only evidence layer that stores original transcripts, tool traces, file snapshots, and decision records before they are transformed into graph memory. That recommendation is an inference from the project’s knowledge-graph design and from the fact that your target behavior is closer to LCM-style “compress but keep lossless references” than to any single-memory product’s default mode. citeturn15view0turn17view2turn0academia2

### Hindsight

**Mental model:** Hindsight is a **specialized agent-memory service** designed around `retain`, `recall`, and `reflect`, with a memory-bank abstraction and a PostgreSQL-first architecture. Its docs describe a hierarchy of memory types, parallel retrieval strategies across semantic, keyword, graph, and temporal search, and observation consolidation that refines beliefs over time. It has broad integrations, including Cursor, Codex, LangGraph, MCP, Obsidian, and OpenClaw-class ecosystems, and it is unusually operationally opinionated in a good way: one database, one backup strategy, one monitoring target. citeturn7view0turn8view0turn9view1

Hindsight would fit **well** if your main objective were “deploy a production-grade learning memory service for agents with minimal database sprawl.” Its storage docs are strong: PostgreSQL is the primary backend, Oracle AI Database is the enterprise alternative, and the project deliberately avoids generic storage abstraction to keep operations simple. For a lot of teams, that is exactly the right philosophy. citeturn8view0

For **your** exact goal, though, Hindsight is only a **partial** fit. The strongest issue is that Hindsight’s own best-practices documentation says a memory bank is the unit of isolation, banks do not share data, and raw content is **not stored verbatim**; retain ingests raw content, but the system extracts facts, entities, and relationships rather than preserving the raw payload as the canonical store. That makes Hindsight excellent as a semantic memory engine, but not ideal as the *single source of truth* for a “lossless claw-like” system where you want every original artifact preserved and reconstructable. citeturn10view6turn9view2

The second issue is practical LangGraph fit. Hindsight’s LangGraph integration is real and useful, but the `HindsightStore` has several caveats: it is async-only, `get()` is recall-based rather than a direct key lookup, `list_namespaces` is session-scoped, and `delete` is a no-op because Hindsight’s model is append-oriented. Those are not deal-breakers for many applications, but they are the wrong trade-offs if you want your **global workstation memory plane** to behave like a durable, governable state substrate for multiple IDEs and automation workflows. citeturn9view0turn10view0turn10view1turn10view2turn10view3

My judgment is that Hindsight is the **best runner-up primary engine** among the repos you surfaced, but it should not be your default workstation-wide memory substrate. It is better understood as a sophisticated memory service that you would choose **instead of** Cognee, not a complement to Cognee, and in your case Cognee’s unified Postgres story and API-mode sharing model map better to your cross-IDE requirement. citeturn8view0turn13view1turn16view1

### COMB

**Mental model:** COMB is **not a database** and **not a memory engine**. It is a **context-governance methodology** for keeping AI-visible documentation structured, cache-friendly, and tool-neutral. The repo is explicit about this: static architecture docs load once, dynamic work files load fresh, active files stay lean, archives move old material out of the hot path, and shared content lives in plain markdown that Claude Code, Cursor, Windsurf, Copilot, and basically any file-reading agent can consume. citeturn20view0turn20view1turn20view2turn20view3

That makes COMB a very good fit for your environment because you use multiple IDEs and MCP servers simultaneously and you specifically want a global `STATE.md`, a knowledge base, templates, and a project-facing context protocol that does not depend on one vendor’s proprietary behavior. COMB gives you the filesystem contract for that. The right way to use it is as a **projection layer**: the canonical source of truth stays in the broker + database + evidence log, while COMB files are generated and updated so that every IDE starts from the same state. citeturn20view2turn20view3

### Distill

**Mental model:** Distill is a **deterministic context-intelligence layer**, not a full semantic memory platform. It is strongest where Cognee is weakest: **rolling context windows, write-time deduplication, hierarchical decay, token-budgeted session context, and MCP delivery**. The repo states that it has no LLM calls in its core optimization path, that it adds around 12 ms of overhead, and that it exposes both persistent context memory and explicit session-management tools. It can decay memories from full text to summaries to keywords and manage session budgets with importance-aware compression and eviction. citeturn19view1turn19view2turn19view3turn19view4turn19view5

This repo is the clearest match for your “lossless claw-like rolling context” requirement, **but only for the session/context plane**. I would not use Distill as the only long-term memory system for your whole workstation, because it is not trying to be a governed, ontology-shaped, shared semantic memory fabric. I **would** use it as a model—or a hidden sidecar behind your broker—for short-term context budgeting and auto-compaction. In other words: Distill solves the **rolling window** problem very well; Cognee solves the **persistent semantic memory** problem better. citeturn19view2turn19view3

### agentmemory

**Mental model:** agentmemory is an **agent host integration layer** first and a canonical database second. It is excellent at wiring memory into Claude Code, Codex CLI, Cursor-style MCP hosts, OpenClaw, Hermes, and other agent shells. It bundles hooks, skills, a viewer, and an MCP server, and it is intentionally designed to have **no external DBs** in its main path. The README explicitly says its external dependencies are “None (SQLite + iii-engine),” and even the “what iii replaces” section contrasts it with a more traditional SQLite/Postgres + pgvector stack. citeturn5view1turn18view3turn18view5

That is appealing if your goal is “make current agents smarter fast.” It is **not** ideal if your goal is “build one durable workstation-wide memory substrate on a big local Postgres-backed storage tier.” It also has a Windows reality check: the repo says the fast path on Windows is WSL2, native Windows engine setup is manual, and `agentmemory connect` is currently unsupported there. That does not match your desire for a low-friction, rock-solid, workstation-native foundation. citeturn5view1turn18view4

### claude-changeling-agent

**Mental model:** this is a **persona-switching / specialist-loading pattern**, not a memory system. Its value is context efficiency: only load the persona or specialist that matters for the task. The repo’s benefits section says exactly that—context-efficient loading, instant switching, and persona fusion from markdown files. That is useful as a **design pattern** for your broker and prompt templates, but it should not be deployed as part of the core memory plane. Borrow the idea; do not make it infrastructure. citeturn5view4

## Outside options worth knowing about

### Graphiti

If I had to name the most serious **outside** alternative to Cognee for your use case, it would be **Graphiti**. Its mental model is a **temporal context graph** with validity windows, provenance through episodes, and hybrid retrieval across semantic, keyword, and graph traversal. It now has an MCP server, but its default operational story still centers on **Neo4j or FalkorDB** and a separate service stack. That makes it attractive if temporal fact history is the overwhelming priority, but it introduces more moving parts than Cognee-on-Postgres. For your “Apple-like” requirement, that complexity cuts against it unless Cognee fails a real benchmark in your environment. citeturn24view0turn24view1turn24view2

### Letta

The strongest **stateful runtime** outside your list is **Letta**. Its docs expose a clean mental hierarchy: always-visible **memory blocks** in the prompt, **shared memory** blocks (including read-only blocks), **archival memory** for semantic search, and configurable **compaction** when the context window overflows. That is powerful, especially for multi-agent handoff and shared state. The reason I would not make it your primary substrate is category mismatch: Letta is best when Letta itself is the agent runtime. You need a **neutral memory fabric** that many IDEs and frameworks can sit on top of, not a single runtime that wants to be the center of gravity. citeturn29view0turn30view0turn30view1turn30view2turn30view4turn30view5turn30view6

### Projectmem

The best **governance-sidecar idea** outside your list is **Projectmem**. It is local-first, event-sourced, MCP-native, and explicitly frames itself as a **memory + judgment layer** that warns against repeating failed fixes. Its recent workspace release adds a global dashboard aggregated at read time across projects while keeping each repo’s data local. This is extremely relevant to your requirement for preventing agents from repeating mistakes and for preserving “what changed, why, what was tried, and what failed.” I would not use it as the main semantic database, but I would absolutely steal its event-log and pre-action-guard ideas for your broker. citeturn35view0turn22academia0

A brief honorable mention goes to **Mem0**, but I would not put it ahead of the three above for your build. The current Mem0 README says its strongest benchmark numbers come from the managed platform with proprietary optimizations, not the open-source SDK, and the `openmemory` path is being sunset in favor of the self-hosted server. That uncertainty is tolerable if you want a broader ecosystem bet, but it is not ideal when you want one carefully governed local-first foundation. citeturn27view1turn27view2

## The blueprint I would build on your workstation

The core design should be **four layers behind one MCP endpoint**. First, an **Evidence Ledger**: an append-only raw store of prompts, assistant outputs, tool traces, terminal output, git events, selected file snapshots, and explicit decisions. This is the only layer that should claim to be “lossless.” Second, a **Semantic Memory Layer**: Cognee in API Mode on local Postgres, turning curated raw evidence plus documents and library corpora into graph memory. Third, a **Session Context Layer**: Distill-style token-budgeted windows and hierarchical compression per agent/project/session. Fourth, a **Filesystem Projection Layer**: generated COMB files per project and a generated global `STATE.md` / template / KB hierarchy that every IDE can read without custom glue. The broker in `agentcore-control-plane` sits in front of all of it and becomes the only thing IDEs and LangGraph workflows talk to. citeturn16view5turn16view1turn19view2turn20view2turn20view3turn0academia2

The most important anti-friction decision is this: **make the global `STATE.md` a generated artifact, not a shared hand-edited file**. Shared mutable markdown becomes a conflict magnet when several agents are active. Letta’s shared-memory docs explicitly warn about race conditions and recommend append-style contributions over multi-writer rewrites; COMB also separates static from dynamic context and archives old content to keep hot files lean. So your broker should own the write path, update the database and evidence ledger first, and then project read-optimized markdown views out to the filesystem. Agents may write their **project-scoped** state files, but the broker should validate and re-render the global files. citeturn30view0turn30view1turn20view1turn20view3

The memory taxonomy should be explicit. I would create **Global Immutable**, **Global Curated**, **Project Durable**, and **Session Ephemeral** classes. “Global Immutable” holds machine profile, user profile, coding standards, policy, templates, and base KB snapshots; this should be broker-owned and read-only to agents. “Global Curated” holds reusable patterns, common fixes, and vetted architectural guidance. “Project Durable” holds ADRs, active context, sprint state, repo-specific learnings, and issue/fix history. “Session Ephemeral” holds today’s rolling context window, tool traces, and temporary summaries. That split maps naturally onto Cognee’s graph memory, Distill’s session memory, COMB’s static/dynamic markdown split, and Letta-style read-only/shared patterns. citeturn17view0turn19view2turn20view1turn30view1

Your uploaded hardware profile suggests a clear storage tiering plan. Use the **fast Samsung SSD/NVMe tiers** for active repos, the broker, Postgres, WAL, temp tablespaces, and session stores; use the large-capacity drives for raw evidence growth, backups, and completed-project cold storage. I would place `agentcore-control-plane`, active git worktrees, COMB projections, template repos, and hot library mirrors on `D:`; PostgreSQL 18 primary data for Cognee on `E:`; `pg_wal`, temp tablespaces, and the session-context store on `I:`; the append-only evidence ledger and inactive-but-searchable project archives on `F:`; and Postgres base backups, WAL archive, completed projects, and cloud-sync staging on `H:`. I would also move Docker/volume-heavy agent services off the already busy `C:` system drive. fileciteturn0file3

Your request for “unlimited storage” needs one factual correction: **no local database provides literal unlimited storage**. What you can build is an **effectively unbounded retention policy** using append-only local data, base backups, WAL archiving, and cold-tier or cloud export. PostgreSQL’s WAL design and PITR tooling are exactly what make that sane: WAL reduces write amplification, supports continuous archiving, and enables point-in-time recovery from a base backup plus WAL replay. So the right mental model is not “the DB is unlimited”; it is “the hot DB stays fast, and older evidence/snapshots roll to colder tiers while recoverability stays intact.” citeturn33view0turn33view1

For the vector/index layer, I would start with **plain pgvector HNSW** inside PostgreSQL 18 and keep **pgvectorscale / DiskANN** as an optional upgrade path, not a day-one dependency. pgvector’s own docs say HNSW gives a better speed/recall trade-off than IVFFlat but at higher memory cost, and both HNSW and IVFFlat can be tuned per-query with `SET LOCAL`. pgvectorscale is attractive for larger datasets and disk-based vector search, but it is an optimization layer that should come **after** you validate your real workload. Since Cognee already recommends Postgres + pgvector as the default shape, this keeps the stack simple. citeturn16view1turn34view0turn34view1turn34view2turn34view5

For security and governance, keep this system **localhost-first** and broker-mediated. Your own inventory mentions an existing unauthenticated Qdrant exposure on `0.0.0.0`; the new memory substrate should not repeat that pattern. In addition, recent research shows persistent memory itself can become an attack surface: poisoned memories can be written, retrieved later, and used to steer future agent behavior. That is another strong reason to put all writes through a broker with source labeling, quarantine rules, and explicit promotion from “raw evidence” to “curated durable memory.” fileciteturn0file3 citeturn26academia3

If you later want the laptop to participate, the typical best-practice pattern here is **not** full bi-directional graph replication at first. Instead, run a **separate local instance** on the laptop for autonomy, and sync only a curated subset—global immutable state, selected templates, and a vetted KB—through git/object storage export jobs. When the laptop is on a trusted network or VPN, it can also point its broker to the desktop’s Cognee API Mode backend; Cognee’s own docs explicitly support both isolated standalone mode and shared-backend API mode. That recommendation is an inference from Cognee’s architecture modes and from your reliability-first requirement. citeturn13view1turn16view5

## Why Hindsight should not be the default memory system here

The direct answer to your original Hindsight question is: **Hindsight fits well as a high-quality memory service, but not well enough as the full global memory/context/database system you want.** It gives you PostgreSQL-first storage, many integrations, and strong retrieval/learning semantics. If your build were mostly “one memory service for several agents,” Hindsight would stay near the top of the list. citeturn5view5turn7view0turn8view0

The reason I would not choose it here is that your actual requirement is larger than “memory service.” You want **lossless evidence retention**, **global cross-IDE state**, **project-scoped write policies**, **LangGraph automation**, **a markdown projection layer**, and **rolling context auto-compaction**. Hindsight’s bank model isolates data per bank, banks do not share data, and the project’s own docs say raw content is not stored verbatim. Its current LangGraph `BaseStore` adapter also has limitations that matter for a default shared substrate. Those are acceptable trade-offs for many products, but they are the wrong defaults for your workstation-wide control plane. citeturn10view6turn10view1turn10view2turn10view3

So my assessment of the “Hindsight as the memory and context and database system” hypothesis is: **partially correct, but ultimately not the best fit.** It is an excellent **component category** match, but a weaker **system-of-systems** match than Cognee + COMB + broker + Distill-style session management. citeturn8view0turn13view1turn19view2turn20view2

## Cursor master prompt

The prompt below is designed to give Cursor a clear target architecture while still giving it room to optimize around real repo context, measured benchmark data, and friction reduction. It reflects the evidence above: Cognee as the semantic core, COMB as the markdown/context protocol, a broker as the single MCP surface, a lossless raw-event ledger underneath, and a Distill-style rolling context layer either embedded or run behind the broker. citeturn16view1turn13view1turn20view2turn19view2

```text
You are working inside the control-plane project at:

D:\github\agentcore-control-plane

Your job is to design and implement a workstation-wide global memory, context, and governance system for AI coding agents and IDEs.

Non-negotiable end state

We are building one unified local-first memory platform for this PC that:
- becomes the default memory/context system for all IDEs and agent runtimes on the machine
- is the default memory substrate for LangGraph workflows
- supports multiple IDEs/clients at the same time through one stable MCP-facing front door
- preserves raw evidence losslessly
- provides durable semantic memory across sessions
- provides rolling context windows with auto compaction
- projects clean plain-markdown context files to the filesystem for any agent to read
- enforces project-scoped write permissions
- minimizes moving parts unless an added component materially improves correctness, durability, or performance

Primary architectural decisions

1. Canonical semantic memory engine
- Use Cognee as the primary long-term semantic memory engine.
- Prefer Cognee API/shared-backend mode so multiple IDEs/clients can share one knowledge graph.
- Use PostgreSQL 18 + pgvector as the primary backend unless measured repo-aware validation proves another backend is materially better.
- Do not introduce Neo4j, Redis, Qdrant, or separate vector/graph services unless benchmarks inside this repo show a clear win that justifies complexity.

2. Global MCP front door
- Build a thin local “Memory Broker” service inside this repo.
- This broker is the only MCP endpoint agents need to know about.
- The broker may call Cognee and may also call or embed a session-context engine, but clients should see one stable interface.
- The broker must be designed so unsupported IDEs can still work if they are generic MCP clients.

3. Lossless evidence plane
- Create an append-only, immutable raw evidence layer below semantic memory.
- It must preserve original prompts, assistant responses, tool traces, terminal output, git events, structured decisions, and selected file snapshots.
- Never make a summarized or graph-transformed store the only source of truth.
- Every promoted semantic memory should retain provenance to raw evidence.

4. Rolling context plane
- Implement a Distill-style session/context layer for token-budgeted rolling windows.
- This may be a vendored integration, a sidecar hidden behind the broker, or a native reimplementation if that reduces friction.
- Required behavior:
  - write-time dedup
  - hierarchical compression
  - importance-aware retention
  - session-scoped context windows
  - deterministic behavior where possible
- Keep this behind the broker so IDEs do not need a second MCP server.

5. Filesystem projection plane
- Use COMB as the plain-markdown projection and context protocol.
- COMB files are projections and operating context, not the canonical durable database.
- Generate or update:
  - global STATE.md
  - per-project STATE.md
  - memory-bank/ INDEX.md
  - active-context
  - sprint tracker / ADR / patterns views
  - template and knowledge base projections
- Keep shared files tool-neutral and plain markdown.

6. Governance and write-scope enforcement
- All agents can read global state and all project files that the workstation policy allows.
- Agents may only write:
  - their current project
  - approved broker-owned projection targets
- Global STATE.md should be broker-generated and treated as read-optimized, not a multi-writer free-for-all.
- Prefer append/update transactions through the broker instead of direct multi-agent file mutation.

Required memory taxonomy

Implement these classes explicitly:

- Global Immutable
  Machine profile, user profile, coding standards, security rules, default conventions, templates, pinned libraries. Read-only to agents.

- Global Curated
  Reusable patterns, validated fixes, architecture guidance, preferred practices, approved workflows.

- Project Durable
  ADRs, active project context, issue/fix history, repo-specific learnings, validated decisions, handoff state.

- Session Ephemeral
  Current rolling context, tool traces, temporary summaries, in-progress reasoning support.

- Raw Evidence
  Immutable logs and provenance snapshots below all other layers.

Drive planning requirements

You must use measured benchmark-driven decisions, not folklore.

Current machine context has multiple internal drives including:
- D: fast active-work volume
- E: internal SSD/NVMe tier
- I: internal SSD/NVMe tier
- F: large-capacity internal drive
- H: large-capacity archive/internal drive
plus C: system drive

Your task:
- inspect the repo and existing machine assumptions
- produce a storage layout plan for:
  - active repos
  - Postgres data
  - pg_wal
  - temp tablespaces
  - raw evidence ledger
  - session-context store
  - backups
  - WAL archive
  - completed-project cold storage
  - template/KB mirrors
- do not assume all non-C drives are equivalent
- create a benchmark harness and decision doc before any destructive reformat or migration recommendation
- if you recommend filesystem changes such as allocation unit sizing or moving Docker data roots, justify them with measured workload assumptions and rollback steps

Security requirements

- Localhost-first by default
- No unauthenticated 0.0.0.0 memory services
- All broker writes must be source-labeled
- Add quarantine/promotion flow so untrusted content does not immediately become durable curated memory
- Design for auditability and restore testing
- Backups must support base backup + WAL archiving + tested restore procedure

LangGraph requirements

- LangGraph workflows must consume the unified broker, not bypass it
- Broker must expose tools/patterns that make sense for:
  - semantic recall
  - raw evidence retrieval
  - session context injection
  - state projection
  - memory promotion / forgetting / superseding where safe
- Keep integration ergonomic for automated workflows

Multi-IDE requirements

Priority hosts include:
- Cursor
- Codex
- any MCP-compatible IDE/runtime on the PC
- agent workflows layered through LangGraph

Design host integrations so:
- supported hosts can use native conveniences when valuable
- unsupported hosts still function through plain MCP
- there is one default memory system from the user’s perspective

What to borrow vs what to run

- Use Cognee as the long-term semantic memory core.
- Use COMB as the markdown context protocol.
- Borrow the idea of changeling/persona specialization as a prompt/skills pattern only if useful; do not add it as core infrastructure unless it clearly reduces context bloat.
- Prefer stealing ideas from Distill and Projectmem over running many extra daemons if equivalent reliability can be achieved with fewer moving parts.
- If you keep a sidecar, hide it behind the broker.

What success looks like

When done, a coding agent on this PC should:
- start with accurate project and global context
- avoid re-reading entire repos unnecessarily
- remember validated prior work across sessions
- preserve raw source evidence
- keep context windows bounded and useful
- see a consistent global STATE.md and per-project state views
- never write outside the allowed project scope
- behave like one polished local platform, not a pile of loosely wired tools

Execution style

- First inspect the repo and existing architecture
- Then produce the cleanest target design with the fewest justified moving parts
- Prefer modular code
- Prefer boring, durable infrastructure over cleverness
- Document assumptions, trade-offs, migration steps, rollback steps, and validation tests
- If you can reduce friction or collapse components without weakening correctness, do it
- If the repo context suggests a better adaptation than this prompt, adapt it while preserving the goal state

Deliverables required inside the repo

1. Architecture decision document
2. Storage layout decision document
3. Security/governance decision document
4. Broker design and MCP contract
5. Semantic memory integration plan
6. Session/rolling-context plan
7. Filesystem projection/COMB implementation plan
8. Backup and restore plan
9. Validation checklist and integration tests
10. Final friction-reduction pass that simplifies the design where possible

Important rule

The final system must feel like one product.
Not a toolbox.
Not a demo.
Not a loose federation of repos.

Optimize for reliability, auditability, recoverability, and low operator burden for a vibe-coding user who should not need to debug the infrastructure manually.
```