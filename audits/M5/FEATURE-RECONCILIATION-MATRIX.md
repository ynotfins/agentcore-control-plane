# Feature Reconciliation Matrix

**Authority:** `BLUEPRINT.md` is locked authority. Original feature notes are non-authoritative research input.  
**Input note:** no file named `plan-notes.txt` exists in this checkout; the matching original feature-note content is in `Global-memory-and-context-system-revised-2.md`, already bannered `DO NOT EXECUTE`.

| Feature / note | Status | Evidence / disposition |
|---|---|---|
| Immutable evidence ledger | Implemented | M2 `agentcore.evidence_events`; append-only and normal-role update/delete denial proved in `audits/M2/M2-EXIT-EVIDENCE.md` |
| Cognee curated semantic memory | Implemented | M5 `KnowledgeMemoryPort`; `cognee_core`; curated promotion/retrieval checks in `audits/M5/M5-EXIT-EVIDENCE.md` |
| Distill-style rolling context | Implemented differently | M3 implemented native token-budgeted, hierarchical, deterministic compaction; no Distill sidecar |
| COMB-style projections | Implemented | M3 projection worker writes generated `GLOBAL_STATE.md`, `.agentcore/STATE.md`, `.agentcore/DECISIONS.md`, `.agentcore/CONTEXT_INDEX.md` |
| Generated global/project STATE | Implemented | M3/M5 projection evidence; hardening fixed literal-variable interpolation in `Invoke-M3ProjectionWorker.ps1` and regenerated projections |
| One broker/MCP front door | Implemented | `agentcore-gateway` unchanged; `agentcore-memory` compact 10-tool surface preserved |
| Exact source expansion | Implemented | M3/M4 `expand_source` checks; expansion after archive to E: passed |
| Hot/cold artifact movement | Implemented | M3 archive-to-E exact expansion; backup includes H/E artifact paths |
| Local-only / localhost-first behavior | Implemented | PG18 `127.0.0.1:55433`; Bifrost `127.0.0.1:8080`; no IDE DB credentials |
| Quarantine and promotion | Implemented | M3 quarantined context exclusion; M5 raw/quarantined Cognee promotion rejection |
| Project write isolation | Implemented | M2/M4 cross-project write/read rejection |
| Vector/index strategy | Implemented differently | PostgreSQL FTS + `pg_trgm` + exact pgvector baseline implemented; HNSW deferred until measured corpus justifies it; IVFFlat/pgvectorscale/DiskANN remain benchmark-gated |
| Backup/base backup/WAL/PITR | Implemented in hardening | PG18 logical/base backup, E:/G: copy, restore test, WAL archive, and PITR marker recovery added in this pass |
| Explicit memory taxonomy | Clarified | Taxonomy now explicitly mapped below; existing schema/trust/source boundaries already implemented the concepts |
| Evidence Ledger layer | Implemented | AgentCore-owned PostgreSQL evidence plane; not Cognee |
| Semantic Memory layer | Implemented | Cognee only receives promoted/curated knowledge |
| Session Context layer | Implemented | M3 L0-L3 hierarchy, budgeted context assembly, exact source edges |
| Filesystem Projection layer | Implemented | COMB-style generated projections |
| Broker-mediated writes | Implemented | M4 `agentcore-memory` tools; no raw SQL/admin tools exposed |
| Local laptop/shared-backend ideas | Optional future | Out of M0-M5 scope; not imported into architecture |
| Obsolete drive assignments from original notes | Superseded | Rejected by BLUEPRINT drive roles: PG18/F:, WAL archive/E:, backup/G:, Bifrost/H:, scratch/I: |
| Qdrant/other vector DB exposure remediation | Optional future / separate security work | BLUEPRINT rejects second canonical vector DB for v1; local security observations remain outside M0-M5 platform hardening |
| LangGraph durable workflow | Scheduled for M6 | Do not begin M6 during this task |
| Engineering knowledge/templates | Scheduled for M7 | Not missing from M0-M5 |
| Operations/performance/final cutover | Scheduled for M8 | This task pulled forward WAL/PITR because M2-M5 durable state now exists |

## Explicit Memory Taxonomy

| Taxonomy class | Canonical mapping | Current result |
|---|---|---|
| Global Immutable | Stable operator/machine/project authority, policies, source docs, generated global state; PostgreSQL-backed metadata and source-controlled authority docs | Implemented/clarified; ordinary agents read, not mutate |
| Global Curated | Promoted reusable facts, verified decisions, reusable fixes/patterns, curated docs concepts | Implemented through M5 Cognee promotion rows and PostgreSQL provenance |
| Project Durable | Project identity, evidence, summaries, fact proposals, generated project STATE/DECISIONS/CONTEXT_INDEX | Implemented through M2-M4 schemas and projections |
| Session Ephemeral | Bounded active context window, recent raw tail, temporary compaction state | Implemented through M3 context hierarchy and session state |
| Raw Evidence | Append-only original prompts/messages/tool events/artifact metadata | Implemented through M2 evidence ledger and content-addressed artifacts |

## Genuinely Missing

No original feature-note item required for M0-M5 was found genuinely missing after this pass. Remaining items are either scheduled for M6-M8, optional future work, superseded by BLUEPRINT, or blocked by elevated Windows service/task permissions documented in `M0-M5-HARDENING-EVIDENCE.md`.
