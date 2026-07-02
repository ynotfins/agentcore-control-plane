# PROJECT ANCHOR — AgentCore Control Plane Constitution

> **STABLE / IMMUTABLE.** This is the non-negotiable project constitution. It contains no temporary rollout status.
> Do not edit without explicit operator approval. Current rollout state lives in `CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md`, not here.
> Document hierarchy: see `DOC_AUTHORITY.md`. Schema/gateway design: see `database-plan.md`.

---

## 0. Native-First Memory Override (2026-07-01, operator-approved)

> **LIVE-STATE OVERRIDE.** Operator directive: native SwarmRecall + native SwarmVault are the
> automatic default memory/RAG plane for every IDE and agent. `global-memory-gateway` is RETIRED
> from the mandatory MCP baseline and removed from every IDE's live default config, from the
> renderers, and from the master contract's default surfaces (it is now listed in
> `default_exclusions.must_not_emit`). Any downstream text in this constitution or in
> `MASTER_CONFIG_AND_PROMPT.md`, `database-plan.md`, or `DOC_AUTHORITY.md` that still treats
> `global-memory-gateway` as the canonical/normal memory write path is superseded by this section:
> route normal durable memory through native SwarmRecall (memory/graph/learnings/skills/pools) and
> native SwarmVault (RAG/wiki/context/task ledger). The `agent_core` governed DB and the projector
> remain available for governed/curated flows, but are not the default IDE memory route.

---

## 1. Authority

- **Source authority:** `D:\github\agentcore-control-plane` — all governance, contracts, renderers, validators, ops scripts, migrations, and docs.
- **Compatibility / live-ops evidence only:** `D:\MCP-Control-Plane` — NOT a design authority. Scheduled tasks and WAL scripts may still reference it; agents must not treat it or any doc under it as current instructions.

## 2. Drive Roles


| Drive | Role                                                                                          |
| ----- | --------------------------------------------------------------------------------------------- |
| `C:`  | OS, apps, user profile, live IDE configs (app-owned; not directly edited without approval)    |
| `D:`  | Source repos, projects, worktrees, build evidence (code/source tier)                          |
| `F:`  | Hot local memory / database / RAG / search runtime (access via service/API/CLI wrappers only) |
| `E:`  | Archive / cold storage / backups / exports / emergency spool only (no primary SQL)            |
| `G:`  | Backup target only                                                                            |


## 3. Runtime Endpoints


| Component          | Endpoint / Path                                                                         |
| ------------------ | --------------------------------------------------------------------------------------- |
| PostgreSQL cluster | `127.0.0.1:55432`                                                                       |
| `agent_core` DB    | governed canonical AgentCore DB (same cluster)                                          |
| `swarmrecall` DB   | native SwarmRecall app DB — **separate from `agent_core`; never merged** (same cluster) |
| SwarmRecall API    | `http://127.0.0.1:3300`                                                                 |
| SwarmRecall health | `http://127.0.0.1:3300/api/v1/health`                                                   |
| Meilisearch        | `http://127.0.0.1:7700`                                                                 |
| SwarmVault root    | `F:\AgentCore\agentmemory\swarmvault` (file-based; not Postgres)                        |
| Projection state   | `F:\AgentCore\agentmemory\projection-state`                                             |
| Obsidian REST      | `https://127.0.0.1:27124`                                                               |
| OpenClaw gateway   | `http://127.0.0.1:18789`                                                                |


**Forbidden port:** `:65432` has no active runtime route. Allowed only inside archived/historical evidence. Use `:55432`.

## 4. Canonical Memory Path

```text
IDE agent
  -> global-memory-gateway
  -> agent_core (127.0.0.1:55432)
  -> Invoke-AgentCoreMemoryProjector.ps1   (governed pipeline, NOT a monitor; preserved)
  -> SwarmRecall API (127.0.0.1:3300)
  -> swarmrecall DB + Meilisearch (127.0.0.1:7700)
  -> curated SwarmVault ingest (F:\AgentCore\agentmemory\swarmvault) where approved
```

Normal agents must not: raw-SQL into `agent_core` or `swarmrecall`; dual-write into both DBs; direct-write into `F:\AgentCore\agentmemory`; direct-write into the active Obsidian vault; print secrets; create `.env` files.

## 5. Gateway Tool Contract (two-tier)

**Current tools (exist now):**
`memory_append`, `memory_search`, `memory_state`

**Target tools (future — require `memory_catalog` migration; do not assume available):**
`agentcore_get_startup_context`, `agentcore_retrieve_context`, `agentcore_store_memory`, `agentcore_store_project_fact`, `agentcore_build_handoff_pack`, `agentcore_find_related_projects`, `agentcore_explain_sources`

`agentcore_check_drift` is **excluded** — drift is validator-driven, not agent-driven.

## 6. Memory System Roles

- `agent_core` = governed canonical AgentCore PostgreSQL/pgvector DB.
- `swarmrecall` DB = native SwarmRecall app DB, separate from `agent_core`.
- **SwarmRecall** = native local agent memory, semantic recall, knowledge graph, learnings, skills, shared pools (via `swarmrecall` MCP / governed wrapper).
- **SwarmVault** = local-first RAG / wiki / knowledge graph / context packs / task ledger (file-based, via `swarmvault` MCP / governed wrapper).

## 6a. Native-First Principle

SwarmRecall and SwarmVault must work **natively first**. Prove native behavior (native MCP/API health, tool discovery, `doctor`/`retrieval status`/`graph stats`) before adding AgentCore governance complexity. AgentCore wrappers, projectors, renderers, validators, and `memory_catalog` integration may **wrap** the native tools only after native behavior is proven — they must not replace or bypass native best practice. Validators must test native health first, then wrapper integration, and treat `memory_catalog`/`agentcore_`* checks as SKIP/dry-run until migrations are applied.

## 7. Swarm Ecosystem Scope

- **Core mandatory (every managed IDE):** SwarmRecall, SwarmVault.
- **Staged, developer-team runtime only:** SwarmClaw.
- **Staged / blocked unless local-only proven & approved:** SwarmRelay, SwarmFeed, SwarmDock.

## 8. Mandatory MCP Baseline (every managed IDE)

```text
arabold-docs
serena
sequential-thinking
cursor-agent-mcp
context-fabric
mcp-debugger
artiforge
global-memory-gateway
obsidian-vault
swarmrecall
swarmvault
```

Ollama is **optional only** — not a mandatory MCP baseline server.

## 9. Forbidden Active Routes

```text
context7
raw mem0
direct composio
Hostinger
hosted SwarmRecall
hosted SwarmVault
direct SQL as a normal-memory route
:65432 active runtime route
D:\MCP-Control-Plane as design authority
SwarmVault described as a Postgres database
SwarmRecall automatically using the SwarmVault DB
```

## 10. Secrets & Config

- No `.env` files anywhere in this system.
- Windows User-scope environment variables only.
- Never store or print raw secret values. Docs may name env var names and paths only.
- Live IDE configs are app-owned and are not directly edited without approval (changes flow through `docs/prompts/` per-IDE cleanup prompts).

## 11. Automation Posture

- Monitor automations are removed/deferred. The governed memory projector (`Invoke-AgentCoreMemoryProjector.ps1`) is preserved.
- Retained scheduled work: Postgres/SwarmRecall/Meilisearch startup ownership, nightly backup, nightly restore test, weekly maintenance, 2-hour memory projection, and manual validators.

## 12. Git Policy

- Working repos under `D:\github` use normal GitHub `origin` remotes (same URL for fetch and push). GitHub is the current remote mirror and automation trigger target.
- **Push after every completed task.** A completed task means all requested changes are done and validated, or the task is blocked and a blocker report with exact next commands was written to source control. Push the source-controlled delta immediately after passing validation and a secret/junk scan.
- Do not pull, fetch, merge, rebase, or remote-update unless the operator explicitly asks.
- Never force-push without explicit operator approval.
- Never stage live secret-bearing configs, rendered PAT URLs, DB dumps, caches, node_modules, runtime artifacts, Docker inspect output with secrets, `.env` files, or `F:\AgentCore` runtime state.
- If a task changes only live runtime state or live IDE configs, write an evidence report to `artifacts/task-runs/` or `artifacts/rollout-*/` and commit/push that instead.
- If there are no source-controlled changes and no runtime/live-config changes: report "no source-controlled delta; no push required" — do not create an empty commit.
- For remote lookups, use a separate read-only clone under `D:\github-readonly\<repo>`.

## 13. Hard Stop Gates (require explicit operator approval)

```text
- DB migration apply / live DDL
- live IDE config edits
- scheduled task changes
- service start/stop
- Docker mutation
- secret rotation/removal
- SwarmVault source deletion
- raw writes to F:\AgentCore
- raw writes to the active Obsidian vault
- remote pull/fetch/merge/rebase
```

## 14. Change Policy

`PROJECT_ANCHOR.md` is stable. It must not be edited without explicit operator approval. Temporary status, acceptance results, and next-step checklists belong in the current-state context block and handoff, not here.