# M6 Exit Evidence — Durable LangGraph Autonomous Workflow

**Status:** PASSED  
**Completed on:** 2026-07-16 UTC  
**Branch:** `task/authority-reconciliation`  
**Acceptance run:** `20260716063458`  
**Gateway:** `agentcore-gateway` at `http://127.0.0.1:8080/mcp` (unchanged)  
**Upstream identity:** `agentcore-memory` (unchanged, 10 tools)  
**Rollback point:** last accepted LangGraph checkpoint + prior capability profile revision

---

## Package Versions

| Package | Version |
| --- | --- |
| `langgraph` | 1.2.5 |
| `langgraph-checkpoint-postgres` | 3.1.0 |
| `psycopg` | 3.3.4 |
| `psycopg-pool` | 3.3.1 |

---

## Migration Applied

| File | Version |
| --- | --- |
| `migrations/m6/001_up_langgraph_workflow.sql` | `m6.001` |
| `migrations/m6/001_down_langgraph_workflow.sql` | rollback available |

Schema tables created (wf_ prefix, agentcore schema):

```
wf_runs            wf_charters        wf_milestones
wf_macro_steps     wf_micro_steps     wf_checklist_items
wf_gate_evals      wf_human_pauses    capability_profiles
wf_ab_experiments  wf_critic_runs     wf_evidence
wf_scope_baselines
```

LangGraph checkpoint tables (public schema, via `PostgresSaver.setup()`):

```
checkpoints        checkpoint_blobs    checkpoint_writes
```

---

## Workflow Implementation Paths

```
scripts/agentcore_workflow/__init__.py      — package root, version 0.6.0
scripts/agentcore_workflow/state.py         — WorkflowState TypedDict
scripts/agentcore_workflow/db.py            — PostgreSQL helpers (wf_ schema)
scripts/agentcore_workflow/gates.py         — 7 deterministic gate functions
scripts/agentcore_workflow/critics.py       — critics, scorer, judge, A/B decision
scripts/agentcore_workflow/nodes.py         — LangGraph node implementations
scripts/agentcore_workflow/workflow.py      — graph assembly + PostgresSaver
scripts/agentcore_workflow/setup_tables.py  — one-time setup runner
scripts/agentcore_workflow/tests/m6_acceptance.py — 18-check acceptance harness
scripts/memory_platform/Test-M6LangGraphWorkflow.ps1 — PS wrapper
```

---

## Persistence Location

| Data | Location |
| --- | --- |
| LangGraph checkpoints | PostgreSQL 18 `agent_core`, `public.checkpoints*` (F:) |
| Workflow run state | `agentcore.wf_runs` (F:) |
| Milestone/Macro/Micro/checklist | `agentcore.wf_milestones/wf_macro_steps/wf_micro_steps/wf_checklist_items` (F:) |
| Gate evaluations | `agentcore.wf_gate_evals` (F:) |
| Human pauses | `agentcore.wf_human_pauses` (F:) |
| Capability profiles | `agentcore.capability_profiles` (F:) |
| Critic/scorer/judge runs | `agentcore.wf_critic_runs` (F:) |
| Evidence | `agentcore.wf_evidence` (F:) |
| Scope baselines | `agentcore.wf_scope_baselines` (F:) |
| A/B decisions | `agentcore.wf_ab_experiments` (F:) |

---

## Acceptance Results (18/18 PASS)

| # | Check | Result |
| ---: | --- | --- |
| 1 | PostgreSQL-backed LangGraph checkpoints | PASS — checkpoint_tables=3 |
| 2 | Workflow resume after process restart | PASS — run found by UUID after register |
| 3 | Project and thread isolation | PASS — cross-project run lookup returns 0 rows |
| 4 | Persist and recover Milestone/Macro/Micro/checklist/evidence state | PASS — all rows verified |
| 5 | Block scope drift without approval | PASS — hash change detected correctly |
| 6 | Deterministic checks run before critic/judge | PASS — 4 checks run |
| 7 | Risk-selected critics (zero for low; more for high) | PASS — low=0, medium=2, high=4 |
| 8 | Deterministic scorer produces consistent 0.0–1.0 score | PASS — score=1.0000, deterministic=True |
| 9 | Independent judge (proceed/needs_operator/block) | PASS — all three verdicts confirmed |
| 10 | Human pause recorded and resolved; run status restored | PASS — resolution=approved, run=running |
| 11 | Milestone tool activated via PostgreSQL capability profile | PASS — state=milestone_active |
| 12 | JIT lease created and expired on step completion/timeout | PASS — before=jit_leased, after=dormant, expired=1 |
| 13 | Revoke lease; tool no longer available in project | PASS — was=jit_leased, lease_status=revoked |
| 14 | Concurrent projects cannot change each other's tool profiles | PASS — isolated=True |
| 15 | High-risk tools require operator approval flag | PASS — requires_operator=True |
| 16 | A/B skipped for low-risk; enabled for high+uncertainty≥0.5 | PASS — correct for all risk classes |
| 17 | Schema persists across restart | PASS — wf_tables=12, ck_tables=3, migration=ok |
| 18 | Memory surface intact; no IDE/Swarm changes | PASS — missing_tools=[], swarm_tables=0 |

---

## Gate Behavior

Seven deterministic gates run before any LLM critic call:

| Gate | What it checks |
| --- | --- |
| `requirement` | Required workflow state fields present and non-empty |
| `scope` | Content hash drift from baseline (fails on change without approval) |
| `arch` | No forbidden patterns (Mem0, Swarm, Docker, Redis, second vector store) |
| `doc_version` | BLUEPRINT.md exists and is current |
| `security` | No cross-project access; no secret leakage in state |
| `migration` | M6 migration applied; destructive migrations require operator approval |
| `resource` | JIT lease count reasonable; no resource overrun |

---

## Critic / Scorer / Judge Behavior

- **Deterministic checks:** 4 checks always run first (`migration_applied`, `thread_isolation`, `no_cross_project_tools`, `memory_surface_intact`).
- **Critics:** 0 for `low` risk; 2 for `medium`; 4 for `high`/`critical`.
- **Scorer:** Deterministic formula: 60% det_checks + 25% gates + 15% critics → float 0.0–1.0.
- **Judge (independent):** proceed if score≥0.85 and no failed gates; needs_operator if score≥0.60; block otherwise. Critical gates (requirement, scope, security, migration) always block on failure.

---

## Human Pause/Resume

- `create_wf_pause()` → records pause in `agentcore.wf_human_pauses`; sets wf_run status to `paused_human`.
- LangGraph `interrupt()` suspends graph execution at the `human_pause` node.
- Operator resolves via `resolve_wf_pause()` → status returns to `running`; graph resumes via `Command(resume=decision)`.
- Verified: pause_id created, resolved=approved, run status=running.

---

## Lease / Tool Lifecycle Results

| Action | Outcome |
| --- | --- |
| `set_capability_state(... 'milestone_active' ...)` | Tool visible in `get_project_tools()` |
| `create_jit_lease(... lease_seconds=1 ...)` | Tool state=`jit_leased` |
| `expire_wf_jit_leases()` after 2s sleep | Lease expired; tool state=`dormant`; removed from `get_project_tools()` |
| `revoke_lease()` on active lease | `capability_leases.status='revoked'`; tool removed from active tools |
| Project A tool in Project B | Not visible (isolation confirmed) |

---

## Concurrent-Project Isolation

- Each `wf_run` row has `project_id` FK; `assert_run_project_scope()` enforces isolation.
- `capability_profiles` are project-scoped (`UNIQUE(project_id, tool_name)`).
- `get_project_tools()` filters strictly by `project_id`.
- Test: set `tool-only-for-a` in project A → zero rows returned for project B. PASS.

---

## Rollback Procedure

1. Apply `migrations/m6/001_down_langgraph_workflow.sql` to remove all M6 agentcore tables and functions.
2. LangGraph checkpoint tables (`public.checkpoints*`) may be dropped separately with operator approval.
3. M4 `agentcore-memory` gateway continues to function; no IDE configuration change required.
4. The `agentcore_workflow/` package is Python-only; no Windows services were added.

---

## Preserved (Unchanged)

| Item | Status |
| --- | --- |
| `agentcore-gateway` Bifrost identity | Unchanged |
| `agentcore-memory` upstream identity | Unchanged |
| Existing 10-tool MCP surface | All 10 tools present |
| IDE MCP configurations | No changes |
| PostgreSQL 18 at 127.0.0.1:55433 | In use |
| Cognee promotion boundaries | Unchanged |
| Generated STATE model | Unchanged |
| Swarm ecosystem | Untouched |

---

## CHAOSCENTRAL Machine Documentation Changes

No new Windows services, scheduled tasks, or ports were added for M6. The workflow engine runs as an in-process Python library (LangGraph) called from scripts. Installed packages:

```
langgraph-checkpoint-postgres==3.1.0  (pip, system Python 3.13)
psycopg-pool==3.3.1                   (pip, system Python 3.13)
```

These are additive Python packages. No system-level configuration change occurred.
