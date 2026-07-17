# PROJECT ANCHOR — AgentCore Control Plane Constitution

> **STABLE / IMMUTABLE.** This is the non-negotiable project constitution. It contains no temporary rollout status.
> Do not edit without explicit operator approval.
> Document hierarchy: see `DOC_AUTHORITY.md`. Locked implementation blueprint: `BLUEPRINT.md` (level 3 in hierarchy). Memory/database implementation authority: see `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` (`database-plan.md` is historical schema evidence only).
>
> **Operator approval (2026-07-12):** This constitution edit was explicitly authorized by the Bifrost MCP Gateway cutover task. The previous §0 Native-First Swarm override remains historical for the Swarm ecosystem only; it is superseded below for **non-Swarm IDEs**.
>
> **Operator approval (2026-07-14):** The authority reconciliation task was explicitly authorized to add §0.1 (Project Execution Boundaries) and repoint the schema-design reference to the memory-platform execution plan.
>
> **Operator approval (2026-07-14):** `BLUEPRINT.md` was added as the locked implementation blueprint at hierarchy level 3. BLUEPRINT.md governs final architecture, storage roles, allocation-unit targets, lossless memory guarantees, STATE.md behavior, Cognee/Mem0 decision, Bifrost identities, Swarm isolation, and locked Milestones M0–M8 exit criteria.

---

## 0. Bifrost Gateway Override (2026-07-12, operator-approved)

> **LIVE-STATE OVERRIDE for NON-SWARM IDEs.** Bifrost native Gateway (`bifrost-http.exe`, pinned **v2.0.0-prerelease1**) is the workstation MCP gateway. Non-Swarm IDEs connect to **one** endpoint only:
>
> ```text
> agentcore-gateway  http://127.0.0.1:8080/mcp
> Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}
> ```
>
> Upstream MCP servers are registered behind Bifrost via `contracts/bifrost-upstream-mcp-registry.json` and rendered into `H:\AgentRuntime\bifrost\config.json`. IDEs must not embed the full per-server baseline.
>
> **Memory path (non-Swarm):**
>
> ```text
> IDE agent
>   -> agentcore-gateway (127.0.0.1:8080/mcp)
>   -> agentcore-memory   (stable server identity; may report degraded until the memory platform lands)
> ```
>
> **Swarm exclusion:** SwarmRecall, SwarmVault, and SwarmClaw are a **separate ecosystem**. Do not require Swarm MCP servers in non-Swarm IDE baselines. Do not depend on Swarm for AgentCore control-plane / non-Swarm IDE work. Swarm product installs remain untouched by this gateway cutover.
>
> The 2026-07-01 Native-First Swarm override (former §0) is **superseded for non-Swarm IDEs** by this section. It may still describe Swarm-product-local behavior inside the Swarm ecosystem, but it is not the mandatory MCP baseline for Cursor, Codex, Claude Code/Desktop, MiniMax, Mavis, Antigravity, or Open Interpreter.
>
> The Go SDK experiment under `experiments/bifrost-go-sdk-smoke/` is **not** the workstation MCP gateway.

---

## 0.1 Project Execution Boundaries (2026-07-14, operator-approved)

Non-negotiable invariants for every managed project:

1. **Milestone governance.** New projects use Milestones (outcome boundaries), Macro steps, Micro steps, strict checklists, evidence-backed completion, project context checkpoints, and Milestone tool audits. Policy: `docs/agent-policy/`.
2. **Progressive tool disclosure.** All approved tools remain available for activation, but only the tools needed for the current project and current Milestone are actively exposed to the model. A project begins with a safe Bootstrap profile, never with unrestricted administrative or destructive authority. The full builder catalog must not remain permanently loaded into every model turn.
3. **Milestone-gated capability leases.** Tools outside the current Milestone's active set are activated through audited, expiring leases. Runtime lease enforcement is implemented by the memory platform (PostgreSQL-backed, Milestone M6 of `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`); until then the tool manifest records policy and desired state only.
4. **Hardcoded standards.** The operating model in `docs/agent-policy/` and `contracts/global-agent-policy.yaml` is source-controlled authority; per-IDE rule renderings under `ide-profiles/` derive from it and may not contradict it.

---

## 1. Authority

- **Source / config authority:** `D:\github\agentcore-control-plane` — all governance, contracts, renderers, validators, ops scripts, migrations, and docs.
- **Bifrost runtime root:** `H:\AgentRuntime\bifrost` — live `bifrost-http.exe`, `config.json`, sqlite stores, logs, state. Not a design authority.
- **Compatibility / live-ops evidence only:** `D:\MCP-Control-Plane` — NOT a design authority. Agents must not treat it or any doc under it as current instructions.

## 2. Drive Roles

| Drive | Role |
| ----- | ---- |
| `C:`  | OS, apps, user profile, live IDE configs (app-owned; not directly edited without approval) |
| `D:`  | Source repos, projects, worktrees, build evidence (code/source tier); config authority lives here |
| `E:`  | Docs archive / cold storage / backups / exports / emergency spool only (no primary SQL) |
| `F:`  | PostgreSQL / hot indexes / hot local database & search runtime (access via service/API/CLI wrappers only) |
| `G:`  | Backup target only |
| `H:`  | Bifrost runtime, models, caches, AgentRuntime (`H:\AgentRuntime\bifrost`, Tentra data, MCP process helpers) |
| `I:`  | Disposable scratch only |
| `J:`  | Portable media / transfer only |

## 3. Runtime Endpoints

| Component | Endpoint / Path |
| --------- | --------------- |
| **AgentCore Bifrost MCP Gateway** | `http://127.0.0.1:8080/mcp` (`agentcore-gateway`) |
| Bifrost runtime | `H:\AgentRuntime\bifrost` (`bin\bifrost-http.exe`, `config.json`, sqlite under `data/` / `logs/`) |
| PostgreSQL cluster | `127.0.0.1:55432` |
| `agent_core` DB | governed canonical AgentCore DB (same cluster) |
| `swarmrecall` DB | native SwarmRecall app DB — **separate from `agent_core`; never merged** (same cluster; Swarm ecosystem only) |
| SwarmRecall API | `http://127.0.0.1:3300` (Swarm ecosystem; not required for non-Swarm IDEs) |
| Meilisearch | `http://127.0.0.1:7700` |
| SwarmVault root | `F:\AgentCore\agentmemory\swarmvault` (Swarm ecosystem; file-based) |
| Obsidian REST | `https://127.0.0.1:27124` |
| OpenClaw gateway | `http://127.0.0.1:18789` (not part of Bifrost IDE cutover) |

**Forbidden:**

- Port `:65432` — no active runtime route; archived/historical evidence only. Use `:55432`.
- Whole-drive filesystem MCP roots (`C:\`, `D:\`, `F:\`, `H:\`, home-directory-wide) in IDE or gateway configs.
- Direct PostgreSQL credentials, connection strings, or ingest passwords in any IDE MCP config.
- Embedding resolved virtual-key / API-key values in Git.

## 4. Canonical Memory Path (non-Swarm IDEs)

```text
IDE agent
  -> agentcore-gateway (http://127.0.0.1:8080/mcp + Bearer BIFROST_MCP_VIRTUAL_KEY)
  -> agentcore-memory  (stable identity; health/status tools; may be degraded)
```

When the fuller memory platform lands, keep the **`agentcore-memory`** server id stable; expand tools behind that id rather than renaming the IDE-facing identity.

Normal agents must not: raw-SQL into `agent_core` or `swarmrecall`; place Postgres secrets in IDE configs; dual-write into Swarm DBs from non-Swarm IDEs; direct-write into `F:\AgentCore\agentmemory`; direct-write into the active Obsidian vault; print secrets; create `.env` files.

## 5. Gateway Tool Contract

**IDE-visible surface:** tools exposed by Bifrost according to the active virtual-key / capability profile (see `contracts/bifrost-upstream-mcp-registry.json`).

**Stable memory identity tools (current minimal surface):**
`memory_health`, `memory_status` on `agentcore-memory`

**Project router tools:**
`project_list`, `project_activate`, `project_status`, `project_clear` on `agentcore-project-router`

Target richer `agentcore_*` memory catalog tools remain future work; do not assume they exist until migrations and platform work land.

## 6. Memory System Roles

- `agentcore-memory` = stable non-Swarm IDE memory identity (via Bifrost).
- `agent_core` = governed canonical AgentCore PostgreSQL/pgvector DB (ops/gateway internals; not direct IDE SQL).
- SwarmRecall / SwarmVault / SwarmClaw = **separate Swarm ecosystem** — not part of the non-Swarm IDE mandatory baseline.

## 7. Swarm Ecosystem Scope (independent)

- Swarm products may continue to use native SwarmRecall / SwarmVault locally inside their own ecosystem.
- **Non-Swarm IDEs must not require Swarm MCP.**
- Staged / blocked unless local-only proven & approved: SwarmRelay, SwarmFeed, SwarmDock.
- Bifrost cutover ops must not modify Swarm product installs or Swarm launchers except to **exclude** Swarm entries from non-Swarm IDE baselines.

## 8. Mandatory MCP Baseline (non-Swarm IDEs)

```text
agentcore-gateway   # sole IDE MCP entry
                    # upstream registry lives behind Bifrost
```

Canonical upstream set (behind the gateway, not pasted into each IDE) is defined in `contracts/bifrost-upstream-mcp-registry.json`. Builder profile typically includes arabold-docs, serena (via project router), sequential-thinking, cursor-agent-mcp, context-fabric, mcp-debugger, artiforge, depwire, tentra, obsidian-vault, playwright, filesystem (project-scoped), agentcore-memory, agentcore-project-router. Deferred/disabled until healthy: `depwire-cloud`, `github-mcp`.

Ollama remains optional — not a mandatory MCP baseline server.

## 9. Forbidden Active Routes

```text
context7
raw mem0
direct composio
Hostinger
hosted SwarmRecall / hosted SwarmVault as IDE defaults
direct SQL as a normal-memory route
:65432 active runtime route
D:\MCP-Control-Plane as design authority
whole-drive filesystem MCP roots
Postgres credentials in IDE MCP configs
Go SDK smoke treated as the MCP gateway
Swarm MCP required in non-Swarm IDE baselines
```

## 10. Secrets & Config

- No `.env` files anywhere in this system.
- Windows User-scope environment variables only.
- Bifrost config uses `env.NAME` references; IDE gateway clients use `${env:BIFROST_MCP_VIRTUAL_KEY}` (or materialize into live config only when the client cannot expand env headers — never commit the resolved value).
- Never store or print raw secret values. Docs may name env var names and paths only.
- Live IDE configs are app-owned; changes flow through renderers + `docs/prompts/install-agentcore-gateway-in-ide.md` / cutover ops with backup first.

## 11. Automation Posture

- Bifrost Gateway install/start/stop/test/backup/restore scripts live under `ops/bifrost/`.
- Retained scheduled work may include Bifrost logon start, Postgres/SwarmRecall/Meilisearch ownership (Swarm ecosystem), nightly backup, and manual validators.
- Monitor automations remain removed/deferred unless operator-approved.

## 12. Git Policy

- Working repos under `D:\github` use normal GitHub `origin` remotes (same URL for fetch and push).
- **Push after every completed task.** Validate narrowly, secret/junk scan, stage only source-controlled files, commit, push `origin main` (or the active feature branch when that is the task branch).
- Do not pull, fetch, merge, rebase, or remote-update unless the operator explicitly asks.
- Never force-push without explicit operator approval.
- Never stage live secret-bearing configs, rendered PAT URLs, DB dumps, caches, node_modules, runtime artifacts, `.env` files, or `F:\AgentCore` / `H:\AgentRuntime` runtime state.
- If a task changes only live runtime state or live IDE configs, write an evidence report under `artifacts/` and commit/push that instead.
- For remote lookups, use a separate read-only clone under `D:\github-readonly\<repo>`.

## 13. Hard Stop Gates (require explicit operator approval)

```text
- DB migration apply / live DDL
- live IDE config edits (except approved cutover prompts/ops)
- scheduled task changes
- service start/stop (outside approved Bifrost ops scripts when already authorized)
- Docker mutation
- secret rotation/removal
- SwarmVault source deletion / Swarm product mutation
- raw writes to F:\AgentCore
- raw writes to the active Obsidian vault
- remote pull/fetch/merge/rebase
- treating experiments/bifrost-go-sdk-smoke as production gateway
```

## 14. Change Policy

`PROJECT_ANCHOR.md` is stable. It must not be edited without explicit operator approval. Temporary status, acceptance results, and next-step checklists belong in current-state handoffs and artifacts, not here.
