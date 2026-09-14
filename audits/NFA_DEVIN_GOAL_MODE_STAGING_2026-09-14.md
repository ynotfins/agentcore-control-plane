# nfa-platform / Devin Goal Mode staging (2026-09-14)

Evidence only. Not an authority document. Default-deny and exact-path enrollment are unchanged.

## Privilege model (unchanged)

- Devin remains Trust Class A builder on `http://127.0.0.1:18082/mcp` (`process_attested_proxy`).
- Devin must not receive `operator`, `agentcore-project-router`, a pasted builder bearer, or enrollment-edit rights.
- `scripts/agentcore_project_boundary.py` `match_enrolled_path` is exact path equality only. Enrolling a parent does not enroll children.

## Enrolled `nfa-platform` paths

- `D:\github\nfa-platform`
- `D:\agentcore-worktrees\nfa-platform`
- `D:\agentcore-worktrees\nfa-platform\goal-staging-001`

Starter worktree: branch `goal/staging-001` at `a4c68f1c615041adb61f8d69b0112f03eb929c22` created from nfa `integration/commercial-readiness`. No nfa product-code edit. No Swarm/`H:` path.

## New Goal Mode worktree enroll procedure

When Devin Goal Mode creates a NEW worktree under `D:\agentcore-worktrees\nfa-platform\<name>`:

1. STOP Devin from editing `contracts/agentcore-project-enrollment.json`.
2. Operator/Cursor enrolls that EXACT path:
   ```text
   scripts\.venv\Scripts\python.exe scripts\enroll_exact_project_path.py --caller cursor --project-key nfa-platform --path "D:\agentcore-worktrees\nfa-platform\<name>"
   ```
3. Validate `require_enrolled_path` for that path and confirm a non-enrolled sibling still fails.
4. Only then resume Goal Mode in that worktree.

Helper callers are `cursor` or `operator` only. `devin` is rejected.

## Identity stop (not weakened)

Unsigned Devin/MCP memory for `project_key=nfa-platform` returns `device_assertion_required`. Devin has no Stage B / host-signed `GatewayClient`. Do not weaken assertions. Signed memory remains the Cursor/host `GatewayClient` path until a separate Devin-signed-client task exists.

## Rollback

`.agentcore/rollback/20260914-013500-nfa-devin-goal-staging/agentcore-project-enrollment.json`
