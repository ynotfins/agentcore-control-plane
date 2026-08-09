# Bifrost Rollout Task Backup Classification Fix — 2026-08-09 16:41 EDT

## Summary

The approved Administrator rollout reached the scheduled-task backup phase and stopped safely:

```text
INSTALL_TASK_BACKUP_FAILED AgentCore-Bifrost-Watchdog
```

Root cause was source-side error classification, not a live watchdog corruption. On this Windows host, `Get-ScheduledTask -TaskName AgentCore-Bifrost-Watchdog -ErrorAction Stop` returns:

- `FullyQualifiedErrorId`: `CmdletizationQuery_NotFound,Get-ScheduledTask`
- `CategoryInfo.Category`: `ObjectNotFound`
- `CategoryInfo.Reason`: `CimJobException`

The installer did not treat that CIM not-found shape as an absent task, so it incorrectly classified the missing watchdog as an existing task with a failed backup.

## Source correction

Source file: `@D:\github\agentcore-control-plane\ops\bifrost\Install-AgentCoreBifrostGateway.ps1`

`ops\bifrost\Install-AgentCoreBifrostGateway.ps1` now classifies scheduled-task not-found errors using message text, `FullyQualifiedErrorId`, `CategoryInfo.Category`, and `CategoryInfo.Reason`.

This preserves the fail-closed behavior for real export failures while allowing first-time watchdog creation when the task does not exist.

## Validation

Focused regression:

```text
python -m pytest scripts\bifrost\test_lifecycle_watchdog.py -q
20 passed
```

Broader Bifrost suite:

```text
python -m pytest scripts\bifrost -q
85 passed
```

Contract validators:

```text
python scripts\bifrost\validate_contracts.py
OK

python scripts\bifrost\validate_output_schemas.py
OK

python scripts\validate_authority_lock.py
OK
```

## Current next action

After this source fix is committed and pushed, rerun the already-approved rollout from the existing Administrator PowerShell:

```powershell
Set-Location -LiteralPath ('D:' + '\github\agentcore-control-plane')
.\ops\bifrost\Invoke-AgentCoreMorningRollout.ps1 -ApproveBifrostRollout
```

Expected pass condition remains unchanged:

1. Bifrost config drift clears.
2. `AgentCore-Bifrost-Watchdog` is installed.
3. `Get-BifrostStatus.ps1` returns `BIFROST_STATUS_OK`.
4. `Test-AgentCoreBifrostGateway.ps1` passes.
5. `Test-AgentCoreMorningReadiness.ps1` has no AgentCore-side Bifrost/Cursor failures.
