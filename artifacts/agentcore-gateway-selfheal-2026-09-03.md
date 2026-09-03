# AgentCore Gateway Self-Heal Repair - 2026-09-03

## Scope

Restored the AgentCore Bifrost MCP gateway on CHAOSCENTRAL and repaired the startup failure mode that prevented self-healing when Redis was not available before Bifrost launch.

## Evidence

- Initial health check failed: `http://127.0.0.1:8080/health` refused the connection.
- `F:\AgentCore\runtime\bifrost\logs\bifrost-gateway.stderr.log` showed Bifrost exited fatally on 2026-09-02 because Redis at `localhost:6379` was unavailable.
- The gateway scheduled task `\AgentCore\AgentCore-Bifrost-Gateway` was enabled but configured with only one restart attempt.
- The previous one-minute watchdog task remained disabled because it was already documented as an intrusive interactive desktop-session task.

## Changes

- `ops\bifrost\Launch-AgentCoreBifrostGateway.ps1` now waits up to 180 seconds for the configured Redis vector-store endpoint before launching Bifrost.
- `ops\bifrost\Install-AgentCoreBifrostGateway.ps1` now emits a gateway task with `restart_count = 999`.
- The live `\AgentCore\AgentCore-Bifrost-Gateway` scheduled task was updated to `RestartCount=999` and `RestartInterval=PT1M`.
- `ops\bifrost\Test-AgentCoreBifrostGateway.ps1` now prefers the repo-owned Python runtime before falling back to system Python.
- `D:\launchers\AUTOMATION_REGISTRY.json` and `D:\launchers\AUTOMATION_MAP.md` were updated outside this repository to record the active gateway automation and rollback XML.

## Rollback

Task XML backups:

- `D:\launchers\.backups\agentcore-gateway-selfheal-20260903-141815\AgentCore-Bifrost-Gateway.before.xml`
- `D:\launchers\.backups\agentcore-gateway-selfheal-20260903-141815\AgentCore-Bifrost-Watchdog.before.xml`

## Validation

- PowerShell parse: `Launch-AgentCoreBifrostGateway.ps1`, `Install-AgentCoreBifrostGateway.ps1`, and `Test-AgentCoreBifrostGateway.ps1` passed.
- `D:\launchers\AUTOMATION_REGISTRY.json` parsed as JSON.
- `scripts\bifrost\validate_contracts.py` passed with the repo venv.
- `ops\bifrost\Test-AgentCoreBifrostGateway.ps1` passed, including `/health`, authenticated MCP `initialize`, authenticated `tools/list`, and Cursor gateway config checks.
- `scripts\bifrost\test_lifecycle_watchdog.py`: 20 passed.

## Current State

- `http://127.0.0.1:8080/health` returned HTTP 200 with `status: ok`.
- Authenticated MCP `tools/list` returned 46 tools.
- `\AgentCore\AgentCore-Bifrost-Gateway` is running and enabled.
- The intrusive watchdog remains disabled pending a non-intrusive replacement.
