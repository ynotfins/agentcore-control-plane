# Automatic Cursor New-Chat Recovery

**Status:** Stage B accepted; prompt submission is fail open and mutation authorization is fail closed
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
| `beforeSubmitPrompt` | Revoke prior-turn authorization, redact secrets, and append the operator prompt with an idempotency key | Always `continue: true`; workspace, gateway, memory, continuity, malformed-input, and dispatcher failures return a visible warning |
| `preToolUse` | Enforce deterministic pre-tool boundaries | Read-only calls may continue; write-capable or unclassified mutation paths fail closed until current-turn durable capture is proven |
| `beforeShellExecution` | Block destructive/secret-printing patterns and gate filesystem mutations | Read-only commands may continue; mutating or ambiguous commands fail closed until current-turn durable capture is proven |
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

## Prompt submission and mutation interlock

`beforeSubmitPrompt` is an observability and continuity hook. It must never stop
the operator from sending a prompt. It returns `continue: true` and a warning if
the workspace cannot be verified, the gateway or memory facade is unavailable,
continuity is stale or ambiguous, input is malformed, or the dispatcher fails.

After workspace resolution, and before bootstrap, network I/O, or
bootstrap-artifact parsing, the hook revokes authorization from the preceding
turn. Malformed or unscoped dispatcher failure sets a global unresolved deny
latch. A new authorization is released only after the prompt has a durable event
and the local and global interlocks match the current:

- workspace root;
- session id;
- conversation id;
- `generation_id`.

Until all four identities match, `preToolUse` denies write-capable tools and
`beforeShellExecution` denies mutating or ambiguously classified shell commands.
Deterministically read-only tools and commands remain usable for diagnosis and
recovery. A warning under the submitted prompt therefore means the prompt ran,
while state-changing tools remain protected until continuity recovers.

## Operator CLI

```powershell
$AgentCorePython = 'D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $AgentCorePython)) {
  & 'D:\github\agentcore-control-plane\scripts\bootstrap-runtime.ps1'
}
Set-Location 'D:\github\agentcore-control-plane\scripts'
& $AgentCorePython -m agentcore cursor recover
& $AgentCorePython -m agentcore cursor status
& $AgentCorePython -m agentcore cursor resume --session-key <key>
& $AgentCorePython -m agentcore cursor new-task --slug <slug>
```

## Degraded mode

When `agentcore-gateway` is temporarily unavailable:

- Failed prompt capture is not currently spooled; the hook reports
  `canonical_write_unavailable` or the specific continuity failure.
- Hook diagnostics log to `F:\AgentCore\runtime\clients\cursor\logs\hooks\`
- Hooks never fabricate user-role messages or call continual-learning
- `beforeSubmitPrompt` still allows the prompt and reports the degradation.
- Write-capable tools and mutating or ambiguous shell commands remain denied
  until durable capture for the current turn is confirmed.

## Safe registration or repair process

1. Write `.cursor/hooks.json.new`
2. Schema-check JSON
3. Confirm `.cursor/hooks/agentcore-hook.cmd` and dispatcher exist
4. Run `D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe D:\github\agentcore-control-plane\scripts\agentcore_cursor\test_hook_protocol.py --iterations 100`
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
