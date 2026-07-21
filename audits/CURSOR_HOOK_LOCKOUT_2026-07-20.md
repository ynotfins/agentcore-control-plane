# Cursor Hook Lockout — Root Cause and Recovery (2026-07-20)

## Incident

Every Cursor tool was blocked after a partial automatic new-chat recovery implementation registered project hooks before the referenced command existed.

## Root cause

| Factor | Detail |
| --- | --- |
| Registered config | `.cursor/hooks.json` referenced `.cursor/hooks/agentcore-hook.cmd` |
| Missing artifact | `agentcore-hook.cmd` and `hook_dispatcher.py` were not yet present |
| Amplifier | `preToolUse` registered with `"failClosed": true` |
| Effect | All tool calls denied when hook command failed |

## Operator recovery (external)

Moved active hooks registration to backup:

```text
E:\AgentCore-Backups\cursor-hook-lockout-20260720-223737\hooks.json.blocked
```

Preserved blocked config records `sessionStart`, `beforeSubmitPrompt`, and `preToolUse` entries.

## Fix

1. Implemented `scripts/agentcore_cursor/hook_dispatcher.py` with controlled error responses
2. Implemented `.cursor/hooks/agentcore-hook.cmd` (deterministic Python launcher, stdin preserved)
3. Added durable local spool (`H:\AgentRuntime\clients\cursor\spool\pending\`)
4. Added offline harness `scripts/agentcore_cursor/test_hook_protocol.py` (100-iteration protocol proof)
5. Stage A registration: **only** `sessionStart` + `beforeSubmitPrompt`, **no** `failClosed`, **no** `preToolUse`

## Prevention rules

- Never register a hook whose command does not exist and pass offline tests
- Never register `preToolUse` with `failClosed` until Stage B acceptance
- Dispatcher internal errors on `preToolUse` must **fail open** (`permission: allow`)
- `beforeSubmitPrompt` allows submission after database **or** spool acceptance
- No `followup_message`; continual-learning auto-trigger remains disabled

## Evidence

| Artifact | Path |
| --- | --- |
| Blocked hooks.json | `E:\AgentCore-Backups\cursor-hook-lockout-20260720-223737\hooks.json.blocked` |
| Protocol harness log | `audits/M6/cursor-hook-protocol-harness.log` |
| Stage A hooks | `.cursor/hooks.json` (after atomic install) |
| Runbook | `docs/operations/AUTOMATIC_NEW_CHAT_RECOVERY.md` |

## Follow-up: live beforeSubmitPrompt stdin failure (2026-07-21)

Operator acceptance attempt typed `continue` in Cursor. Hook logs showed:

```text
[beforeSubmitPrompt] malformed stdin JSON
```

twice at `2026-07-21T05:45:15Z` / `05:45:17Z`. The operator prompt was **not**
durably appended for that live turn (harness fixtures still worked because they
pipe JSON correctly).

**Fix:** Stage A `hooks.json` now invokes `.cursor/hooks/agentcore-hook.ps1`
(PowerShell stdin forwarder). `.cmd` remains as a fallback. Dispatcher stdin
parsing hardened (`utf-8-sig`, brace extraction, redacted preview logging).
Bootstrap artifact now writes `ok=true` after success flags are set.

## Status

- Hook lockout: **resolved** (hooks disabled → safe Stage A reinstall)
- Live stdin capture: **patched; requires operator retest**
- Automatic new-chat recovery: **pending operator acceptance**
