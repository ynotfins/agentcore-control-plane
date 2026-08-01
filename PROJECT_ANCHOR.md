# PROJECT ANCHOR — AgentCore Control Plane Constitution

> **STABLE / IMMUTABLE.** This is the non-negotiable project constitution. It contains no temporary rollout status.
> Do not edit without explicit operator approval.
> Document hierarchy: see `DOC_AUTHORITY.md`. Locked implementation blueprint: `BLUEPRINT.md` (level 3 in hierarchy). Memory/database implementation authority: see `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` (`database-plan.md` is historical schema evidence only).
>
> **Operator approval (2026-07-12):** Bifrost MCP Gateway cutover — non-Swarm IDE single-gateway baseline.
> **Operator approval (2026-07-14):** §0.1 Project Execution Boundaries; BLUEPRINT.md locked at hierarchy level 3.
> **Operator approval (2026-07-31):** Ecosystem and drive separation reconciliation — AgentCore and Swarm are independent control planes; AgentCore hot namespace is `F:\AgentCore\...`; `H:` is reserved for Swarm after relocation acceptance.

---

## Ecosystem and Drive Separation — Read First

AgentCore and Swarm are **independent control planes**. They share a machine, not authority, runtime, memory, credentials, or backups.

| Domain | Ownership |
| --- | --- |
| AgentCore repository / design authority | `D:\github\agentcore-control-plane` |
| AgentCore hot runtime / data namespace | `F:\AgentCore\...` |
| AgentCore staging | `I:` (unless later changed by explicit authority) |
| AgentCore cold / backup namespace | `E:\AgentCore\...` only |
| Swarm hot runtime / data | `H:` exclusively (after AgentCore relocation and acceptance cutover) |
| Swarm cold / backup namespace | `E:\Swarm\...` only |

**Hard rules**

- AgentCore must not read, write, index, ingest, summarize, administer, repair, or depend on Swarm **runtime** (SwarmClaw execution, SwarmVault, Swarm schedules/agents), Swarm credentials as AgentCore baseline credentials, or Swarm backup roots as AgentCore backups.
- **Neutral shared SwarmRecall exception (AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE):** one machine-level SwarmRecall + PG16/pgvector + Meilisearch plane is **neutral infrastructure** (not AgentCore-owned runtime, not Swarm-owned runtime). AgentCore may use it **only** through the server-side `agentcore-memory` adapter. Ordinary IDEs must never embed raw SwarmRecall MCP tools or Recall API keys.
- Swarm must not reach AgentCore runtime, Bifrost, `agentcore-gateway`, AgentCore PG18 databases, repositories, IDE profiles, credentials, staging, or AgentCore backups. SwarmClaw may call the **neutral** Recall API through its own bounded adapter without calling Bifrost.
- No **AgentCore-canonical** resource (PG18 evidence/checkpoints, Bifrost, Cognee DB, IDE gateway contracts) may be jointly owned with Swarm. The neutral Recall plane is the deliberate shared exception.
- Cross-ecosystem detail belongs in an operator-carried neutral boundary contract, not in either ecosystem’s automatically ingested context.
- Historical documents that described AgentCore-**owned** SwarmRecall under `F:\AgentCore\agentmemory\...` remain **historical evidence only**. The approved model is the **neutral shared** plane (see `docs/adr/ADR-2026-08-01-neutral-shared-swarmrecall-context-engine.md`).

---

## 0. Bifrost Gateway Override (2026-07-12, operator-approved)

> **LIVE-STATE OVERRIDE for AgentCore / non-Swarm IDEs.** Bifrost native Gateway (`bifrost-http.exe`, pinned **v2.0.0-prerelease1**) is the AgentCore workstation MCP gateway. AgentCore IDEs and explicitly enrolled non-Swarm clients connect to **one** endpoint only:
>
> ```text
> agentcore-gateway  http://127.0.0.1:8080/mcp
> Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}
> ```
>
> Upstream MCP servers are registered behind Bifrost via `contracts/bifrost-upstream-mcp-registry.json` and rendered into the live Bifrost config under `F:\AgentCore\runtime\bifrost\`. IDEs must not embed the full per-server baseline.
>
> **Memory path (AgentCore / enrolled non-Swarm):**
>
> ```text
> IDE agent
>   -> agentcore-gateway (127.0.0.1:8080/mcp)
>   -> agentcore-memory   (stable ten-tool server identity; live via gateway — do not invent alternate memory MCP entries)
> ```
>
> **Swarm exclusion:** Swarm is a separate ecosystem. Do not require Swarm MCP servers in AgentCore IDE baselines. Do not depend on Swarm for AgentCore control-plane work. Do not treat Swarm repositories as AgentCore projects. Swarm product installs are outside AgentCore write authority.
>
> The 2026-07-01 Native-First Swarm override (former §0) is **superseded for AgentCore IDEs** by this section. It may still describe Swarm-product-local behavior inside the Swarm ecosystem, but it is not the mandatory MCP baseline for Cursor, Codex, Claude Code/Desktop, MiniMax, Mavis, Antigravity, Cherry Studio, or Open Interpreter when doing AgentCore work.
>
> The Go SDK experiment under `experiments/bifrost-go-sdk-smoke/` is **not** the workstation MCP gateway.

---

## 0.1 Project Execution Boundaries (2026-07-14, operator-approved)

Non-negotiable invariants for every AgentCore-managed project:

1. **Milestone governance.** New projects use Milestones (outcome boundaries), Macro steps, Micro steps, strict checklists, evidence-backed completion, project context checkpoints, and Milestone tool audits. Policy: `docs/agent-policy/`.
2. **Progressive tool disclosure.** All approved tools remain available for activation, but only the tools needed for the current project and current Milestone are actively exposed to the model. A project begins with a safe Bootstrap profile, never with unrestricted administrative or destructive authority. The full builder catalog must not remain permanently loaded into every model turn.
3. **Milestone-gated capability leases.** Tools outside the current Milestone's active set are activated through audited, expiring leases. Runtime lease enforcement is implemented by the memory platform (PostgreSQL-backed, Milestone M6); the tool manifest records policy and desired state.
4. **Hardcoded standards.** The operating model in `docs/agent-policy/` and `contracts/global-agent-policy.yaml` is source-controlled authority; per-IDE rule renderings under `ide-profiles/` derive from it and may not contradict it.
5. **Project enrollment boundary.** AgentCore-controlled IDE agents work only on AgentCore and explicitly enrolled non-Swarm projects. Swarm work is performed by Swarm’s own control plane and Swarm-owned agents. A neutral dual workspace may be used for read-only collision and boundary audits. No normal AgentCore execution session may treat a Swarm repository as an AgentCore project. No AgentCore MCP, memory, project router, or IDE profile may persist Swarm work.

---

## 1. Authority

- **Source / config authority:** `D:\github\agentcore-control-plane` — all governance, contracts, renderers, validators, ops scripts, migrations, and docs.
- **Bifrost runtime root (current state):** `F:\AgentCore\runtime\bifrost` — live `bifrost-http.exe`, `config.json`, sqlite stores, logs, state. Not a design authority.
- **Compatibility / live-ops evidence only:** `D:\MCP-Control-Plane` — NOT a design authority. Agents must not treat it or any doc under it as current instructions.
- **Swarm foreign pointer only:** `docs/boundaries/SWARM_FOREIGN_BOUNDARY.md` and `contracts/foreign-ecosystem-boundaries.yaml`. Mutable Swarm facts belong only to `D:\github\swarm-ecosystem-control`.

---

## 2. Drive Roles

| Drive | Role |
| ----- | ---- |
| `C:`  | OS, apps, user profile, live IDE configs (app-owned; not directly edited without approval) |
| `D:`  | Source repos, projects, worktrees, build evidence (code/source tier); AgentCore config authority lives here |
| `E:`  | Cold storage / archives / backups. AgentCore cold/backup data only under `E:\AgentCore\...`. Swarm cold/backup data only under `E:\Swarm\...`. No primary SQL. |
| `F:`  | AgentCore dedicated hot NVMe: PostgreSQL 18, Bifrost/AgentRuntime under `F:\AgentCore\...`, memory hot artifacts, Tentra, MCP helpers, caches (access DB via service/API/CLI wrappers only) |
| `G:`  | Second backup copy target only |
| `H:`  | Reserved exclusively for Swarm hot runtime/data after AgentCore relocation acceptance. AgentCore must not place canonical runtime, data, or rollback here. |
| `I:`  | AgentCore disposable scratch / staging only |
| `J:`  | Portable media / transfer only |

Mutable path details, transitional leftover locations, and acceptance evidence live in `CONTEXT_BLOCK.md`, current handoffs, and audits — not here.

---

## 3. Runtime Endpoints (AgentCore)

> **Operator approval (2026-07-17):** PostgreSQL 18 at `127.0.0.1:55433` is the canonical AgentCore data platform.
> PostgreSQL 16 at `127.0.0.1:55432` is **rollback/legacy evidence only** for AgentCore; it must not host AgentCore `agent_core` or `cognee_core`.
> `agent_core` and `cognee_core` live on PostgreSQL 18 (`F:\PostgreSQL18\data`).

| Component | Endpoint / Path |
| --------- | --------------- |
| **AgentCore Bifrost MCP Gateway** | `http://127.0.0.1:8080/mcp` (`agentcore-gateway`) |
| Bifrost runtime (current) | `F:\AgentCore\runtime\bifrost` |
| **PostgreSQL 18 cluster (canonical AgentCore)** | `127.0.0.1:55433` (`F:\PostgreSQL18\data`) |
| `agent_core` DB | governed canonical AgentCore DB on PostgreSQL 18 |
| `cognee_core` DB | Cognee-owned database on PostgreSQL 18 |
| PostgreSQL 16 (legacy/rollback only) | `127.0.0.1:55432` (`F:\AgentCore\database_cluster`) — AgentCore rollback/legacy evidence only |
| LangGraph Studio (dev-only) | `127.0.0.1:2024` — not a persistent Windows service; not production checkpointer |
| Obsidian REST | `https://127.0.0.1:27124` (application vault; outside default MCP surface) |

Swarm ports, Swarm databases, Swarm vault roots, OpenClaw/ClawX gateways, and Swarm MCP endpoints are **not** AgentCore constitution endpoints. Collision-avoidance pointers live in the foreign-boundary capsule and Swarm’s own control plane.

**Forbidden:**

- Port `:65432` — no active AgentCore runtime route. Use `:55433` for AgentCore canonical PostgreSQL 18.
- Port `:55432` for AgentCore `agent_core` or `cognee_core`.
- Whole-drive filesystem MCP roots (`C:\`, `D:\`, `F:\`, `H:\`, home-directory-wide) in IDE or gateway configs.
- Direct PostgreSQL credentials, connection strings, or ingest passwords in any IDE MCP config.
- Embedding resolved virtual-key / API-key values in Git.
- Treating `H:\AgentRuntime` (or any `H:` path) as AgentCore’s final runtime/data home.
- Requiring Swarm MCP servers in AgentCore IDE baselines.
- Persisting Swarm project work through AgentCore memory, project router, or IDE profiles.

---

## 4. Canonical Memory Path (AgentCore / enrolled non-Swarm)

```text
IDE agent
  -> agentcore-gateway (http://127.0.0.1:8080/mcp + Bearer BIFROST_MCP_VIRTUAL_KEY)
  -> agentcore-memory  (stable identity; ten-tool surface; live as of 2026-07-17)
```

The `agentcore-memory` server id is stable. The full ten-tool memory platform landed with M3.002 and is live-validated (Cursor enrolled 2026-07-17).

Normal agents must not: raw-SQL into `agent_core`; place Postgres secrets in IDE configs; write into Swarm DBs or vaults; direct-write into AgentCore hot artifact roots; direct-write into the active Obsidian vault; print secrets; create `.env` files; open AgentCore memory sessions against Swarm-owned repositories.

---

## 5. Gateway Tool Contract

**IDE-visible surface:** tools exposed by Bifrost according to the active virtual-key / capability profile (see `contracts/bifrost-upstream-mcp-registry.json`).

**Exact ten** `agentcore-memory` **tools (live as of M3.002, 2026-07-17):**
`memory_status`, `startup_context`, `retrieve_context`, `append_event`, `propose_fact`, `expand_source`, `session_open`, `session_close`, `build_handoff`, `docs_search`

**Project router tools:**
`project_list`, `project_activate`, `project_status`, `project_clear` on `agentcore-project-router`

No SQL, DDL, database-admin, backup-admin, or Bifrost-admin tools are exposed to normal agents. See `audits/M8/UNBOUNDED_DURABLE_MEMORY_RELEASE_ACCEPTANCE.md` §7 for live validation evidence.

---

## 6. Memory System Roles

- `agentcore-memory` = stable AgentCore IDE memory identity (via Bifrost); may project curated semantic rows into the **neutral shared SwarmRecall** plane server-side.
- `agent_core` = governed canonical AgentCore PostgreSQL/pgvector DB for exact evidence, identity, provenance, leases, and LangGraph checkpoints (not direct IDE SQL).
- Portable Context Engine = `D:\github\agentcore-context-engine` — session/context orchestration above `agentcore-memory` and neutral Recall; does not replace Cognee or PG18 evidence.
- Neutral shared SwarmRecall (API + PG16/pgvector + Meilisearch) = machine-level semantic-memory data plane (AUTH-2026-08-01).
- SwarmVault / SwarmClaw / SwarmDock / SwarmFeed / SwarmRelay / OpenClaw / ClawX = **Swarm-owned** — not part of the AgentCore IDE mandatory MCP baseline.

---

## 7. Swarm Pointer (independent — not AgentCore)

AgentCore may retain only minimum collision-avoidance facts:

- Swarm is an independent ecosystem centered on SwarmClaw.
- Intended Swarm components include SwarmClaw, SwarmRecall, SwarmVault, SwarmDock, SwarmFeed, and Swarm-owned OpenClaw agents. SwarmRelay is intended to be installed but disabled until separately approved by the Swarm build.
- Swarm owns its own runtime, databases, RAG, memory, vaults, indexes, credentials, MCP servers, agents, services, schedules, backups, and recovery. Exclusive Swarm hot ownership of `H:` is the **target after M9 acceptance**. Swarm cold/backup under `E:\Swarm\...` is operator-intent / external target (AgentCore does not implement Swarm layout).
- Cloud models are allowed for Swarm when they provide the best capability; that does not authorize Swarm local DB/RAG/memory/index/state onto AgentCore drives.
- AgentCore must not prescribe or modify Swarm’s native internal setup.
- Detailed Swarm architecture belongs only in Swarm’s control plane and an operator-carried neutral boundary contract.

---

## 8. Mandatory MCP Baseline (AgentCore / enrolled non-Swarm IDEs)

```text
agentcore-gateway   # sole IDE MCP entry
                    # upstream registry lives behind Bifrost
```

Canonical upstream set (behind the gateway, not pasted into each IDE) is defined in `contracts/bifrost-upstream-mcp-registry.json`. Builder profile typically includes arabold-docs, serena (via project router), sequential-thinking, cursor-agent-mcp, context-fabric, mcp-debugger, artiforge, depwire, tentra, playwright, filesystem (project-scoped), agentcore-memory, agentcore-project-router. Deferred/disabled until healthy: `depwire-cloud`, `github-mcp`.

Ollama remains optional — not a mandatory MCP baseline server. Swarm MCP servers must never appear in this baseline.

---

## 9. Forbidden Active Routes

```text
context7
raw mem0
direct composio
Hostinger
hosted SwarmRecall / hosted SwarmVault as IDE defaults
raw SwarmRecall MCP or Recall API keys in ordinary IDE configs
direct SQL as a normal-memory route
:65432 as an AgentCore **evidence/checkpoint** runtime route (neutral Recall PG16 on :65432 is permitted only as the shared semantic plane, never for LangGraph checkpoints)
D:\MCP-Control-Plane as design authority
whole-drive filesystem MCP roots
Postgres credentials in IDE MCP configs
Go SDK smoke treated as the MCP gateway
Swarm MCP required in AgentCore IDE baselines
AgentCore memory/project-router sessions for Swarm-owned repos
H: as AgentCore final runtime/data home
```

---

## 10. Secrets & Config

- No `.env` files anywhere in the AgentCore system.
- Windows User-scope environment variables only.
- Bifrost config uses `env.NAME` references; IDE gateway clients use `${env:BIFROST_MCP_VIRTUAL_KEY}` (or materialize into live config only when the client cannot expand env headers — never commit the resolved value).
- Never store or print raw secret values. Docs may name env var names and paths only.
- Live IDE configs are app-owned; changes flow through renderers + `docs/prompts/install-agentcore-gateway-in-ide.md` / cutover ops with backup first.

---

## 11. Automation Posture

- Bifrost Gateway install/start/stop/test/backup/restore scripts live under `ops/bifrost/`.
- Retained AgentCore scheduled work may include Bifrost logon start, PostgreSQL backup/restore tests, nightly backup, and manual validators.
- Swarm service ownership, Swarm schedules, and Swarm launchers are outside AgentCore authority.
- Monitor automations remain removed/deferred unless operator-approved.

---

## 12. Git Policy

- Working repos under `D:\github` use normal GitHub `origin` remotes (same URL for fetch and push).
- **Push after every completed task.** Validate narrowly, secret/junk scan, stage only source-controlled files, commit, push `origin main` (or the active feature branch when that is the task branch).
- Do not pull, fetch, merge, rebase, or remote-update unless the operator explicitly asks.
- Never force-push without explicit operator approval.
- Never stage live secret-bearing configs, rendered PAT URLs, DB dumps, caches, node_modules, runtime artifacts, `.env` files, or live `F:\AgentCore\runtime` / `F:\PostgreSQL18` runtime state.
- If a task changes only live runtime state or live IDE configs, write an evidence report under `artifacts/` and commit/push that instead.
- For remote lookups, use a separate read-only clone under `D:\github-readonly\<repo>`.
- Full policy: `docs/GIT_PUSH_ONLY_POLICY.md`.

---

## 13. Hard Stop Gates (require explicit operator approval)

```text
- DB migration apply / live DDL
- live IDE config edits (except approved cutover prompts/ops)
- scheduled task changes
- service start/stop (outside approved Bifrost ops scripts when already authorized)
- Docker mutation
- secret rotation/removal
- Swarm product mutation / Swarm vault deletion / Swarm schedule changes
- raw writes to F:\AgentCore outside approved ops
- raw writes to the active Obsidian vault
- remote pull/fetch/merge/rebase
- treating experiments/bifrost-go-sdk-smoke as production gateway
- treating a Swarm repository as an AgentCore-managed project
- expanding AgentCore write authority into H: or E:\Swarm\...
```

---

## 14. Change Policy

`PROJECT_ANCHOR.md` is stable. It must not be edited without explicit operator approval. Temporary status, acceptance results, and next-step checklists belong in current-state handoffs and artifacts, not here.
