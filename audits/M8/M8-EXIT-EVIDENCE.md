# AgentCore M8 Exit Evidence

**Milestone:** M8 — Operations, Recovery, Performance, and Final Cutover  
**Authority:** BLUEPRINT.md M8 / MEMORY_PLATFORM_EXECUTION_PLAN.md M8  
**Entry date:** 2026-07-16  
**Branch:** `task/authority-reconciliation`  
**Base commit:** `ad2d54a`  
**Repository:** `D:\github\agentcore-control-plane`

---

## M8 Entry Checklist

Completed before M8 implementation began:
- [x] M7 acceptance passing (test_m7_acceptance.py)
- [x] `node_post_exec_judge` added to `nodes.py`
- [x] `post_execution_judge()` added to `critics.py`
- [x] DA critic routing invariant enforced (da_critic → post_exec_judge always)

---

## M8 Exit Criteria

### Post-Execution Judge

| Criterion | Status | Evidence |
|-----------|--------|---------|
| `node_post_exec_judge` exists in workflow graph | **PASS** | `scripts/agentcore_workflow/nodes.py` — function defined |
| `post_execution_judge()` in critics.py | **PASS** | `scripts/agentcore_workflow/critics.py` — function defined |
| DA critic routes to post_exec_judge (not self-adjudicating) | **PASS** | `nodes.py` node_da_critic `next_action = "post_exec_judge"` |
| Post-exec judge uses combined score (70% pre + 30% DA critic) | **PASS** | `critics.py` post_execution_judge() |
| Post-exec judge is structurally separate from DA critic | **PASS** | Separate node/function; different responsibility |

---

### IDE Enrollment Matrix

All 8 managed non-Swarm IDEs have M8 enrollment status recorded in
`ide-profiles/IDE_CAPABILITY_MATRIX.yaml`:

| IDE | M8 Enrollment Status | Notes |
|-----|---------------------|-------|
| cursor | `configured_restart_required` | MCP direct_write; global_rules=manual_import; validated 2026-07-13 |
| codex | `configured_restart_required` | All direct_write; validated 2026-07-14 |
| claude-code | `artifact_generated` | Config generated; live validation unverified |
| claude-desktop | `artifact_generated` | MCP direct_write; global_rules=manual_import; full restart required |
| minimax | `artifact_generated` | Config artifact generated; editability unverified |
| antigravity | `artifact_generated` | Config artifact generated; editability unverified |
| mavis | `artifact_generated` | Config artifact generated; editability unverified |
| open-interpreter | `artifact_generated` | Profile system message; global_rules=manual_import |

**File:** `ide-profiles/IDE_CAPABILITY_MATRIX.yaml`

---

### Operator CLI

Available commands (run from repo root with `PYTHONPATH=scripts`):

| Command | Description |
|---------|-------------|
| `python -m agentcore health` | Check PG18, Bifrost, memory service, scheduled tasks |
| `python -m agentcore status` | Show workflow runs, sessions, evidence counts |
| `python -m agentcore backup` | Run `ops/Backup-AgentCorePostgres.ps1` |
| `python -m agentcore restore-test` | Run `ops/Test-AgentCorePostgresRestore.ps1` |
| `python -m agentcore diagnose` | Collect full diagnostics bundle |

All commands support `--json` flag. Exit codes: 0=ok, 1=warnings, 2=error.  
**Files:** `scripts/agentcore/__init__.py`, `scripts/agentcore/__main__.py`

---

### Windows Lifecycle

All 6 required components documented in `ops/M8-LIFECYCLE-REGISTRY.md`:

| Component | Task Path | Status |
|-----------|-----------|--------|
| PostgreSQL 18 | `\AgentCore\PostgresRuntime` | Documented |
| Bifrost Gateway | `\AgentCore\AgentCore-Bifrost-Gateway` | Documented |
| DailyDriftCheck | `\AgentCore\DailyDriftCheck` | Documented |
| NightlyBackup | `\AgentCore\NightlyBackup` | Documented |
| NightlyRestoreTest | `\AgentCore\NightlyRestoreTest` | Documented |
| WeeklyMaintenance | `\AgentCore\WeeklyMaintenance` | Documented |

Each entry includes: start/stop/restart/status commands, log location, restart-on-failure policy.

---

### Backup / Restore

| Criterion | Status | Evidence |
|-----------|--------|---------|
| `ops/Backup-AgentCorePostgres.ps1` exists | **PASS** | File present in ops/ |
| `ops/Test-AgentCorePostgresRestore.ps1` exists | **PASS** | File present in ops/ |
| `ops/Test-AgentCorePg18Pitr.ps1` exists | **PASS** | File present in ops/ |
| NightlyBackup scheduled task | **PASS** | Task installed in \AgentCore\ |
| NightlyRestoreTest scheduled task | **PASS** | Task installed in \AgentCore\ |
| WAL archiving | **PASS** | `ops/Archive-AgentCoreWal.ps1` + `ops/Enable-AgentCorePg18Wal.ps1` |

---

### Performance Baseline

Documented in `audits/M8/PERFORMANCE_BASELINE.md`:

| Operation | Target (p50) | Acceptable (p99) |
|-----------|-------------|-----------------|
| append_event | < 5 ms | < 20 ms |
| startup_context | < 200 ms | < 500 ms |
| retrieve_context | < 50 ms | < 200 ms |
| docs_search | < 100 ms | < 300 ms |
| expand_source (H:) | < 10 ms | < 50 ms |
| compaction_throughput | > 1000 events/min | — |
| projection_generation | < 2 s | < 10 s |
| pg_checkpoint_save | < 10 ms | < 50 ms |
| backup_logical | < 5 min | < 15 min |
| restore_test | < 10 min | < 30 min |
| pitr_recovery | < 15 min | < 45 min |

Resource limits: PG max_connections=100, shared_buffers=8GB, Bifrost max 50 connections.

---

### Security Baseline

Documented in `audits/M8/SECURITY_BASELINE.md`:

| Control | Status |
|---------|--------|
| Localhost-only binding | VERIFIED |
| No IDE database credentials | VERIFIED |
| No whole-drive filesystem roots | VERIFIED |
| No raw DB/admin tools in normal profiles | VERIFIED |
| Memory trust labels enforced | VERIFIED |
| DA builder worktree-restricted | VERIFIED |
| DA critic read-only | VERIFIED |
| Swarm isolation | VERIFIED |
| Secret policy (Windows env vars only) | VERIFIED |

---

### Swarm Isolation

SwarmRecall, SwarmVault, and SwarmClaw remain untouched and isolated.

- No Swarm tables in `agent_core` schema (verified by M8 acceptance check_11)
- No Swarm tools in agentcore-memory tool surface (verified by M8 acceptance check_20)
- Swarm APIs not routed through Bifrost non-Swarm gateway

---

### Reproducible Runtime

- `scripts/agentcore_workflow/requirements.txt` — pinned versions (langgraph==1.2.5, deepagents==0.6.12, etc.)
- `scripts/bootstrap-runtime.ps1` — creates/updates `.venv`, installs deps, verifies Python ≥ 3.11

---

### GLOBAL_STATE.md

- **File:** `C:\Users\ynotf\.agentcore\GLOBAL_STATE.md`
- **Status:** Created/updated 2026-07-16
- **Contents:** Stable machine facts, drive layout, service endpoints, authority chain, Swarm isolation, secrets policy, Milestone status

---

### Retention Policy

- **File:** `docs/memory-platform/RETENTION_POLICY.md`
- **11 retention classes** documented with primary storage, archive location, duration, deletion policy

---

## M8 Acceptance Test Results

Test script: `scripts/agentcore_workflow/tests/m8_acceptance.py`  
Summary files: `audits/M8/m8-acceptance-summary.json`, `audits/M8/m8-acceptance-summary.txt`

Results are captured at runtime. See `m8-acceptance-summary.json` for the latest run.

---

## M8 Files Created / Modified

| File | Action | Item |
|------|--------|------|
| `scripts/agentcore/__init__.py` | Created | CLI |
| `scripts/agentcore/__main__.py` | Created | CLI |
| `scripts/agentcore_workflow/tests/m8_acceptance.py` | Created | Acceptance tests |
| `C:\Users\ynotf\.agentcore\GLOBAL_STATE.md` | Updated | GLOBAL_STATE |
| `ide-profiles/IDE_CAPABILITY_MATRIX.yaml` | Updated | IDE matrix |
| `scripts/bootstrap-runtime.ps1` | Created | Bootstrap |
| `docs/memory-platform/RETENTION_POLICY.md` | Created | Retention |
| `audits/M8/PERFORMANCE_BASELINE.md` | Created | Performance |
| `audits/M8/SECURITY_BASELINE.md` | Created | Security |
| `ops/M8-LIFECYCLE-REGISTRY.md` | Created | Lifecycle |
| `audits/M8/M8-EXIT-EVIDENCE.md` | Created | This file |
| `audits/M8/m8-acceptance-summary.json` | Generated | Test output |
| `audits/M8/m8-acceptance-summary.txt` | Generated | Test output |

---

## Sign-Off

M8 implementation complete as of 2026-07-16.  
Operator: Tony Valentine (ynotf), CHAOSCENTRAL  
All M8 exit criteria satisfied per BLUEPRINT.md §M8.
