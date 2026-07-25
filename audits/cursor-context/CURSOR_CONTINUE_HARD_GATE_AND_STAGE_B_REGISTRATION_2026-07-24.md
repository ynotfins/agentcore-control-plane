# Cursor Continue. Hard Gate and Stage B Registration — Phase 3

**Date:** 2026-07-24 / 2026-07-25  
**Canonical repo:** `D:\github\agentcore-control-plane`  
**Status:** PASS / STAGE_B_LIVE

---

## Executive summary

Phase 3 confirmed that Cursor Stage B was **already registered** in
`.cursor/hooks.json` (not merely coded). The pending Continue. operator hard
gate is satisfied by durable DB evidence of exact `"Continue."` prompt capture
via `cursor.beforeSubmitPrompt`. The 26-test Stage B suite and isolated
rollback fixture both PASS on this date.

---

## Registered hooks (live)

From `D:\github\agentcore-control-plane\.cursor\hooks.json`:

1. `sessionStart`
2. `beforeSubmitPrompt`
3. `preToolUse`
4. `beforeShellExecution`
5. `afterFileEdit`
6. `postToolUse`
7. `stop`

All invoke `.cursor/hooks/agentcore-hook.ps1 -Event <name>` with timeout 90s.

---

## Continue. proof

`python scripts/agentcore_cursor/formal_continue_proof.py` (exit 0):

- Multiple `prompt` events with `payload.text == "Continue."` (length 9)
- Capture path: `cursor.beforeSubmitPrompt`
- Distinguished from non-prompt `accepted_evidence` rows that only mention Continue. in summary text
- Projection revision observed: 22
- Surviving `hook-test-session` rows: 0

---

## Validation matrix (re-run 2026-07-25)

`python scripts/agentcore_cursor/test_stage_b_suite.py` → **26/26 PASS**

Including: hook protocol ×100, Step 0 gating, dangerous shell deny, fail-open,
exact-once prompt, projection stale block, lean surface (1 rule / 1 skill /
1 MCP), Swarm untouched, LangGraph fixture green.

`python scripts/agentcore_cursor/test_rollback_fixture.py` → **PASS**  
(restores Stage A hooks only in disposable fixture)

---

## CONTEXT_BLOCK update

`CONTEXT_BLOCK.md` §0a IDE clients row updated:

- Stage A “hard gate pending” → Stage B **live** with evidence paths
- Cherry DRIFT-01 called out (config-present / native untrusted until Phase 4C)

---

## Rollback

```powershell
python D:\github\agentcore-control-plane\scripts\agentcore_cursor\rollback_stage_b.py
```

Live Stage B backup reference:
`E:\AgentCore-Backups\agentcore-control-plane\cursor-stage-b-20260724-233811`

---

**Status signal:** `CURSOR_STAGE_B_LIVE_CONFIRMED`
