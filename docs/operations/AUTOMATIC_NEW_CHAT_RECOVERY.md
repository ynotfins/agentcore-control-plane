# Automatic Cursor New-Chat Recovery

**Status:** Stage B accepted — seven lifecycle hooks registered; `Continue.` gate and 26/26 integrity suite passed on 2026-07-24
**Authority:** `PROJECT_ANCHOR.md` · `BLUEPRINT.md` · `docs/operations/AGENTCORE_CONTINUAL_LEARNING.md`

## Goal

A fresh Cursor Agent chat in the same project and same open task must automatically recover canonical AgentCore context without pasted history or attachments.

## Architecture

```text
Cursor hook (project .cursor/hooks.json)
  -> powershell ... agentcore-hook.ps1 -Event <event>
       (agentcore-hook.cmd retained as fallback / offline helper)
  -> scripts/agentcore_cursor/hook_dispatcher.py
  -> scripts/agentcore_cursor/hooks.py
  -> agentcore-gateway -> agentcore-memory
  -> generated projections (.agentcore/STATE.md, DECISIONS.md, CONTEXT_INDEX.md)
  -> ephemeral bootstrap artifacts (.agentcore/runtime/, .cursor/rules/agentcore-active-bootstrap.mdc)
```

**Windows note (2026-07-21):** Cursor's hook host can deliver non-JSON/empty stdin through
`.cmd` wrappers. Stage A registers the PowerShell wrapper so stdin is read via
`[Console]::In.ReadToEnd()` and forwarded to Python.

## Hook events (Stage B)

| Event | Purpose | Fail mode |
| --- | --- | --- |
| `sessionStart` | Activate project, resume session_key, inject bounded `additional_context` | Fail open (env flags only) |
| `beforeSubmitPrompt` | Redact secrets, append operator prompt with idempotency key | Allow after DB or local spool acceptance |
| `preToolUse` | Enforce deterministic pre-tool boundaries | Fail open on internal hook error; explicit policy denials remain authoritative |
| `beforeShellExecution` | Block known destructive or secret-printing shell patterns | Deterministic deny for matched policy; otherwise allow |
| `afterFileEdit` | Record bounded file-change evidence | Fail open on hook error |
| `postToolUse` | Record bounded tool outcome evidence | Fail open on hook error |
| `stop` | Persist the final-review envelope without resubmitting a prompt | Returns `{}`; never emits `followup_message` |

## Identities

| Field | Value |
| --- | --- |
| client_key | `cursor` |
| agent_key | `cursor-composer` |
| context_profile | `standard-context` |
| gateway | `http://127.0.0.1:8080/mcp` |

## Operator CLI

```powershell
cd D:\github\agentcore-control-plane
python -m agentcore cursor recover
python -m agentcore cursor status
python -m agentcore cursor resume --session-key <key>
python -m agentcore cursor new-task --slug <slug>
```

## Degraded mode

When `agentcore-gateway` is temporarily unavailable:

- Prompt capture spools to `F:\AgentCore\runtime\clients\cursor\spool\pending\`
- Hook diagnostics log to `F:\AgentCore\runtime\clients\cursor\logs\hooks\`
- Hooks never fabricate user-role messages or call continual-learning

## Safe registration or repair process

1. Write `.cursor/hooks.json.new`
2. Schema-check JSON
3. Confirm `.cursor/hooks/agentcore-hook.cmd` and dispatcher exist
4. Run `python scripts/agentcore_cursor/test_hook_protocol.py --iterations 100`
5. Backup prior hooks.json to `E:\AgentCore-Backups\`
6. Atomically rename `hooks.json.new` → `hooks.json`
7. Restart Cursor and rerun the `Continue.` recovery proof only when hook registration or lifecycle behavior changed

## Rollback

```powershell
Remove-Item D:\github\agentcore-control-plane\.cursor\hooks.json -Force
Copy-Item E:\AgentCore-Backups\cursor-hook-lockout-20260720-223737\hooks.json.blocked `
  E:\AgentCore-Backups\cursor-hook-lockout-20260720-223737\hooks.json.rollback-reference -Force
# Or restore from E:\AgentCore-Backups\cursor-hook-lockout-20260720-223737\hooks.json.blocked after renaming to disable preToolUse
```

To disable hooks entirely: move `.cursor/hooks.json` to `E:\AgentCore-Backups\cursor-hook-lockout-<timestamp>\hooks.json.disabled`.

## Acceptance — completed `Continue.` hard gate

The Stage B gate completed on 2026-07-24. All 26 integrity tests passed and the seven-hook registration in `.cursor/hooks.json` is the live project baseline.

Operator opens a **new** Cursor Agent chat in this repo and types **only**:

```text
Continue.
```

Pass criteria for any future rerun: the agent reports project/worktree, resumed `session_key`, current task, blocker, and next action with AgentCore source IDs — without a pasted recap prompt.

## Related audits

- `audits/CURSOR_HOOK_LOCKOUT_2026-07-20.md`
- `audits/CURSOR_NEW_CHAT_RECOVERY_2026-07-20.md`
- `audits/CURSOR_HOOK_SKILL_RULE_INVENTORY_2026-07-20.md`
- `audits/cursor-context/CURSOR_STAGE_B_INTEGRITY_HARNESS_ACCEPTANCE_2026-07-24.md`
