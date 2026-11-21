# Proposal: Bifrost watchdog failsafe repair (gateway outage 2026-11-19)

**Date:** 2026-11-19
**Status:** Implemented and live-verified. Needs an elevated installer run to refresh the stored task definition.
**Owner for apply:** Devin. Codex reviews.
**Rollback:** revert the four files in this commit. No data, schema, secret, or contract change.

## Why

`agentcore-gateway` was reported down. It was actually serving by the time of diagnosis, but the incident exposed that the managed failsafe had never worked: the watchdog logged **1,996 failed recovery attempts against 1 successful recovery (2026-09-05)**.

## What happened

Timeline (local time, 2026-11-19):

| Time | Event |
| --- | --- |
| 19:20:27 | User session ended. The interactive gateway task instance terminated (`0x80070004`). |
| 19:20–19:22 | Gateway down. Task Scheduler did not run the SYSTEM watchdog during the session transition. |
| 19:22:15 | Logon trigger restarted the gateway task. |
| 19:22:47 | Launcher reached the builder-compat preflight. |
| 19:22:50–19:26:05 | Watchdog detected the outage and attempted recovery every minute. Every attempt failed. |
| 19:25:14 | Docker backend (and the Redis vector store on `127.0.0.1:6381`) came back. |
| 19:25:38 | Launcher started `bifrost-http` after waiting the full 180 s dependency timeout. |
| 19:27:00 | Gateway healthy. |

Total outage: about 5 minutes. Recovery came from the logon trigger and the launcher's own retry, not from the failsafe.

## Root cause

1. **Broken task identity (critical).** The watchdog scheduled task passes `-TaskPath "\AgentCore\"`. Windows command-line parsing treats a backslash before a closing quote as an escaped quote, so the watchdog actually received:

   - `TaskPath` = `\AgentCore" -TaskName AgentCore-Bifrost-Gateway -FailureThreshold 2 ...`
   - the remaining arguments were swallowed into that value.

   That produced exactly the logged failures: `No matching MSFT_ScheduledTask objects found`, `The system cannot find the file specified`, and `Value for '/TN' option cannot be more than 237 character(s)`. The watchdog could not find or start the gateway task, so every recycle attempt failed. The defect was introduced with the `-TaskPath` argument and survived the `b4a72c9` "always-on supervisor + watchdog coverage" change.

2. **Startup gated on an optional dependency for 180 s.** The launcher waited up to 180 s for the Redis vector store before starting Bifrost. Docker restarts with the user session, so the cache was down for the same window and every restart became a multi-minute outage.

3. **Silent failure.** Watchdog failures were written only to `bifrost-watchdog.log`. Nothing raised an alarm, so a 1,996-failure streak went unnoticed.

4. **Merged with failing tests.** `b4a72c9` changed the installer to 180 s / 30 s and added boot triggers, but left `scripts/bifrost/test_lifecycle_watchdog.py` expecting 60 s / 60 s and two triggers. The suite was red at HEAD before this change.

## Changes

- `ops/bifrost/Invoke-AgentCoreBifrostWatchdog.ps1`
  - Normalizes `TaskPath`/`TaskName` at startup and repairs the legacy mangled form, logging `WATCHDOG_CONFIG_REPAIRED`. The live task now recovers even with its stale stored definition.
  - Raises `state/bifrost-alarm.json` and a Windows Application event (source `AgentCore-Bifrost-Watchdog`, event 5100) when recovery fails; clears both on health.
  - Logs `WATCHDOG_TASK_MISSING` when the task is genuinely absent.
- `ops/bifrost/Launch-AgentCoreBifrostGateway.ps1`
  - `MaxDependencyWaitSeconds` default 180 → 30. The vector store remains optional; `-RequireRedisVectorStore` still enforces it when requested.
- `ops/bifrost/Install-AgentCoreBifrostGateway.ps1`
  - Emits `-TaskPath "\AgentCore"` (no trailing backslash inside quotes).
  - Watchdog `ExecutionTimeLimit` 180 s → 60 s, matching the validator contract.
  - Fixes the boot-trigger test scope so gateway and watchdog triggers are no longer conflated.
- `scripts/bifrost/test_lifecycle_watchdog.py`
  - Aligns the installer expectations with the current spec.
  - Adds regressions: installer arguments survive real Windows command-line parsing; the legacy trailing-backslash form is repaired; recovery alarms raise and clear.

## Verification (this session)

- Targeted suite: **13 passed** (watchdog lifecycle, installer specs, verifier profile, new regressions).
- Live failsafe test: stopped the gateway task, killed the orphaned `bifrost-http` at 23:37:57.
  - 23:38:04 failure 1; 23:39:04 failure 2; 23:39:05 `WATCHDOG_RECYCLE_STARTED count=2`; 23:39:34 new `bifrost-http`; 23:40:08 healthy.
  - Recovery in 2 m 11 s, entirely by the watchdog. This is the first successful recycle since 2026-09-05.
- `GET /health` → 200 `{"status":"ok"}`; gateway MCP `tools/list` succeeds; alarm file absent.

## Residual risk and follow-ups

1. **Stored task definition is still stale.** Re-running the installer elevated will write `-TaskPath "\AgentCore"` and the 60 s limit. The script repair makes this non-blocking.
2. **Interactive-token principal.** The gateway task runs in the operator's session and cannot start while logged off (Task Scheduler event 332). Moving it to SYSTEM would require machine-scope secrets for `BIFROST_MCP_VIRTUAL_KEY`; that is a governed secrets change and is **not** part of this proposal.
3. **Watchdog dead-man switch.** If the watchdog task itself is disabled or deleted, nothing recovers the gateway. `Test-AgentCoreBifrostGateway.ps1 -RequireWatchdogEnabled` catches it on demand; a periodic external check is a separate follow-up.
4. **No documentation edits.** This file is the bounded proposal; governed docs remain untouched pending maintainer action.
