# AgentCore Knowledge Library — Constitution

**Status:** operator-locked. Do not edit without explicit operator `UNLOCK` of this file.  
**Approval:** `AUTH-2026-11-01-KNOWLEDGE-LIBRARY-AUTHORITY`  
**Owner:** AgentCore control plane (`D:\github\agentcore-control-plane`)  
**Live ops root:** `D:\agentcore-worktrees\agentcore-control-plane\main`

This file is the constitution of the operator-owned knowledge library. Counts, SHAs, and nightly logs are not law. Those belong in sync-state and service logs.

Companion laws:

- `docs/knowledge-library/AGENT_USE_LAW.md` — every agent must query before inventing structure
- `docs/knowledge-library/PROMOTION_AND_TRUST.md` — what may enter the index
- `docs/knowledge-library/LIBRARY_AGENT_CHARTER.md` — the Library agent’s job

---

## 1. What the library is

The knowledge library is **one retrieval plane**, not a new database and not a new MCP server.

| Layer | Location | Role |
| --- | --- | --- |
| Searchable index | PostgreSQL 18 `agent_core` / `agentcore.retrieval_documents` at `127.0.0.1:55433` | Chunks, full-text, trigram, `pgvector`, metadata filters |
| Promoted cold files | `E:\AgentCoreArchive\agentcore-memory\knowledge-corpus\` | Approved docs, boilerplates, agent rules, OpenAPI |
| Quarantine clones | `E:\AgentCoreArchive\agentcore-memory\knowledge-quarantine\` | Nightly fetch before QA |
| Hold evidence | `E:\AgentCoreArchive\agentcore-memory\quarantine\knowledge-sync\` | Files that must not teach agents |
| Sync logs / state | `E:\AgentCoreArchive\agentcore-memory\service-logs\knowledge-sync\` and `knowledge-quarantine\sync-state.json` | Operational evidence |
| Embeddings runtime | `F:\AgentCore\runtime\knowledge-corpus` + models under `F:\AgentCore\runtime\models` | Local `nomic-embed-text-v1.5` (768-d) |
| Official vendor docs | Arabold at `F:\AgentCore\runtime\docs-store` | Exact-version Next.js, FastAPI, Bifrost, and other pinned libraries |

Indexes live on F: (PGDATA). Raw corpus lives on E:. Do not put this library on `H:`, Swarm trees, `I:\LocalApps`, or `C:`.

This is BLUEPRINT **M5 hybrid retrieval**: official/operator files on cold E:, searchable metadata on F:. It is **not** a second vector product. LanceDB, Qdrant, Redis, Neo4j, Mem0, and a second Postgres database name stay rejected.

---

## 2. How every agent reaches it

```text
IDE agent
  -> agentcore-gateway   (http://127.0.0.1:8080/mcp)
  -> agentcore-memory    docs_search / retrieve_context
       +-- operator corpus: retrieval_documents (filters: framework, asset_type, language)
       +-- project memory: exact evidence / chronology
  -> arabold-docs        official library@version facts
```

Bifrost is the front door. Bifrost `semantic_cache` caches model answers. It is **not** the knowledge library.

Forbidden:

- a second knowledge MCP
- raw SQL from ordinary IDEs
- Postgres credentials in IDE config
- treating `D:\MCP-Control-Plane` or MiniMax `E:\TemplateLibrary` as this library
- ingesting Swarm / `H:` / Obsidian vaults / secrets into this corpus

---

## 3. What belongs in the corpus

Allowed `asset_type` values:

| `asset_type` | Meaning |
| --- | --- |
| `boilerplate` | Small approved reference implementations and their docs — not whole upstream repos |
| `docs` | Operator-owned or curated snapshots |
| `agent_rule` | Agent rule packs and standards |
| `openapi` | Contract / OpenAPI specs |

Required metadata on every chunk: `asset_type`, `framework`, `language`, `license`, `chunk_id`, `embedding_model`, `embedding_dim`.

Enrolled starter frameworks: `flutter`, `android`, `refine`, `nextjs`, `react`, `fastapi`, `agentcore`. New frameworks require operator AUTH and a catalog remote — they are not invented in chat.

---

## 4. What is not this library

| Surface | Authority | Use for |
| --- | --- | --- |
| Arabold | `F:\AgentCore\runtime\docs-store` | Official vendor API/version facts |
| AgentCore project memory | `agentcore-memory` chronology / evidence | What this project decided and proved |
| Neutral SwarmRecall | server-side only behind `agentcore-memory` | PC-wide semantic projection — not boilerplate source |
| Cognee | curated promotions only | Promoted facts — not raw repos |
| Training memory | none | Never a source for versions or scaffold structure |

---

## 5. Change policy

This constitution, the use law, the trust law, and the Library agent charter are **operator-locked**. Wording fixes must not change meaning. Nightly corpus sync does not unlock or rewrite them.

Mutable operational files (not this constitution):

- `contracts/knowledge-corpus-catalog.json` — enrolled remotes and globs
- nightly logs and `sync-state.json`
- hold reports

Adding a remote, changing embedding model/dimension, adding a database, adding an MCP tool, or moving roots off E:/F: requires operator AUTH. Live DDL still requires AUTH.
