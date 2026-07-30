# LangGraph Production-Readiness Hardening — Acceptance Evidence

**Date:** 2026-07-29 / 2026-07-30  
**Branch:** main  
**Commit basis:** prior HEAD + this hardening diff  
**Authority:** `BLUEPRINT.md` M6/M8 + `docs/agent-policy/`

---

## Test Suite Results

| Suite | Command | Result |
|-------|---------|--------|
| Full pytest | `pytest scripts/agentcore_workflow/tests/ --ignore=fixture_e2e.py` | **66 / 66 PASS** |
| M6 acceptance | `python scripts/agentcore_workflow/tests/m6_acceptance.py` | **18 / 18 PASS** |
| M8 acceptance | `python scripts/agentcore_workflow/tests/m8_acceptance.py` | **25 / 26 PASS** |
| Topology fingerprint | `topology_fingerprint(build_topology())` | **`a86e40e8ddd0a370…` — unchanged** |

M8 check 26 (`minimax-classic=awaiting_operator_cloud_mcp_enrollment`) fails — IDE enrollment item, out of scope (see Gap 8 below).

---

## Gap-by-Gap Evidence

### Gap 1 — Formatting / Lint / Typecheck gates run real tools

**Before:** `gate_formatting`, `gate_lint`, `gate_typecheck` called `_tool_hook_gate` which returned `"pass"` with `mode: availability_only` the moment `ruff`/`mypy` were on PATH. No diff was ever inspected.

**After:**
- `deepagents_worker.py` — new `_run_tool_gates_after_build(files_changed, worktree)` runs `ruff check --output-format concise <py_files>` and `mypy --ignore-missing-imports <py_files>` after the DA agent completes. Results stored in the worker return dict under `gate_evidence`.
- `nodes.py / node_da_builder` — extracts `gate_evidence` from worker result and surfaces it as top-level `state["gate_evidence"]`.
- `nodes.py / node_post_exec_judge` — merges builder `gate_evidence` failures into `gate_verdicts` before calling `post_execution_judge`, so lint failures from the current diff block the current step (not just the next cycle).

**Tests:**
- `test_gate_formatting_real_evidence` — PASS
- `test_gate_lint_real_evidence` — PASS
- `test_gate_typecheck_real_evidence` — PASS
- `test_post_exec_judge_builder_lint_fail_blocks` — PASS

---

### Gap 2 — Depwire gate runs real evidence

**Before:** `gate_depwire_verify` was `return _tool_hook_gate(state, "depwire_verify", commands=["depwire"])` — availability check only.

**After:** `_run_tool_gates_after_build` also runs `depwire verify --path <worktree>` when `depwire` is on PATH. Result (including parsed `blast_radius_count`, `god_node_detected`, `hotspots` from JSON output) stored in `gate_evidence["depwire_verify"]`. `gate_depwire_verify` already reads `_gate_evidence` first — no change to `gates.py` needed for this gap.

**Test:** `test_gate_depwire_real_evidence` — PASS

---

### Gap 3 — Refactor-risk critic

**Before:** `CRITIC_REGISTRY["medium"]` contained only `critic_schema_change` and `critic_lease_expiry`. No complexity/hotspot critic existed.

**After:** `critics.py` — new `critic_refactor_risk(state, evidence)` added after `critic_no_swarm_mutation`:
- Consumes `gate_evidence["depwire_verify"]["blast_radius_count"]` (flag: > 5)
- Consumes `gate_evidence["depwire_verify"]["god_node_detected"]`
- Falls back to file-count heuristic (`len(files_changed) > 8`)
- Falls back to drift score heuristic (`gate_evidence["drift"]["score"] > 0.5`)
- Registered in `CRITIC_REGISTRY["medium"]`, `["high"]`, `["critical"]`

M6 acceptance check 7 confirms: medium now has 3 critics, high has 5.

**Tests:**
- `test_critic_refactor_risk_present` — PASS
- `test_critic_refactor_risk_file_count_heuristic` — PASS
- `test_critic_refactor_risk_depwire_blast_radius` — PASS

---

### Gap 4 — gate_arch consults structural evidence

**Before:** `gate_arch` searched only `macro_labels` (string join of macro step labels) for forbidden terms. Purely keyword-based.

**After:** `gates.py / gate_arch` — after the existing keyword loop, reads `state["gate_evidence"]["depwire_verify"]` for:
- `god_node_detected: true` → appended to `errors` → verdict `"fail"`
- `dependency_direction_violation: true` → appended to `errors` → verdict `"fail"`
- `len(hotspots) > 3` → appended to `warnings` → verdict `"warn"` (not an immediate fail)
- Depwire evidence absent / empty → keyword-only result unchanged (warn-and-skip posture preserved)

**Tests:**
- `test_gate_arch_structural_signals` — PASS
- `test_gate_arch_keyword_fallback_unaffected` — PASS

---

### Gap 5 — node_micro_execute silent no-op prevention

**Before:** `node_micro_execute` declared `result = {"status": "completed"}` before the `try` block. Any micro key not matching `M6.1.1`–`M6.5.1` fell through silently, marking the step completed with zero real work.

**After:** `nodes.py` — module-level constant:
```python
from .charter import M6_MICRO_STEPS as _M6_MICRO_STEPS
KNOWN_MICRO_KEYS: frozenset[str] = frozenset(m["key"] for m in _M6_MICRO_STEPS)
```
Early-return guard before the `try` block routes unknown keys to `workflow_fail` with a clear message. Derived from `charter.M6_MICRO_STEPS` (8 keys: `M6.1.1`, `M6.1.2`, `M6.2.1`, `M6.2.2`, `M6.3.1`, `M6.3.2`, `M6.4.1`, `M6.5.1`) — the prior draft hardcoded set was missing `M6.1.2`.

**Tests:**
- `test_micro_execute_unknown_key_fails` — PASS
- `test_micro_execute_all_known_keys_unaffected` (confirms `M6.1.2` present) — PASS
- M6 acceptance 18/18 PASS confirms M6 self-bootstrap unaffected

---

### Gap 5b — gate_evidence reset between micro steps

**Before:** `gate_evidence` was never cleared in `node_next_step`. Lint/depwire verdicts from step N's diff could leak into `gate_check` and `node_post_exec_judge` for step N+1.

**After:** `nodes.py`:
- `node_next_step` both branches (next-micro, next-macro) now include `"gate_evidence": {}` in their reset dicts
- `node_da_builder` early-return paths (`skipped_no_da`, rework-exhausted) now include `"gate_evidence": {}`

**Test:** `test_gate_evidence_reset_in_next_step` — PASS

---

### Gap 6 — Stale wf_runs reconciliation script

**Before:** 176 of 212 `wf_runs` rows were stuck in `status='running'` with no operator-approved resolution path.

**After:** `scripts/agentcore_workflow/reconcile_stale_runs.py` — new script with:
- `--dry-run`: show candidates only, no writes
- `--yes`: skip interactive prompt (non-interactive/CI use)
- `--hours N`: threshold (default 24)
- `--project-key K`: limit scope
- All status transitions via `db.update_run_status` (SECURITY DEFINER path, never raw `UPDATE`)
- Cross-checks `public.checkpoints` for recent activity per thread before classifying as stale

**Usage to resolve the 176 stuck rows:**
```powershell
cd D:\github\agentcore-control-plane
python -m agentcore_workflow.reconcile_stale_runs --dry-run --hours 24
# Review output, then:
python -m agentcore_workflow.reconcile_stale_runs --yes --hours 24
```

---

### Gap 7 — Uncommitted files (flagged, deferred)

The following files are in the working tree and require a separate commit:

- `ops/bifrost/Install-AgentCoreBifrostGateway.ps1`
- `ops/bifrost/Launch-AgentCoreBifrostGateway.ps1`
- `scripts/agentcore_cursor/hooks.py`

**None were modified or staged in this hardening commit.** These are pending separate commit ops.

---

### Gap 8 — M8 check 26 (out of scope, confirmed)

M8 acceptance check 26 fails because `minimax-classic` has `m8_enrollment: awaiting_operator_cloud_mcp_enrollment`, which is not in the valid_statuses set `{"live_validated", "configured_restart_required", "awaiting_operator_import", "unsupported_with_reason"}`.

This is an **IDE enrollment item** — MiniMax Classic requires a cloud MCP UI enrollment step by the operator. **No LangGraph code change can fix this.** It is the only M8 acceptance failure and is confirmed out of scope per the original task brief.

---

### Gap 9 — Stale source-grep tests fixed

**Before:** `test_11_deterministic_gates_run_before_worker` and `test_da_graph_routing_structure` both called `inspect.getsource(build_graph)`. Since `build_graph` is a thin PostgresSaver-wiring wrapper (not the topology builder), its source contained neither `"gate_check"` nor `"da_builder"` as strings. Both assertions returned `-1 < -1 → False`, causing permanent failures.

**After:** Both tests rewritten to use:
- `build_topology()` to get the `TopologyBuilder` instance
- `t.builder.nodes` to check node registration
- `NODE_ORDER` to verify ordering
- `_AFTER_DA_CRITIC`, `_AFTER_POST_JUDGE`, `_AFTER_DA_BUILDER` to verify conditional edge option sets (the canonical fingerprint contract)

**Tests:** `test_11_deterministic_gates_run_before_worker` — PASS, `test_da_graph_routing_structure` — PASS

---

## Topology Fingerprint

```
a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32
```

Unchanged. `NODE_ORDER` and all `_AFTER_*` conditional-edge option sets in `workflow.py` were not modified.

---

## Files Changed

| File | Gap(s) |
|------|--------|
| `scripts/agentcore_workflow/deepagents_worker.py` | 1, 2 |
| `scripts/agentcore_workflow/nodes.py` | 1, 5, 5b |
| `scripts/agentcore_workflow/critics.py` | 3 |
| `scripts/agentcore_workflow/gates.py` | 4 |
| `scripts/agentcore_workflow/reconcile_stale_runs.py` | 6 (NEW) |
| `scripts/agentcore_workflow/tests/test_da_integration_full.py` | 9 + new tests |
| `audits/hardening-acceptance-2026-07-29.md` | this file (NEW) |
