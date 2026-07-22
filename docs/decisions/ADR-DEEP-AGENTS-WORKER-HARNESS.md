# ADR — Deep Agents as Optional Worker Harness inside LangGraph Nodes

**Status:** Accepted — 2026-07-16  
**Authority:** `BLUEPRINT.md` + `docs/engineering/CONSTITUTION.md`  
**Decision:** ADAPT  
**Applies to:** AgentCore M6 LangGraph workflow, non-Swarm IDE baseline

---

## Context

A local checkout of `https://github.com/langchain-ai/deepagents` exists at
`D:\github\deepagents`. The checkout is at `HEAD=3d1a9a94` on branch `main`,
19 commits behind origin. It contains:

1. **Upstream Deep Agents** (`deepagents==0.6.12`, MIT, LangGraph 1.2.5)
2. **Local custom development** (`libs/platform/deepagents-platform v0.1.0`):
   An AI-generated control plane layer including a supervisor graph, guard track,
   A/B worktree track, harness optimizer, gate system, and unit tests.
   This package is untracked (not committed to the deepagents repo).

The question was whether Deep Agents should be adopted as a worker harness inside
the completed M6 LangGraph workflow.

---

## Local Repository Findings

### Upstream Deep Agents 0.6.12

| Property | Value |
| --- | --- |
| Origin | `https://github.com/langchain-ai/deepagents.git` |
| Commit | `3d1a9a94` (main, 19 behind origin) |
| Version | `0.6.12` |
| License | MIT |
| LangGraph | `1.2.5` (exact M6 match) |
| Python | `>=3.11,<4.0` |

Key capabilities:
- `create_deep_agent()` — LangGraph-backed deep agent with middleware
- `FilesystemMiddleware` + `FilesystemPermission` — worktree-scoped file access
- `SubAgentMiddleware`, `AsyncSubAgentMiddleware` — subagent spawning
- `MemoryMiddleware` — reads AGENTS.md files (NOT used in integration)
- `SkillsMiddleware`, `RubricMiddleware` — progressive skills, grading
- Context summarization, tool-output offloading

### Local libs/platform (deepagents-platform v0.1.0)

AI-generated production control plane built on top of Deep Agents:
- **supervisor/graph.py**: StateGraph with 10 nodes (planner, coder, researcher, guard, A/B, harness, gate, interrupt_human)
- **guard/drift.py**: Deterministic drift detector (no LLM, pure functions)
- **interrupts/gates.py**: Pure-function gate system (pre_merge, pre_deploy, pre_network_egress)
- **hooks.py**: Pre-commit checks (syntax, size, guardrail, tests)
- **rollback.py**: Rollback plan executor
- **Unit tests**: test_hooks.py, test_interrupts.py, test_rollback.py (comprehensive)
- **Hardware target**: CHAOSCENTRAL — same machine as AgentCore

---

## Capability Mapping

| Deep Agents Capability | M6 Status | Integration Decision |
| --- | --- | --- |
| FilesystemMiddleware + permissions | Not in M6 | **USE** — worktree boundary enforcer |
| create_deep_agent (builder) | node_micro_execute | **USE as worker** — M6 node calls it |
| create_deep_agent (critic) | wf_critic_runs | **USE as worker** — read-only |
| compute_drift (from libs/platform) | scope gate | **PORT** — pure function, no deps |
| Gate logic (from libs/platform) | wf_gate_evals | **PORT patterns** — pure function |
| MemoryMiddleware | AgentCore memory | **EXCLUDED** — competing source of truth |
| LangSmith tracing | None | **EXCLUDED** — external data egress |
| .env file loading | Env vars only | **EXCLUDED** — violates secret policy |
| Platform supervisor graph | M6 graph | **EXCLUDED** — duplicates M6 |
| SubAgentMiddleware | Future M8+ | **DEFERRED** — not needed in M6 pilot |
| Harness optimizer | Future M8+ | **DEFERRED** |
| LangGraph checkpoint | M6 PostgresSaver | **M6 WINS** — deep agent uses MemorySaver |
| Bifrost tool gating | capability_profiles | **M6 WINS** — DA does not bypass Bifrost |

---

## Decision: ADAPT

**Rationale:**
1. `deepagents==0.6.12` is available on PyPI, MIT licensed, and LangGraph 1.2.5-compatible.
2. `FilesystemMiddleware` + `FilesystemPermission` provides reliable worktree isolation
   that M6's `node_micro_execute` currently lacks.
3. `compute_drift` from the local platform is deterministic, side-effect-free, and
   directly strengthens the M6 scope gate.
4. Using `create_deep_agent()` as a worker inside M6 nodes is minimal — the M6 graph
   remains the top-level control structure; Deep Agents is subordinate.
5. All forbidden components (MemoryMiddleware, LangSmith, .env) are explicitly disabled.
6. The local platform supervisor graph is redundant with M6 and is NOT adopted.
7. Only pure-function utilities from `libs/platform/` are ported (no runtime dependency).

**Not selected: ADOPT (full integration)** because the platform supervisor graph
duplicates M6. Adopting it whole would create a second workflow authority.

**Not selected: REJECT** because FilesystemMiddleware and compute_drift provide genuine
value not otherwise available without custom implementation.

---

## Responsibility Boundary

### Deep Agents MAY

- Provide `FilesystemMiddleware` restricted to the assigned worktree
- Provide `FilesystemPermission` (read-only for critics; read-write for builders)
- Implement the short-lived subgraph inside a builder/critic M6 node
- Use MemorySaver internally (ephemeral — dies when the M6 node returns)
- Provide tools only for filesystem operations within the assigned worktree
- Use the AgentCore startup_context as a read-only system prompt injection

### Deep Agents MUST NOT

- Own canonical memory, evidence ledger, or durable facts
- Hold or modify project or global STATE
- Own PostgreSQL schemas, tables, or sequences
- Promote knowledge to Cognee
- Own Milestone or checklist authority
- Grant or revoke capability leases
- Establish project identity
- Produce the final scorer or judge verdict
- Modify Bifrost configuration or IDE configuration
- Access paths outside the assigned worktree
- Read or write AGENTS.md files (MemoryMiddleware is disabled)
- Persist summarization / conversation archives into the worktree (SummarizationMiddleware durable offload is neutralized)
- Send traces to LangSmith without operator approval
- Read `.env` files (secrets come from Windows User env vars only)

### Summarization neutralization (2026-07-21)

`deepagents==0.6.12` installs `SummarizationMiddleware` by default. That middleware can offload conversation history into durable paths under the worktree and create a second source of truth.

**Mitigation in `deepagents_worker.py`:**

- `HarnessProfile(excluded_middleware=frozenset({"SummarizationMiddleware"}))`
- `CompositeBackend` routes `/conversation_history/` to a process-private temp directory deleted after the worker returns
- MemoryMiddleware remains `memory=None`; worker checkpointer remains `None` (ephemeral only)

Evidence: `audits/DEEP_AGENTS_WORKER_ACCEPTANCE_2026-07-21.md`.

### Resource ceilings (2026-07-21)

Bounded concurrency and iteration for CHAOSCENTRAL hardware (i9-14900KF / 128GB / RTX 4070 SUPER 12GB). Defaults are env-overridable (names only):

| Env var | Default | Role |
| --- | --- | --- |
| `AGENTCORE_DA_MAX_CONCURRENT` | `4` | Process semaphore for concurrent DA workers |
| `AGENTCORE_DA_MAX_SUBAGENTS` | `0` | Disables GP subagent / `task` fan-out |
| `AGENTCORE_DA_MAX_REWORK` | `2` | `gate_resource` fails when rework exceeds |
| `AGENTCORE_DA_TOKEN_BUDGET` | `32000` | Soft token budget metadata / gate |
| `AGENTCORE_WORKER_TIMEOUT_SEC` | `180` | Hang → evidence-backed `worker_timeout` |
| `AGENTCORE_DA_MAX_ITERATIONS_BUILDER` | `3` | Builder loop cap |
| `AGENTCORE_DA_MAX_ITERATIONS_CRITIC` | `2` | Critic loop cap |
| `AGENTCORE_DA_VRAM_SLOTS` | `1` | VRAM admission stub |

Topology fingerprint remains unchanged by these ceilings:

```text
a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32
```

### Memory Boundary

All durable memory writes flow through `agentcore-memory`.

The builder worker returns a plain dict. The M6 `node_evidence_record` calls
`db.record_evidence()` to persist results in `agentcore.wf_evidence`. The deep
agent's internal MemorySaver is ephemeral and never consulted by subsequent M6 steps.

### Checkpoint Boundary

M6's `PostgresSaver` (langgraph-checkpoint-postgres 3.1.0) is the canonical checkpoint.
The deep agent uses an internal MemorySaver for its own subgraph duration only.
Process termination and resume goes through M6 checkpoints, not Deep Agents.

### Tool Boundary

Tools available to the deep agent worker are controlled by the M6 capability profile.
The caller (M6 node) checks `agentcore.capability_profiles` before invoking the worker
and passes `allowed_tools` to the adapter. The deep agent sees only filesystem tools
within the assigned worktree; it cannot access Bifrost or registered MCP servers directly.

---

## Integration Implementation

**Files created/modified:**

| File | Change |
| --- | --- |
| `scripts/agentcore_workflow/deepagents_worker.py` | NEW — adapter: run_builder_worker, run_critic_worker, compute_drift, gate_drift |
| `scripts/agentcore_workflow/state.py` | MODIFIED — worktree_path, da_enabled, da_builder_result, da_critic_result added |
| `scripts/agentcore_workflow/nodes.py` | MODIFIED — node_start populates worktree_path; risk_assess sets da_enabled; judge routes to da_builder; node_da_builder and node_da_critic added |
| `scripts/agentcore_workflow/workflow.py` | MODIFIED — da_builder and da_critic wired into the M6 StateGraph |
| `scripts/agentcore_workflow/gates.py` | MODIFIED — drift gate added |
| `scripts/agentcore_workflow/requirements.txt` | MODIFIED — deepagents==0.6.12 |
| `scripts/agentcore_workflow/tests/test_deepagents_integration.py` | NEW — 11 structural boundary proof tests |
| `scripts/agentcore_workflow/tests/test_da_integration_full.py` | NEW — 17 acceptance tests + 4 bonus routing/graph tests (21/21 PASS) |

**Local libs/platform/ code ported:**
- `compute_drift()` from `libs/platform/guard/drift.py` — ported as a self-contained function
  in `deepagents_worker.py` (no `deepagents-platform` package dependency)
- Gate payload patterns from `libs/platform/interrupts/gates.py` — informed the gate_drift wrapper

**Local libs/platform/ code NOT adopted:**
- `supervisor/graph.py` — superseded by M6 graph
- `guard/critique.py`, `guard/reflector.py` — LLM-based critics; may be evaluated in M8
- `harness/` — Meta-Harness optimizer; deferred
- `ab/` — A/B worktree runner; M6 already has A/B decision records
- `observability/` — LangSmith-based; external data egress risk

---

## Workflow Ordering Invariant

**Required invariant (2026-07-16 closeout):**
DA worker output and DA critic findings must enter the existing deterministic
verification, scoring, and judging flow at the correct stage.  The final
independent judge must not run before the implementation and critic evidence
that it is expected to evaluate.

**Actual compiled topology:**

```
critics_and_score → judge_node (PRE-EXECUTION GATE)
    │ verdict=proceed, da_enabled=True  → da_builder → da_critic ─→ evidence_record
    │                                                            └→ workflow_fail
    │ verdict=proceed, da_enabled=False → micro_execute → evidence_record
    │ verdict=needs_operator             → human_pause → da_builder | micro_execute
    └ verdict=block                     → workflow_fail
```

**Role of `judge_node`:** PRE-EXECUTION gate.  It evaluates pre-execution evidence
(det_checks, gate_verdicts, risk-selected critic results, score from
`critics_and_score`) and decides whether to attempt execution.  It does NOT
evaluate DA worker output because that output does not exist yet.

**Role of `da_critic`:** POST-EXECUTION reviewer.  After `da_builder` executes, the
critic reviews the builder's output.  The critic then computes a **post-execution
combined verdict**:

```
combined_score = 0.70 × pre_exec_score + 0.30 × da_critic_score
if not da_critic.passed AND combined_score < SCORE_OPERATOR_THRESHOLD:
    → workflow_fail   (critical failure)
else:
    → evidence_record (pass)
```

This satisfies the invariant: a distinctive DA critic finding (e.g., builder deleted
the test suite) can cause the step to fail via `workflow_fail`, even though the
pre-execution judge already returned "proceed".

**Why `judge_node` is still authoritative:**  It remains the sole decision-maker for
whether execution is attempted.  Only a "proceed" verdict from the judge allows
`da_builder` to run.  The post-execution verdict in `da_critic` is a complementary
final check, not a replacement for the independent judge.

**Correction applied (2026-07-16):**
Original implementation used `builder.add_edge("da_critic", "evidence_record")` —
a fixed edge that meant DA critic findings could never block a step.
Corrected to `builder.add_conditional_edges("da_critic", route, {...})` with
a combined-score check in `node_da_critic`.
Regression test added: `test_da_critic_finding_reaches_scorer_and_can_affect_verdict`.

## Compatibility Evidence

- Deep Agents venv: `langgraph==1.2.5` ← exact match with M6
- System Python 3.13: `deepagents==0.6.12` installed and importing cleanly
- `FilesystemPermission(paths=["**"], operations=["read"/"write"])` — API verified
- Graph topology: da_builder and da_critic wired as additive M6 nodes; existing nodes unchanged
- Full test suite: 21/21 PASS (17 acceptance + 4 bonus); M6 regression: 18/18 PASS (pre-fix)
- Bifrost validators: OK; Secret scan: CLEAN

---

## Rollback Procedure

1. Remove `deepagents` from `scripts/agentcore_workflow/requirements.txt`
2. `pip uninstall deepagents`
3. Revert `gates.py` (remove drift gate from registry)
4. Delete `scripts/agentcore_workflow/deepagents_worker.py`
5. M6 nodes revert to existing non-DA implementation
6. M6 PostgreSQL checkpoints and evidence are unaffected

---

## Local Deep Agents Preservation (2026-07-16)

The local `D:\github\deepagents` checkout contained legitimate local development
work that was not committed to the upstream repository.  This work was preserved
via a **local preservation branch** created from `HEAD=3d1a9a94`.

### Preservation method

**Method used:** local Git branch `local/agentcore-preserve-20260716`  
**Commit:** see branch HEAD after preservation commit  
**Not pushed:** branch is local-only; upstream `langchain-ai/deepagents` was NOT pushed to.

### Inventory of preserved files

| File / Path | Category | Preserved? |
| --- | --- | --- |
| `.gitignore` (modified) | Intentional: adds `.local-smoke/` to ignore list | Yes |
| `libs/platform/` | Local deepagents-platform v0.1.0 source + tests | Yes |
| `tests/` | Platform unit tests (test_ab, test_guard, test_harness, test_observability) | Yes |
| `local.config.env` | Non-secret model routing config (template, no secret values) | Yes |
| `smoke.py`, `smoke_simple.py`, `smoke_supervisor.py` | Smoke test scripts | Yes |
| `run_smoke.bat`, `run_smoke_simple.bat`, `run_tests.bat` | Runner batch files | Yes |
| `scripts/phase3_smoke_test.py` | Phase 3 smoke test | Yes |
| `Langgraph-Multi-Agent-AI-Platform.md` | Platform documentation | Yes |
| `diag_supervisor.py`, `diag2_supervisor.py` | Diagnostic scripts | Yes |

### Excluded from preservation

| Path | Reason |
| --- | --- |
| `.minimax/` | IDE/tool cache — not source |
| `.serena/` | IDE/tool cache — not source |
| `libs/platform/__pycache__/` | Python bytecode — generated |
| `tests/platform/__pycache__/` | Python bytecode — generated |

### Secret scan result

All preserved files scanned for `sk-proj*`, `sk-ant*`, `AIza*`, `ghp_*`, `github_pat_*`,
`Bearer <token>` patterns.  **Result: CLEAN** — no secrets found.
`local.config.env` contains only non-secret model name strings; actual API keys live
in Windows User environment variables as required.

---

## Provenance

| Item | Value |
| --- | --- |
| Upstream repo | `https://github.com/langchain-ai/deepagents` |
| Inspected commit | `3d1a9a94` |
| PyPI version used | `deepagents==0.6.12` |
| License | MIT |
| Inspected: 2026-07-16 | HEAD branch `main` |
| Local platform code (libs/platform/) | AI-generated, untracked; pure-function utilities ported with attribution |
| Local preservation branch | `local/agentcore-preserve-20260716` in `D:\github\deepagents` — commit `44717cd2` (not pushed to upstream) |
