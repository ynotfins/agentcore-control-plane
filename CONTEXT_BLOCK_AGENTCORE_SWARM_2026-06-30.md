# CONTEXT_BLOCK.md — AgentCore Swarm Rollout New-Chat Context

**Purpose:** Keep a new agent/chat aligned on the AgentCore control-plane skeleton, runtime wiring, current rollout state, hard safety gates, and next actions.  
**Date:** 2026-06-30  
**Canonical source authority:** `D:\github\agentcore-control-plane`  
**Compatibility / live-ops evidence only:** `D:\MCP-Control-Plane`  
**Current rollout status:** **PARTIAL-GREEN source-state acceptance**. Source-controlled rollout work is largely implemented and validated. Live cutover items remain approval-gated.

---

## 1. Current Operational Status

The AgentCore Swarm rollout has moved past P0 incident reconciliation and a safe source-controlled implementation pass.

### Completed / Implemented Source-Controlled Work

- P0 incident reconciliation completed:
  - Rogue processes stopped.
  - Rogue blast radius bounded to 7 live IDE configs modified in the `2026-06-30 00:42–00:45` window.
  - Broken rogue SwarmVault wrapper path identified:
    - `C:\Users\ynotf\.agentcore\mcp-wrappers\swarmvault-mcp.ps1`
    - This wrapper does **not** exist.
  - Rogue edits to source-controlled files were confirmed undone.
  - SwarmVault source state audited: `staging`, `control-plane`, `swarmrecall`, `swarmvault`, and `swarmclaw` registered ready; `swarmrelay`, `swarmfeed`, and `swarmdock` not reached.
  - `swarmclaw` OOM appears to have been process-memory pressure, not vault disk explosion; `raw/` around ~22 MB.
- Renderers normalized:
  - `cursor-global.mcp.json`
  - `minimax.mcp.json`
  - `openclaw.openclaw.fragment.json`
  - `antigravity.mcp_config.json`
  - `open-interpreter.config.fragment.json`
- Rogue broken `swarmvault` entries and raw/un-governed `swarmrecall` entries were normalized in source-controlled renderers to governed wrappers:
  - `Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`
  - `Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp`
- `supervisor/servers.json` updated with local-only `swarmrecall` and `swarmvault` server definitions, all 6 clients, render-by-default.
- `contracts/master-mcp-server-config.json` updated:
  - `swarmrecall` removed from `must_not_emit`
  - `swarmrecall` and `swarmvault` added to server catalog and memory rule
- `validators/validate-control-plane.ps1` updated:
  - SwarmRecall check inverted from forbidden to required
  - no hosted Swarm assertions added
  - no `:65432` assertions added
  - Codex budget raised `11 -> 16`
- `ops/Install-AgentCoreOperationalScheduledTasks.ps1` updated:
  - removed `DailyDriftCheck`
  - removed `ContextFabricReadiness` monitor
  - preserved startup / backup / restore / maintenance / governed `MemoryProjection` pipeline
- Migration files authored under `migrations/`:
  - `0001` through `0005` plus down files as applicable
  - **Dry-run only. Live DB apply is blocked pending operator approval.**
- New validators authored:
  - `ops/Test-AgentCoreUnifiedRetrieval.ps1`
  - `ops/Test-AgentCoreRuleConflictScanner.ps1`
  - `ops/Test-AgentCoreOllamaReadiness.ps1`
- Per-IDE cleanup prompt set created:
  - `docs/prompts/`
  - 9 per-IDE prompts plus README
- Staged Claude Code config created:
  - `artifacts/staging/claude-code/`
- Rollout evidence/artifacts created:
  - `artifacts/incident-2026-06-30/reconciliation-report.md`
  - `artifacts/rollout-2026-06-30/`
  - `artifacts/backups/20260630-042231-p2-baseline/`
- `E:\CodexMemory` and `E:\CodexMemory\markdown-vault` created.

### Current Acceptance State

- `validate-control-plane.ps1 -DryRun` → **PASS**
- `Test-AgentCoreRuleConflictScanner.ps1` → **PASS**
- `Test-AgentCoreOllamaReadiness.ps1` → **WARN**; optional layer only
- `Test-AgentCoreUnifiedRetrieval.ps1` → **SKIP** pre-migration
- `Test-AgentCoreSwarmRecall.ps1` → **PASS**
  - 53 MCP tools discovered
  - local-only loopback confirmed
  - 103 memories with gateway-governed projection metadata
  - confirms `gateway -> agent_core -> projector -> SwarmRecall` pipeline
- `Test-AgentCoreSwarmVault.ps1` → **native-green smokes; query timeout-bounded BLOCKED** (validator rewritten 2026-06-30 to be native-first and timeout-bounded)
  - native checks PASS: structure/config, `mcp help`, `doctor` (2465 sources, 5 managed sources, 7071 pages, 20545 nodes, retrieval fresh; warning only on 201 candidate pages to review), `retrieval status` (fresh), `graph stats` (rich graph)
  - `query` → **BLOCKED** via fail-fast 60s timeout (process tree killed; no infinite retry). Overall RESULT BLOCKED (exit 2) by design — native baseline health is proven.
  - `context build` → SKIP (mutates vault state; only with `-IncludeContextBuild`)
  - completes in ~67s (previously hung >8 min)
  - isolate/raise timeout:
    ```powershell
    pwsh -NoProfile -ExecutionPolicy Bypass -File ops\Test-AgentCoreSwarmVault.ps1 -SkipQuery
    pwsh -NoProfile -ExecutionPolicy Bypass -File ops\Test-AgentCoreSwarmVault.ps1 -QueryTimeoutSeconds 180
    ```

### Cutover Update (2026-06-30 evening)

- **Controlling setup baseline:** `MASTER_CONFIG_AND_PROMPT.md` (with verified canonical launchers in §4a).
- **Env:** `SWARMRECALL_API_KEY` (User) aliased from canonical `AGENT_CORE_SWARMRECALL_API_KEY` (len 48, value never printed); `SWARMRECALL_API_URL=http://127.0.0.1:3300`; SwarmRecall health `ok`.
- **Gateway launcher:** created source-controlled `ops/Invoke-AgentCoreGlobalMemoryGateway.ps1 -Mode Mcp -Platform <ide>` (uniform pwsh wrapper; sets cwd + inherits Windows env; replaces the previously-missing reference).
- **Docker legacy RETIRED:** `local-agent-stack-n8n-1` + `local-agent-stack-postgres-1` containers and their volumes removed after verified tar backup to `G:\DockerLegacyRetire-<stamp>\` (rollback manifest included). n8n / n8n-Postgres / Qdrant are NOT canonical AgentCore. `agentops-qdrant` not present. Native `agent_core` Postgres `:55432` intact.
- **E: archive USB is UNMOUNTED** — `E:\AgentCoreArchive` backup/WAL targets will fail until reconnected; G: is the available backup tier meanwhile. (Action: reconnect E:, or repoint backup/WAL to an available tier.)
- **Claude Code:** configs (`.claude.json`, `.claude\config.json`) now carry the full 11-server baseline (added `cursor-agent-mcp`/`context-fabric`/`mcp-debugger`); `context7`/`hostinger` absent. Restart Claude Code to load. Other IDEs (Cursor/Codex/OpenClaw/MiniMax/Antigravity) updated by a separate operator pass; Codex/Antigravity are operator-managed.
- **New global rule:** every new project/repo must have `AGENTS.md` + `CLAUDE.md` created (from the Root Agent Rules Template) and checked/updated regularly.

### Native-First Stabilization Policy (active)

SwarmRecall and SwarmVault are stabilized **native-first**: native MCP/API/CLI health is proven before AgentCore governance wrappers are trusted. Current status: **SwarmRecall native-green** (25/25, 53 MCP tools, local-only); **SwarmVault native-green** on doctor/retrieval/graph, with the heavy semantic `query` timeout-bounded/BLOCKED pending tuning (heuristic query over ~7071 pages / ~20545 nodes is slow). AgentCore wrappers (`Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`, `Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp`), the gateway/projector, and renderers wrap the proven native tools — they do not replace them. `memory_catalog`/`agentcore_*` checks remain SKIP/dry-run until migrations are applied.

---

## 2. Core Runtime Wiring

### Authoritative Runtime Facts

| Component | Endpoint / Path | Notes |
|---|---|---|
| PostgreSQL | `127.0.0.1:55432` | Canonical local Postgres cluster |
| `agent_core` DB | same cluster | governed AgentCore canonical DB |
| `swarmrecall` DB | same cluster | native SwarmRecall app DB; separate from `agent_core` |
| SwarmRecall API | `http://127.0.0.1:3300` | local-only |
| SwarmRecall health | `http://127.0.0.1:3300/api/v1/health` | expected healthy JSON |
| Meilisearch | `http://127.0.0.1:7700` | SwarmRecall full-text/search |
| Meilisearch health | `http://127.0.0.1:7700/health` | validate locally if needed |
| SwarmVault root | `F:\AgentCore\agentmemory\swarmvault` | file/wiki/graph/retrieval/context-pack/task-ledger based |
| Projection state | `F:\AgentCore\agentmemory\projection-state` | checkpoint/per-entry state for governed projector |
| Obsidian REST | `https://127.0.0.1:27124` | use `obsidian-vault` MCP; no raw FS writes |
| OpenClaw gateway | `http://127.0.0.1:18789` | local OpenClaw instance |
| Retired port | `:65432` | forbidden except archived/historical evidence |

### Drive Roles

| Drive | Role |
|---|---|
| `C:` | OS/apps/user profile/live IDE configs |
| `D:` | source repos, projects, worktrees, evidence |
| `F:` | hot local memory / DB / RAG / search runtime |
| `E:` | archive / cold / cache / exports / emergency spool |
| `G:` | backup target only |

### Memory Pipeline

Normal durable memory write path:

```text
IDE agent
  -> global-memory-gateway
  -> agent_core on 127.0.0.1:55432
  -> Invoke-AgentCoreMemoryProjector.ps1
  -> SwarmRecall API on 127.0.0.1:3300
  -> swarmrecall DB + Meilisearch
  -> curated SwarmVault ingest where approved
```

The projector is a governed pipeline, **not** a monitor. Preserve it.

Normal agents must not:
- raw-SQL into `agent_core`
- raw-SQL into `swarmrecall`
- dual-write into both databases
- direct-write into `F:\AgentCore\agentmemory`
- direct-write into active Obsidian vault files
- print secrets
- create `.env` files

---

## 3. MCP Baseline and Route Policy

### Mandatory All-IDE Baseline

Every managed IDE should converge to:

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

### SwarmVault Profiles

- `swarmvault-admin`: Codex, Cursor
- `swarmvault-lite`: OpenClaw, Open Interpreter, MiniMax, Mavis, Antigravity, Claude Code

### Forbidden Active Routes

These must not appear as active routes in live configs or active rules:

```text
context7
raw mem0
direct composio
Hostinger
hosted SwarmRecall
hosted SwarmVault
direct SQL normal-memory route
:65432 active runtime route
D:\MCP-Control-Plane as design authority
SwarmVault-as-Postgres
SwarmRecall auto-using-SwarmVault-DB
```

Known pre-existing issue:
- Claude Code still has active `context7`, 4× Hostinger, and a live `CONTEXT7_API_KEY` literal in `~/.claude.json`.
- Do not print the value.
- Rotation/removal is operator/provider-approved and should be handled through the Claude Code cleanup prompt.

---

## 4. database-plan.md Authority

`database-plan.md` is finalized as the schema/gateway design artifact.

Important constraints:
- It does **not** authorize live DB mutation.
- It defines future/additive schema.
- Existing tables remain untouched.
- `memory_catalog` is a future pointer/provenance truth spine.
- Raw backend artifacts are not duplicated into Postgres.
- `agent_core` and `swarmrecall` remain separate DBs.
- `SwarmVault` remains file-based and local-first.
- `LCM/lossless` is deferred unless runtime evidence proves otherwise.

### Current Gateway Tools

Use now:

```text
memory_append
memory_search
memory_state
```

### Target Gateway Contracts

Future only unless implemented/proven:

```text
agentcore_get_startup_context
agentcore_retrieve_context
agentcore_store_memory
agentcore_store_project_fact
agentcore_build_handoff_pack
agentcore_find_related_projects
agentcore_explain_sources
```

`agentcore_check_drift` is excluded; drift is validator-driven.

---

## 5. Approval Gates Not Crossed

Stop and ask for explicit approval before:

```text
- applying database migrations / live DDL
- directly editing live IDE configs
- modifying Windows scheduled tasks directly
- starting/stopping services
- mutating Docker
- rotating/removing live secret values
- deleting SwarmVault sources or runtime artifacts
- committing to git
```

Current hard blockers / approval gates:
- Live IDE cleanup prompts must be run per IDE, starting with Claude Code.
- `CONTEXT7_API_KEY` rotation/removal requires operator/provider action.
- DB migration apply requires backup, restore verify, dry-run, operator sign-off.
- Scheduled-task de-registration of removed monitors requires elevated shell.
- SwarmVault query validator timeout needs interactive isolation.

---

## 6. Known Remaining Work

### Immediate Next Step: SwarmVault Query Hang Isolation

Run from `D:\github\agentcore-control-plane`:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Doctor -Json
```

Then decide whether to adjust the SwarmVault validator query mode, timeout, query scope, index state, or source registration before relying on full `Test-AgentCoreSwarmVault.ps1`.

### Re-confirm Source Consistency

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File validators\validate-control-plane.ps1 -DryRun
```

### Per-IDE Cleanup Prompts

Run the matching prompt inside each IDE from:

```text
docs\prompts\
```

Priority order:
1. Claude Code
2. Cursor
3. Codex
4. OpenClaw
5. MiniMax
6. Mavis
7. Antigravity
8. Open Interpreter
9. Claude Desktop remediation if needed

### Deferred Baseline Expansion Step

The latest rollout report says the following remain as baseline expansion next work:
- context-fabric/cursor-agent-mcp/mcp-debugger everywhere
- Mavis renderer split
- Claude Code generator wiring
- full generator regen

Confirm whether these are already completed by current source state before redoing.

---

## 7. Git / Source-Control State

Working tree is **clean** as of 2026-06-30 afternoon session.

Latest commits on branch `codex/agentcore-swarm-automation` (pushed to `origin/main`):

```text
0ce82ac  Update Git remote policy for working repos
1085714  Checkpoint AgentCore swarm rollout source state
7042f84  Update AgentCore swarm rollout plan and handoff
823f032  Add AgentCore SwarmRecall automation ownership
```

All rollout source changes (renderers, supervisor, contract, validator, migrations, prompts, staged configs, incident and rollout reports) are committed and pushed to `https://github.com/ynotfins/agentcore-control-plane.git`.

`database-plan.md`, the handoff doc, and `contracts/master-mcp-server-config.json` are tracked and committed.

To verify cleanliness before any new work:

```powershell
Set-Location "D:\github\agentcore-control-plane"
git status --short
git log --oneline -4
```

---

## 8. Git Remote Policy

Working repos under `D:\github` use **normal GitHub `origin` remotes** (same URL for fetch and push). The push-only remote hack has been removed.

**Agents must not run `git pull`, `git fetch`, `merge`, or `rebase` in these working repos unless the user explicitly asks for remote sync.**

Normal push is allowed after local review and secret/junk scan. Never force-push without explicit operator approval.

For remote lookups, use a separate read-only clone under `D:\github-readonly\<repo>` rather than pulling into the working repos.

See `docs/GIT_PUSH_ONLY_POLICY.md` for the full policy.

---

## 9. Next-Agent Operating Rule

Proceed autonomously through safe source-controlled implementation work. Do not ask for confirmation unless hitting one of the explicit hard safety gates.

If a hard gate is reached while the operator is away:
1. stop,
2. write the blocker with exact evidence,
3. provide exact next commands,
4. do not proceed past the gate.

---

## 10. One-Page Skeleton

```text
Source authority:
  D:\github\agentcore-control-plane

Runtime:
  Postgres 127.0.0.1:55432
    DBs: agent_core, swarmrecall (separate)
  SwarmRecall API 127.0.0.1:3300 /api/v1/health
  Meilisearch 127.0.0.1:7700
  SwarmVault F:\AgentCore\agentmemory\swarmvault
  Projection F:\AgentCore\agentmemory\projection-state
  Obsidian https://127.0.0.1:27124

Memory:
  global-memory-gateway -> agent_core -> projector -> SwarmRecall + curated SwarmVault

Baseline:
  arabold-docs, serena, sequential-thinking, cursor-agent-mcp, context-fabric,
  mcp-debugger, artiforge, global-memory-gateway, obsidian-vault,
  swarmrecall, swarmvault

Current state:
  Source-state partial-green.
  SwarmRecall PASS.
  SwarmVault validator BLOCKED on CLI query hang.
  DB migrations authored but not applied.
  Per-IDE prompts generated.
  Staged Claude Code config generated.
  Monitors removed/deferred in source, projector preserved.
  Working tree clean; latest commit 0ce82ac pushed to GitHub.
  GitHub origin remotes normal (not push-only).

Next:
  1. Run SwarmVault Doctor JSON.
  2. Run source consistency validator.
  3. Run per-IDE prompts starting Claude Code.
  4. Apply DB migrations only after backup/dry-run/operator sign-off.
```
