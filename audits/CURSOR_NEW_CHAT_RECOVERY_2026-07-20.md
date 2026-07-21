# Cursor New-Chat Recovery — Implementation Evidence (2026-07-20)

## Scope

Safe Stage A automatic continuity for Cursor in `D:\github\agentcore-control-plane`.

## Implementation inventory

| Component | Status | Notes |
| --- | --- | --- |
| `scripts/agentcore_cursor/bootstrap.py` | Complete | Session resume, startup_context, projections, pointer |
| `scripts/agentcore_cursor/gateway.py` | Complete | Bifrost MCP client |
| `scripts/agentcore_cursor/hooks.py` | Complete | Event handlers; no followup_message |
| `scripts/agentcore_cursor/hook_dispatcher.py` | Complete | Deterministic stdin/stdout, bounded logs |
| `scripts/agentcore_cursor/spool.py` | Complete | `H:\AgentRuntime\clients\cursor\spool\pending\` |
| `.cursor/hooks/agentcore-hook.cmd` | Complete | Windows wrapper |
| `scripts/agentcore/cursor_cli.py` | Complete | `python -m agentcore cursor` |
| `scripts/agentcore_cursor/test_hook_protocol.py` | Complete | Offline harness |
| `.cursor/hooks.json` Stage A | Installed | sessionStart + beforeSubmitPrompt only |

## Database verification (read-only)

| Check | Result |
| --- | --- |
| m8.001 applied | Yes |
| m8.002 applied | Yes (once) |
| `agentcore.v_client_memory_continuity` | Present |
| Rollback source | `migrations/m8/002_down_client_memory_continuity_view.sql` |

## Git state at implementation

| Field | Value |
| --- | --- |
| Branch | `main` |
| Preserved commits | `d0be627` (Cherry repair), `5331f99` (continual learning alignment) |
| HEAD before hook commits | `5331f99` |

## Protocol harness

Command:

```powershell
python scripts/agentcore_cursor/test_hook_protocol.py --iterations 100
```

Validates: single JSON stdout, no secrets, malformed input, degraded gateway, idempotency, no orphan processes.

Log: `audits/M6/cursor-hook-protocol-harness.log`

## Operator acceptance (pending)

1. Restart Cursor after Stage A `hooks.json` install
2. Open a **new** Agent chat in this repository
3. Type only: `Continue.`
4. Agent must recover task context with AgentCore source IDs

**Gate:** Do not mark `AUTOMATIC ROLLING CONTEXT LIVE FOR CURSOR` until acceptance passes.

## Current task continuity target

When acceptance passes, the recovered session should include:

- project/worktree: `agentcore-control-plane` / `D:\github\agentcore-control-plane`
- task: Cursor hook lockout recovery + safe automatic new-chat continuity (Stage A)
- blocker: operator new-chat acceptance not yet run
- next action: operator types `Continue.` in fresh chat; then LangGraph/Studio live reconfirmation
