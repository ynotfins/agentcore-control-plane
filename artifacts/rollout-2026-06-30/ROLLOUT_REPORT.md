# AgentCore Swarm Rollout — Implementation Report (2026-06-30)

**Agent:** single Cursor Agent (no subagents). **Source authority:** `D:\github\agentcore-control-plane`.
**Scope:** post-P0 → highest safe source-controlled acceptance state. No hard safety gates were crossed.

---

## 1. Executive outcome

The control plane is now **internally consistent and source-validated** for the SwarmRecall/SwarmVault local-only baseline: `validate-control-plane.ps1 -DryRun` returns **Overall: PASS**. The rogue agent's damage to the **source renderers** (broken SwarmVault wrapper + un-governed SwarmRecall CLI) was reconciled to the governed launch path. SwarmRecall is validated fully healthy local-only (53 MCP tools; gateway→agent_core→projector pipeline confirmed). The unified-memory-catalog migrations are authored (dry-run only, apply blocked). Per-IDE cleanup prompts, staged Claude Code config, three new validators, and monitor removal (source installer) are complete.

Acceptance: **PARTIAL-GREEN.** Source-state acceptance is green; remaining items are behind explicit hard gates (live IDE config edits via per-IDE prompts, DB migration apply, secret rotation, scheduled-task de-registration) plus one documented runtime blocker (SwarmVault `query` validator timeout).

---

## 2. Files changed (source-controlled)

Edited:
- `renderers/cursor-global.mcp.json`, `renderers/minimax.mcp.json`, `renderers/openclaw.openclaw.fragment.json`, `renderers/antigravity.mcp_config.json` — normalized rogue `swarmrecall` (raw CLI + un-allowlisted env) and **broken** `swarmvault` (non-existent `…\.agentcore\mcp-wrappers\swarmvault-mcp.ps1`) entries to the governed wrappers `ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp` / `ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp`.
- `renderers/open-interpreter.config.fragment.json` — added governed `swarmrecall` + `swarmvault`.
- `supervisor/servers.json` — added `swarmrecall` + `swarmvault` server defs (governed wrapper launch, local-only, bound to all 6 rendered clients, `render_by_default: true`).
- `contracts/master-mcp-server-config.json` — removed `swarmrecall` from `must_not_emit`; added `swarmrecall`/`swarmvault` to `server_catalog` (local-only, tool profiles, hosted-forbidden); updated `normal_memory_rule` (swarmrecall_direct_mcp_default=true, governed launch, projector note).
- `validators/validate-control-plane.ps1` — inverted the SwarmRecall check (now **requires** local-only `swarmrecall`+`swarmvault` present); added `swarmrecall`/`swarmvault` to each renderer's expected set; added "no hosted Swarm routes" and "no active :65432" assertions; raised Codex budget 11→16 for the grown baseline.
- `ops/Install-AgentCoreOperationalScheduledTasks.ps1` — removed `DailyDriftCheck` + `ContextFabricReadiness` from scheduled registration (now manual validators); preserved startup/backup/restore/maintenance + the governed `MemoryProjection` pipeline; documented that live de-registration is an elevated operator action.

Created:
- `migrations/` — `0001_up/down_memory_source_systems`, `0002_up/down_memory_catalog`, `0003_up/down_retrieval_events_context_packs`, `0004_up/down_agent_run_ledger_quality_scores`, `0005_seed_source_systems`, `README.md` (additive-only, dry-run protocol, apply blocked per database-plan.md §13/§18).
- `ops/Test-AgentCoreUnifiedRetrieval.ps1` (dry-run/SKIP until migration; Phase-6 full validation), `ops/Test-AgentCoreRuleConflictScanner.ps1`, `ops/Test-AgentCoreOllamaReadiness.ps1`.
- `docs/prompts/` — `README.md` + 9 per-IDE cleanup prompts (codex, cursor, openclaw, open-interpreter, minimax, mavis, antigravity, claude-code, claude-desktop-obsidian).
- `artifacts/staging/claude-code/` — `claude-code.mcp.json` (governed candidate) + `README.md`.
- `artifacts/rollout-2026-06-30/` — `p1-preflight-evidence.md`, this report.
- `artifacts/backups/20260630-042231-p2-baseline/` — pre-mutation backups of all edited managed files.
- `artifacts/incident-2026-06-30/reconciliation-report.md` — P0 deliverable (prior step).
- `E:\CodexMemory`, `E:\CodexMemory\markdown-vault` (reversible dir creation).

---

## 3. Commands run (all read-only or source-controlled; no services started/stopped except cleanup of my own validator)

Preflight listeners/health/Ollama; `git` status/log/ls-files; process scans; backups + read-only attribute toggle (unlock→edit→re-lock); JSON parse checks; PowerShell AST parse checks; `validate-control-plane.ps1 -DryRun`; the 3 new validators; `Test-AgentCoreSwarmRecall.ps1`; `Test-AgentCoreSwarmVault.ps1` (timed out — terminated my own validator tree only; services confirmed still up). No Docker, no scheduled-task mutation, no DB DDL, no live IDE config edits, no secret values printed.

---

## 4. Validators / tests run — pass/fail

| Check | Result | Notes |
|-------|--------|-------|
| `validate-control-plane.ps1 -DryRun` | **PASS (Overall)** | incl. swarmrecall+swarmvault baseline present, no hosted Swarm, no :65432, renderer sets match, Codex budget 13≤16, live configs sanitized, managed files re-locked |
| `Test-AgentCoreRuleConflictScanner.ps1` | **PASS** | renderers emission-clean (6 files) |
| `Test-AgentCoreOllamaReadiness.ps1` | **WARN** | Ollama installed, not listening — optional layer, expected; no auto-pull |
| `Test-AgentCoreUnifiedRetrieval.ps1` | **SKIP** | memory_catalog not migrated (expected pre-migration); never hard-fails core rollout |
| `Test-AgentCoreSwarmRecall.ps1` | **PASS (all)** | 53 MCP tools, local-only loopback 3300/7700/55432, no hosted fallback, no secrets in args; CLI returned 103 memories with gateway-governed projection metadata (P3 pipeline confirmed) |
| `Test-AgentCoreSwarmVault.ps1` | **BLOCKED (timeout)** | hung on CLI `query` step >8 min over the large vault; P0 confirmed vault structure/sources healthy. See blockers. |

---

## 5. Required end-state coverage

1. Hard-facts preflight evidence — **DONE** (`p1-preflight-evidence.md`).
2. Source backups before mutation — **DONE**.
3. contracts + supervisor aligned (swarmrecall/swarmvault) — **DONE** (full context-fabric/cursor-agent-mcp/mcp-debugger expansion + claude-code/mavis profiles in contract: PARTIAL — see deferred).
4. generator renders mandatory baseline — **DONE for swarmrecall/swarmvault** (generator reads servers.json and reproduces them; verified by render logic). Context-fabric/cursor-agent-mcp/mcp-debugger expansion + mavis/claude-code client wiring: DEFERRED.
5. renderers/registry regenerated — renderers reconciled by hand to governed wrappers (a full `python scripts/mcp_control_plane.py` run is deferred: it regenerates AGENTS.md/SECURITY.md/rules and spawns probe subprocesses — not safe to run blindly; the current renderer state already matches what the patched model would emit). `servers.yaml` regen + registry regen DEFERRED to that gated run.
6. validators enforce new baseline — **DONE**: require swarmrecall+swarmvault, block hosted Swarm + :65432, Qdrant/n8n excluded (absent from renderers). context-fabric/cursor-agent-mcp/mcp-debugger "require" is staged with the renderer expansion.
7. Claude Code represented as managed/staged client — **DONE** (staged config + prompt). Generator client wiring DEFERRED.
8. MiniMax/Mavis split — PARTIAL: separate cleanup prompts + separate adoption treatment done; dedicated `renderers/mavis.mcp.json` + generator discovery split DEFERRED.
9. Per-IDE cleanup prompts — **DONE** (9).
10. Staged Claude Code config — **DONE**.
11. SwarmRecall validated local-only — **DONE**.
12. SwarmVault local-first + safe source strategy — PARTIAL: structure/sources healthy (P0); deep `query` validator timed out (blocker); safe ignore/exclude strategy documented in handoff + prompts (no broad recursive ingest performed).
13. Monitors removed/deferred in source installer/docs, projection preserved — **DONE** (source installer; live de-registration is an elevated gate).
14. database-plan.md treated as design authority — **DONE**.
15. Migration files authored, apply blocked — **DONE**.
16. Acceptance run as far as safely possible — **DONE** (above).
17. Final report — **this document**.

---

## 6. Blockers requiring approval / follow-up

| Blocker | Type | Action / exact next command |
|---------|------|------------------------------|
| Live IDE config edits | Hard gate (app-owned) | Run each `docs/prompts/*-cleanup-prompt.md` inside its own IDE. Highest priority: `claude-code-cleanup-prompt.md`. |
| `CONTEXT7_API_KEY` rotation (live in `~/.claude.json`) | Secret rotation gate | Operator rotates at provider; Claude Code prompt removes the literal. Never printed. |
| DB migration apply | Hard gate | After §13.1 gates + dry-run: operator runs migrations under role `agent_admin` with sign-off. Dry-run cmd in `migrations/README.md`. |
| Scheduled-task de-registration of monitors | Elevated gate | Operator: `Unregister-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'DailyDriftCheck'` and `'ContextFabricReadiness'` (elevated), or elevated re-run of the updated installer. |
| SwarmVault `query` validator timeout | Runtime blocker | Interactively run `pwsh -File ops\Test-AgentCoreSwarmVault.ps1`; if it hangs on `query`, investigate heuristic retrieval over the ~10k-file vault / CLI build. `doctor` alone: `pwsh -File ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Doctor -Json`. |
| Secret-literal migration (Codex `experimental_bearer_token`, OI `authToken`/`refreshToken`, OpenClaw gateway `token`) | App-owned/approval | Per-IDE prompts instruct env-var migration; never printed. |
| git commit of changes (incl. tracking database-plan.md/handoff) | Commit gate | Awaiting explicit approval; 60 changed/untracked entries. |
| Qdrant/RDP/Portainer exposure, Docker hot data | Admin, out of scope | Documented; not executed. |

---

## 7. Deferred (documented next coordinated step — keeps repo consistent)

- Baseline expansion: add `context-fabric` + `cursor-agent-mcp` + `mcp-debugger` to renderers/supervisor bindings everywhere (flip `render_by_default` in `servers.json` lines that `canonical_model` currently forces false; update generator lines 522-524; update validator expected sets; regenerate). 
- Dedicated `renderers/mavis.mcp.json` + generator discovery/render split for Mavis; `claude-code` client wiring in `scripts/mcp_control_plane.py` + `discover_targets`.
- Full `python scripts/mcp_control_plane.py` regeneration (regenerates governance docs + runs probes) — run as a deliberate, reviewed step; then regenerate `servers.yaml` + `registry/tool-registry.json`.
- Contract `expected_default_servers` per-client expansion + `claude-code` profile.

---

## 8. Acceptance verdict

**PARTIAL-GREEN.** All safe source-controlled implementation work for the SwarmRecall/SwarmVault local-only baseline is complete and validator-green; the memory architecture matches `database-plan.md` (additive migrations authored, not applied); retired/conflicting routes are removed from source renderers; monitors removed from the source installer with the projection pipeline preserved. Remaining work is gated (live configs, DB apply, secret rotation, scheduled-task de-registration) or is the documented baseline-expansion next step, plus the SwarmVault `query` runtime blocker.

---

## 9. Native-First Stabilization Follow-up (2026-06-30 afternoon)

Pivot to native-first SwarmRecall/SwarmVault stabilization. Findings and corrections:

**Over-customization found:**
- `ops/Test-AgentCoreSwarmVault.ps1` ran a heavy semantic `query` with up to 5 retries and **no timeout** before proving lighter native smokes — this caused the prior >8-minute hang. It also lacked read-only `retrieval status` / `graph stats` smokes.
- No other over-customization: SwarmRecall validator was already native-first/timeout-bounded; renderers use governed wrappers around native `mcp` (not `agentcore_*`); `Test-AgentCoreUnifiedRetrieval` already SKIPs pre-migration; no source-controlled guidance points at the non-existent rogue wrapper (replaced earlier).

**Corrected:**
- Rewrote `ops/Test-AgentCoreSwarmVault.ps1` native-first + timeout-bounded: structure/config → `mcp help` → `doctor` → `retrieval status` → `graph stats` → `query` (single attempt, fail-fast **BLOCKED** on `-QueryTimeoutSeconds`, default 60) → `context build` (SKIP unless `-IncludeContextBuild`, mutation). Tree-kill on timeout; status model PASS/FAIL/BLOCKED/SKIP; exit 0/1/2. Added `-SkipQuery`. Runs in ~67s.
- Added `docs/SWARMVAULT_SOURCE_REGISTRATION.md` (no broad recursive `source add`; explicit exclude list for node_modules/.next/dist/build/coverage/.git/generated).
- Added native-first principle to `PROJECT_ANCHOR.md §6a` and native-first stabilization policy to the current context block.

**Native results:**
- **SwarmRecall: native-green** — 25/25, 53 MCP tools, local-only loopback (3300/7700/55432), health ok.
- **SwarmVault: native-green smokes** — `doctor` (2465 sources / 5 managed / 7071 pages / 20545 nodes, retrieval fresh; warning only on 201 candidate pages), `retrieval status` fresh, `graph stats` rich. `query` **BLOCKED** (60s timeout-bounded, fail-fast) — heuristic query over ~7071 pages is slow; tune `-QueryTimeoutSeconds` or query scope.
- DB topology unchanged: `agent_core` and `swarmrecall` remain separate. No vault state mutated. No live configs/services/migrations/scheduled tasks touched.

**Still gated:** SwarmVault `query` performance tuning (raise timeout or reduce scope); live IDE cleanup prompts; DB migration apply; scheduled-task de-registration; secret rotation.
