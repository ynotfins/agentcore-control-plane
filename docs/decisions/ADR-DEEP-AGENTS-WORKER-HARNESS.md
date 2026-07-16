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
- Send traces to LangSmith without operator approval
- Read `.env` files (secrets come from Windows User env vars only)

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

## Compatibility Evidence

- Deep Agents venv: `langgraph==1.2.5` ← exact match with M6
- System Python 3.13: `deepagents==0.6.12` installed and importing cleanly
- `FilesystemPermission(paths=["**"], operations=["read"/"write"])` — API verified
- Graph topology: da_builder and da_critic wired as additive M6 nodes; existing nodes unchanged
- Full test suite: 21/21 PASS (17 acceptance + 4 bonus); M6 regression: 18/18 PASS
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

## Provenance

| Item | Value |
| --- | --- |
| Upstream repo | `https://github.com/langchain-ai/deepagents` |
| Inspected commit | `3d1a9a94` |
| PyPI version used | `deepagents==0.6.12` |
| License | MIT |
| Inspected: 2026-07-16 | HEAD branch `main` |
| Local platform code (libs/platform/) | AI-generated, untracked; pure-function utilities ported with attribution |
