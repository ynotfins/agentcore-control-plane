# Wildcard Tool Enforcement + Context Steward — Phase 7

**Date:** 2026-07-25

## 7A — Named tool inventories

| Server | Before | After |
| --- | --- | --- |
| `filesystem` | `["*"]` | 14 named tools (from live `filesystem-*` tools/list) |
| `context-fabric` | `["*"]` | 5 named tools (`cf_capture`, `cf_drift`, `cf_health`, `cf_log_decision`, `cf_query`) |
| `serena`, `sequential-thinking`, `depwire`, `playwright` | deferred | still `["*"]` / existing notes — next pass |

Filesystem remains bounded to `D:\github` (no whole-drive roots).

Validators: `validate_contracts.py` OK; `test_contracts.py` PASS 124.  
Bifrost restarted; `Get-BifrostStatus.ps1` → memory=10, router=4, skills_hub=3 (unchanged).

## 7B — Context Steward

| Artifact | Path |
| --- | --- |
| Policy | `contracts/context-steward-policy.json` |
| Migration | `migrations/m6/002_up_context_steward.sql` (+ down) |
| Worker | `scripts/agentcore_workflow/context_steward.py` |
| Non-canonical projection | `.agentcore/MILESTONE_DELTA.md` (generated; not authority) |

Applied tables to `agent_core`; `--check` run for `agentcore-control-plane` returned clean findings.

Acceptance injections (missed event / duplicate / wrong-drive / stale / restart) remain **operator follow-up** for full soak; schema + policy + bounded runner are live.

**Signal:** `PHASE7_WILDCARD_AND_STEWARD_BASELINE_LIVE`
