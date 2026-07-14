# IMPLEMENTATION_SEQUENCE_AFTER_APPROVAL — CHAOSCENTRAL

**Generated:** 2026-07-03
**Purpose:** Exact, ordered, gated implementation steps for **Option A** (recommended in `FINAL_RECOMMENDATION.md`).
**Authority:** `D:\github\agentcore-control-plane` (canonical source).
**Pre-flight gate:** **`DO NOT RUN UNTIL USER APPROVES`** the recommendation in `FINAL_RECOMMENDATION.md`.

---

## 0. Pre-Flight Gate

> **DO NOT RUN UNTIL USER APPROVES.**
>
> Every step below mutates live IDE configs, repos, scheduled tasks, or secrets. None of them should run until the user has read the prior 9 reports in this directory and explicitly approved Option A.

If approval is granted, proceed in the order shown. Each step has a **verification gate** that must pass before the next step starts. A failed gate halts the sequence.

---

## 1. Sequencing Principles

1. **Secrets before configs.** Rotate secrets before editing any config that uses them.
2. **Commit before mutate.** Commit pending source edits before any further mutation.
3. **Cold-start before IDEs.** Confirm Postgres/Meilisearch/SwarmRecall API cold-start before launching any IDE on the new wiring.
4. **Native before wrapper.** Verify SwarmRecall/SwarmVault native health before launching their MCP wrappers.
5. **Projector last.** The projector is the only component that fans canonical content into multiple backends; it must run last so it sees a consistent catalog.
6. **Read-only validator at every gate.** `validators\validate-control-plane.ps1 -DryRun` runs after each major step.

---

## 2. Phase 1 — Remediate Secrets and Source State (one-time)

### 2.1 Rotate Inline Secrets

For each secret listed below, perform: (a) generate a new value at the provider; (b) set it as a Windows User-scope environment variable; (c) update the consuming config to reference `${ENV:VAR_NAME}` or equivalent; (d) restart the consuming IDE/agent.

| # | Variable (use as Windows env-var name) | Where it lived inline |
|---|----------------------------------------|------------------------|
| 1 | `OPENROUTER_API_KEY` | `C:\Users\ynotf\.openinterpreter\config.toml` (also `http_headers`) |
| 2 | `OPENCLAW_GATEWAY_TOKEN` | `C:\Users\ynotf\.openclaw\openclaw.json` |
| 3 | `CODEX_EXPERIMENTAL_BEARER_TOKEN` | `C:\Users\ynotf\.codex\config.toml` |
| 4 | `CLAUDE_CODE_API_KEY` | `C:\Users\ynotf\.claude.json` (`apiKey`) |
| 5 | `CONTEXT7_API_KEY` | `C:\Users\ynotf\.claude.json` |

**Verification gate 2.1:** `grep -r "sk-" C:\Users\ynotf\.openinterpreter` returns nothing. Same for any inline literal token in the other configs. Note: never print the new values; verify absence only.

### 2.2 Commit Pending Source Edits

| Repo | Action | Verification |
|------|--------|--------------|
| `D:\github\agentcore-control-plane` | `git add -A && git commit -m "rollout-2026-06-30 PARTIAL-GREEN: source edits, validators, contracts"` | `git status` clean |
| `D:\github\agent-team` | Commit or stash the 20 dirty entries | `git status` clean or working tree intentionally clean |
| `D:\github\autonomous-agent-team` | `git checkout -b recovery/2026-07-03 && git add -A && git commit -m "snapshot detached HEAD before recovery"`; configure remote | HEAD attached to `recovery/2026-07-03`; remote configured |

**Verification gate 2.2:** `git -C D:\github\agentcore-control-plane status` is clean. No dirty entries in any of the three repos (or dirty is intentional and documented).

### 2.3 Re-validate Control Plane

```powershell
cd D:\github\agentcore-control-plane
pwsh -NoProfile -ExecutionPolicy Bypass -File validators\validate-control-plane.ps1 -DryRun
```

Expected: `Overall: PASS`. Includes the swarmrecall+swarmvault baseline present, no hosted Swarm, no `:65432`, renderer sets match, Codex budget 13 ≤ 16, live configs sanitized, managed files re-locked.

**Verification gate 2.3:** Validator returns `Overall: PASS`.

---

## 3. Phase 2 — Bring Runtime Online (Cold-Start Chain)

### 3.1 PostgreSQL

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Start-AgentCorePostgres.ps1 -StartIfStopped
```

Then verify:
```powershell
& 'F:\AgentCore\postgres_runtime_engine\pgsql\bin\pg_isready.exe' -h 127.0.0.1 -p 55432 -d agent_core
```

Expected: `127.0.0.1:55432 - accepting connections`.

**Verification gate 3.1:** `pg_isready` exits 0; `psql -c '\dt'` on `agent_core` lists all expected tables.

### 3.2 Meilisearch

If `\AgentCore\SwarmRecallMeilisearch` Task Scheduler task is registered, trigger it; otherwise launch directly:

```powershell
& 'F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe' `
  --http-addr 127.0.0.1:7700 `
  --db-path 'F:\AgentCore\agentmemory\swarmrecall\meilisearch\data' `
  --no-analytics `
  --env development
```

**Verification gate 3.2:** `curl http://127.0.0.1:7700/health` returns `{"status":"available"}`.

### 3.3 SwarmRecall API

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Start-AgentCoreSwarmRecallApi.ps1 -StartIfStopped
```

Then verify:
```powershell
curl http://127.0.0.1:3300/api/v1/health
```

Expected: `{"status":"ok",…}`.

**Verification gate 3.3:** SwarmRecall API responds with `status: ok`. Confirms the cold-start chain (PG → Meilisearch → API) is end-to-end live.

### 3.4 SwarmVault Native Health

```powershell
node D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js doctor --json
```

Expected: structured JSON with `health: healthy`, source/page counts, no OOM warnings.

```powershell
node D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js retrieval status
```

Expected: `fresh: true`, retrieval backend `sqlite`.

**Verification gate 3.4:** Doctor + retrieval status both report healthy. (Skip `query` if slow — that's the known soft blocker.)

### 3.5 Test Wrappers (Native-First, Read-Only)

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmRecall.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmVault.ps1 -SkipQuery
```

Expected: SwarmRecall PASS (all 53 MCP tools), SwarmVault PASS on `mcp help`, `doctor`, `retrieval status`, `graph stats`.

**Verification gate 3.5:** Both validators PASS or BLOCKED-SKIP (acceptable for SwarmVault `query` until tuning).

---

## 4. Phase 3 — Emit Live IDE Wiring (Per-IDE)

### 4.1 Order

Run cleanup prompts in this order (highest blast radius first → lowest):

1. **Cursor** — `docs\prompts\cursor-cleanup-prompt.md`
2. **OpenClaw** — `docs\prompts\openclaw-cleanup-prompt.md`
3. **Codex** — `docs\prompts\codex-cleanup-prompt.md`
4. **Antigravity** — `docs\prompts\antigravity-cleanup-prompt.md`
5. **MiniMax** — `docs\prompts\minimax-cleanup-prompt.md`
6. **Mavis** — `docs\prompts\mavis-cleanup-prompt.md`
7. **Open Interpreter** — `docs\prompts\open-interpreter-cleanup-prompt.md` (after secret rotation)
8. **Claude Code** — `docs\prompts\claude-code-cleanup-prompt.md` (highest priority per rollout §6)
9. **Claude Desktop + Obsidian** — `docs\prompts\claude-desktop-obsidian-cleanup-prompt.md` (after Obsidian Local REST plugin is enabled)

### 4.2 Per-IDE Verification Gate

After each cleanup prompt completes:

- Restart the IDE.
- Open a workspace that has prior canonical memory (e.g., `D:\github\agentcore-control-plane`).
- Confirm the IDE's MCP panel shows `swarmrecall` and `swarmvault` as connected.
- Run `memory_search "<workspace path>"` via the IDE's MCP-aware tooling and confirm a non-empty result.

**Verification gate 4.2:** All 9 cleanup prompts executed; each IDE shows green MCP connections; each returns a non-empty context pack for the active workspace.

### 4.3 Re-validate Control Plane

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\validators\validate-control-plane.ps1 -DryRun
```

**Verification gate 4.3:** Validator still PASS after IDE wiring changes.

---

## 5. Phase 4 — Activate Projector + Maintenance

### 5.1 Projector

Confirm `\AgentCore\MemoryProjection` Task Scheduler task is registered. If not, run:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Install-AgentCoreOperationalScheduledTasks.ps1
```

Then trigger a manual run:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreMemoryProjector.ps1
```

**Verification gate 5.1:** Projector exits 0; new embeddings appear in `agent_core.global_vector_memory_store`; new records appear in `swarmrecall` (DB + Meilisearch index).

### 5.2 Maintenance

Confirm `\AgentCore\PostgresMaintenance`, `\AgentCore\PostgresBackup`, `\AgentCore\PostgresRestore` are registered. Same installer script.

**Verification gate 5.2:** All AgentCore scheduled tasks registered; `Get-ScheduledTask -TaskPath '\AgentCore\'` lists them.

### 5.3 De-register Monitors

Per rollout §6, operator runs (elevated):

```powershell
Unregister-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'DailyDriftCheck' -Confirm:$false
Unregister-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'ContextFabricReadiness' -Confirm:$false
```

**Verification gate 5.3:** Both tasks removed; `Get-ScheduledTask` no longer lists them.

---

## 6. Phase 5 — Backup & Restore Drill

### 6.1 Base Backup

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Backup-AgentCorePostgres.ps1
```

Expected: base backup written to `E:\AgentCoreArchive\backups_cold\pgvector\base\<timestamp>\`.

### 6.2 Off-Host Mirror

```powershell
robocopy F:\AgentCore\agentmemory E:\AgentCoreBackups\agentmemory /MIR /Z /MT:8
robocopy F:\AgentCore\agents_workspace E:\AgentCoreBackups\agents_workspace /MIR /Z /MT:8
```

Optional but recommended. Periodic (weekly) snapshot to G: for off-host retention:

```powershell
robocopy F:\AgentCore G:\AgentCoreMirror /MIR /Z /MT:8 /R:1 /W:1
```

### 6.3 Restore Drill

Restore the latest base backup into a scratch cluster (not the live one) and verify `agent_core` + `swarmrecall` are reachable.

**Verification gate 6.3:** Backup produces a valid base on E:; restore drill succeeds on scratch.

---

## 7. Phase 6 — Deferred Hardening (Optional, After PARTIAL-GREEN → GREEN)

These are the rollout-report "deferred" items. Do not execute until Phase 1–5 are GREEN.

### 7.1 Migration Apply (Hard Gate)

Per `database-plan.md` §13/§18, the migration apply gate requires:

1. Native SwarmRecall/SwarmVault are green (Phase 3.4 verified).
2. AgentCore gateway/projector wrapper verification passes (Phase 5.1 verified).
3. `migrations\0001`–`0005` dry-run is green.
4. Operator sign-off (this script does not self-execute the apply).

Only after all four, run under role `agent_admin`:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\migrations\0001_up_memory_source_systems.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\migrations\0002_up_memory_catalog.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\migrations\0003_up_retrieval_events_context_packs.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\migrations\0004_up_agent_run_ledger_quality_scores.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\migrations\0005_seed_source_systems.ps1
```

After apply, `Test-AgentCoreUnifiedRetrieval.ps1` exits PASS instead of SKIP.

### 7.2 Renderer Expansion

Add `context-fabric`, `cursor-agent-mcp`, `mcp-debugger` to renderers/supervisor bindings where `render_by_default` is currently false. Update generator lines 522–524; update validator expected sets; regenerate.

### 7.3 Dedicated Mavis Renderer

Split Mavis into its own `renderers\mavis.mcp.json` and update `scripts\mcp_control_plane.py` `discover_targets` to include Mavis.

### 7.4 Full Regeneration

Run `python scripts\mcp_control_plane.py` (full regeneration, not DRY RUN). This regenerates `AGENTS.md`, `SECURITY.md`, governance docs, and runs probes. Run as a deliberate reviewed step; then regenerate `servers.yaml` and `registry\tool-registry.json`.

### 7.5 Lossless Claw / Codex Logs Compaction

Add a scheduled compaction policy:
- Codex `logs_2.sqlite` cap at 200 MB with 7-day TTL.
- Lossless Claw `lcm.sqlite` daily vacuum + size cap with rolling compaction.

---

## 8. Failure Recovery

If any verification gate fails:

1. **Halt.** Do not proceed to the next phase.
2. **Diagnose.** Run `validate-control-plane.ps1 -DryRun` for source-level diagnosis; run `Test-AgentCoreRuntimeSuite.ps1` for runtime diagnosis.
3. **Rollback.** The pre-mutation source backups are at `D:\github\agentcore-control-plane\artifacts\backups\20260630-042231-p2-baseline\`. The pre-mutation Postgres auth copy is at `E:\AgentCoreBackups\agentcore-control-plane\20260625-225901\live-postgres-auth\20260625-231022\pg_hba.conf`. The base backup is at `E:\AgentCoreArchive\backups_cold\pgvector\base\`.
4. **Re-plan.** Update the affected phase and re-validate before retrying.

---

## 9. Summary Checklist

- [ ] **Phase 1.1** — All 5 inline secrets rotated to env vars.
- [ ] **Phase 1.2** — Source repo edits committed; working trees clean or intentional.
- [ ] **Phase 1.3** — `validate-control-plane.ps1 -DryRun` = PASS.
- [ ] **Phase 2.1** — PostgreSQL live on `:55432`.
- [ ] **Phase 2.2** — Meilisearch live on `:7700`.
- [ ] **Phase 2.3** — SwarmRecall API live on `:3300`.
- [ ] **Phase 2.4** — SwarmVault doctor + retrieval status PASS.
- [ ] **Phase 2.5** — SwarmRecall + SwarmVault validators PASS (or BLOCKED-SKIP).
- [ ] **Phase 3.1–3.9** — All 9 IDE cleanup prompts run; live MCP wiring matches renderers.
- [ ] **Phase 3.3** — `validate-control-plane.ps1 -DryRun` still PASS after IDE wiring.
- [ ] **Phase 4.1** — Projector runs and produces new embeddings + records.
- [ ] **Phase 4.2** — All AgentCore scheduled tasks registered.
- [ ] **Phase 4.3** — `DailyDriftCheck` + `ContextFabricReadiness` removed.
- [ ] **Phase 5** — Backup + restore drill succeeds.
- [ ] **Phase 6** — Deferred hardening executed only after operator sign-off.

When all boxes are checked, **PARTIAL-GREEN becomes GREEN**, and the architecture is shipped.

---

## 10. Final Note

> **DO NOT RUN UNTIL USER APPROVES.**
>
> This sequence touches live IDE configs, scheduled tasks, secrets, and source repos. Every step requires the operator's eyes and the corresponding verification gate. The architecture described in `FINAL_RECOMMENDATION.md` is the goal; this document is the path. Approval must be explicit before the first command is executed.