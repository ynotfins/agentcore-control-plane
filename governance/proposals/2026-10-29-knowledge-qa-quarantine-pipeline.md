# Proposal: Knowledge QA quarantine pipeline and gateway filter exposure

**Date:** 2026-10-29  
**Status:** proposal (ordinary-agent path; no locked-doc mutation)  
**Depends on:** approved Local Agent Knowledge plan; live `m5.002` on PG18 `agent_core`

## Why

Coding agents already search the PG18 knowledge plane through `agentcore-gateway` → `agentcore-memory`. `m5.002` added metadata prefilters and a 7th SQL argument (`p_metadata_filter`). Those filters were not on the MCP tools, so agents could not ask for “FastAPI boilerplate” precisely. Upstream repo updates also must not be embedded blindly.

## What this change does

1. Expose optional `framework`, `asset_type`, and `language` on the existing `docs_search` and `retrieve_context` tools. Do **not** add an 11th memory tool and do **not** invent a tool named `hybrid_retrieve_documents`.
2. Keep Bifrost `semantic_cache` in current hash mode (inference only). Add a short `docs_search` result cache inside `agentcore-memory`, keyed by query + filters + corpus revision.
3. Add a nightly outbound sync worker that polls allowlisted remotes with `git ls-remote`, fetches into E: quarantine, QA-gates files, and promotes only non-breaking passes through the DB agent ingest runner.
4. Adopt the breaking-change hold policy below.

Locked files (`BLUEPRINT.md`, memory-platform docs, Bifrost registry) stay unchanged until `UNLOCK` + documentation-guard ACCEPT.

## Fact corrections

- `hybrid_retrieve_documents` is a PostgreSQL function. Agents reach it through `docs_search` / `retrieve_context`.
- Bifrost 2.0.0 `semantic_cache` caches `/v1/chat/completions` answers. It does not cache MCP tool results. Current live config (hash mode, `dimension: 1`, TTL 30m, Redis `127.0.0.1:6381`) is already the correct Bifrost setting for repeated architecture questions at the model layer.
- Official third-party library docs stay in `arabold-docs`. This pipeline is for the operator-owned corpus on E:.

## Breaking-change policy

**Last-good wins.** A failed or held sync never overwrites live `retrieval_documents` rows.

**Auto-promote only when all are true:**

- remote is already enrolled (`enrolled: true`)
- SHA is a same-major / non-breaking update
- Tree-sitter / Markdown QA passes
- changed-file count is inside the catalog bound
- no secrets, binaries, or unexpected paths

**Hold for operator approval when:**

- new remote or first ingest
- major version or tag jump
- public API / symbol churn above bound
- QA fail
- unexpected path outside include globs
- secret-like or binary content

**Breaking change** means the update would teach agents a different public contract (new required API, removed template entrypoint, replaced framework major). Clean parse is not enough.

**Rollback:** keep the previous official E: tree and previous row versions; `Invoke-AgentCoreKnowledgeCorpusSync.ps1 -Rollback <corpus-id>` restores last-good SHA without touching other corpora.

**Trust zones:** failed files may be recorded as quarantined evidence for investigation. They stay out of normal `docs_search`, startup context, and Cognee.

**Hard no:** inbound webhooks, Cloud-agent sync, Swarm / `H:` paths, G: copies, whole-framework repo dumps, a second MCP server.

## Layout

- Staging: `E:\AgentCoreArchive\agentcore-memory\knowledge-quarantine\`
- Promoted corpus: `E:\AgentCoreArchive\agentcore-memory\knowledge-corpus\`
- Hold evidence: `E:\AgentCoreArchive\agentcore-memory\quarantine\knowledge-sync\`
- Logs: `E:\AgentCoreArchive\agentcore-memory\service-logs\knowledge-sync\`

## Automation

Script: `ops/Invoke-AgentCoreKnowledgeCorpusSync.ps1` (dry-run default).  
Scheduled task `\AgentCore\KnowledgeCorpusSync` stays unregistered until GitHub PR #2 (ingest runner) merges into `main` and this branch rebases onto that tip. Nightly 04:00, hidden, logs only, no desktop popup.

Seed remotes are enrolled as `boilerplate` with `auto_promote: false` and tight include globs: Flutter samples, Android Compose samples, Refine, create-t3-app, and shadcn/ui. First ingest still holds.

## UNLOCK items (later, not this change)

- `BLUEPRINT.md` — mention quarantine sync as M5/M7 extension
- `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` — ingest/QA cadence
- Bifrost registry — none, unless someone later tries to add a new tool name (rejected)
