# Deep Agents Worker Boundary Acceptance — 2026-07-21

**Project:** `agentcore-control-plane`  
**Scope:** Harden Deep Agents (`deepagents==0.6.12` PyPI pin) as a bounded M6 worker harness  
**Non-goals:** No 15-node topology redesign; no pull/push of `D:\github\deepagents`; no platform supervisor adoption

Authority: `docs/decisions/ADR-DEEP-AGENTS-WORKER-HARNESS.md`, `BLUEPRINT.md`, `AGENTS.md`

---

## Verdict

**ACCEPTED** — worker boundary hardened on the existing WIP (timeout / deterministic / hang modes) without changing the LangGraph topology fingerprint.

---

## Requirements checklist

| # | Requirement | Evidence |
| --- | --- | --- |
| 1 | No MemoryMiddleware; no platform supervisor; no `.env`; no Swarm; no PostgresSaver in worker | `deepagents_worker.py`: `memory=None`, `checkpointer=None`; comments forbid `.env`/Swarm; no PostgresSaver import |
| 2 | Neutralize summarization offload that would write durable archives into the worktree | HarnessProfile `excluded_middleware={"SummarizationMiddleware"}` + `CompositeBackend` routes `/conversation_history/` to a process-private temp dir (deleted after run) |
| 3 | Populate `files_changed` via git diff before/after | `_git_snapshot` + `_git_files_changed` (porcelain + `git diff --name-only HEAD`) in builder path |
| 4 | Builder R/W worktree-scoped; critic read-only | Builder `operations=["read","write"]`; critic `operations=["read"]`; `FilesystemBackend(..., virtual_mode=True)` |
| 5 | Resource ceilings (i9-14900KF / 128GB / RTX 4070 SUPER 12GB) | Env defaults + process semaphores + `gate_resource` |
| 6 | Keep / add tests | `test_deepagents_worker_boundary.py` + updated `test_08` in `test_deepagents_integration.py` |
| 7 | This acceptance audit | `audits/DEEP_AGENTS_WORKER_ACCEPTANCE_2026-07-21.md` |

---

## Resource ceiling defaults

| Env var | Default | Role |
| --- | --- | --- |
| `AGENTCORE_DA_MAX_CONCURRENT` | `4` | Bounded concurrent DA workers (process semaphore) |
| `AGENTCORE_DA_MAX_SUBAGENTS` | `0` | Disables GP subagent + excludes `task` tool |
| `AGENTCORE_DA_MAX_REWORK` | `2` | `gate_resource` fails when `da_rework_count` exceeds |
| `AGENTCORE_DA_TOKEN_BUDGET` | `32000` | Soft token budget metadata / gate |
| `AGENTCORE_WORKER_TIMEOUT_SEC` | `180` | Worker hang → evidence-backed `worker_timeout` |
| `AGENTCORE_DA_MAX_ITERATIONS_BUILDER` | `3` | Builder loop cap |
| `AGENTCORE_DA_MAX_ITERATIONS_CRITIC` | `2` | Critic loop cap |
| `AGENTCORE_DA_VRAM_SLOTS` | `1` | VRAM admission stub (one heavy GPU task) |
| `AGENTCORE_OPENROUTER_TIMEOUT_SEC` | `60` | ChatOpenRouter connect/read timeout |
| `AGENTCORE_WORKER_MODE` | `llm` | `deterministic` / `hang` for orchestration proofs |

Secrets remain Windows User-scope env vars only — no `.env` files.

---

## Files changed

- `scripts/agentcore_workflow/deepagents_worker.py` — finished WIP + boundary hardening
- `scripts/agentcore_workflow/gates.py` — expanded `gate_resource`
- `scripts/agentcore_workflow/state.py` — `da_rework_count`, `da_budget`, `da_heavy_gpu_active`
- `scripts/agentcore_workflow/nodes.py` — rework/budget wiring + per-micro reset (no topology change)
- `scripts/agentcore_workflow/tests/test_deepagents_integration.py` — fix stale `test_08`
- `scripts/agentcore_workflow/tests/test_deepagents_worker_boundary.py` — new boundary tests
- `audits/DEEP_AGENTS_WORKER_ACCEPTANCE_2026-07-21.md` — this document

---

## Topology / fingerprint impact

**None.** `NODE_ORDER`, conditional-edge option sets, and `topology_fingerprint()` payload are unchanged.

Pre-change fingerprint (captured during this work):

```text
a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32
```

Post-change fingerprint must match (validated in test run below).

---

## Test commands and results

```powershell
$env:PYTHONPATH = "D:\github\agentcore-control-plane\scripts"
python -m pytest scripts/agentcore_workflow/tests/test_deepagents_worker_boundary.py -v --tb=short
python -m pytest scripts/agentcore_workflow/tests/test_deepagents_integration.py -v --tb=short -k "not test_m6_regression and not test_04_expired and not test_07_project"
python -c "from agentcore_workflow.workflow import build_topology, topology_fingerprint; print(topology_fingerprint(build_topology()))"
```

| Suite | Result |
| --- | --- |
| `test_deepagents_worker_boundary.py` (9) | **9 passed** |
| `test_deepagents_integration.py` offline (8 selected) | **8 passed** (DB-backed 04/07 and m6_regression deselected) |
| `test_da_integration_full.py` structural | **18 passed**; 2 pre-existing failures (`test_11`, `test_da_graph_routing_structure` inspect `build_graph` source instead of `TopologyBuilder` — unrelated to this change) |
| M8 acceptance check 16 (DA bounded) | **PASS** |
| Topology fingerprint | **unchanged** `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32` |

---

## Explicit non-adoption

- Production pin remains **`deepagents==0.6.12` from PyPI** (local `D:\github\deepagents` not used).
- Deep Agents platform supervisor graph is **not** adopted.
- M6 `PostgresSaver` remains the only durable checkpoint authority.
- Durable memory remains `agentcore-gateway` → `agentcore-memory` only.
