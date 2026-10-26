# Raven control-plane enrollment

Date: 2026-10-26
Approval: AUTH-2026-10-26-RAVEN-CONTROL-PLANE-ENROLLMENT
Project key: raven
Source root: D:\raven

This file is evidence for a control-plane-only admission. Raven and Dify were not installed in this task.

## Decision

Raven is an AgentCore-managed project at the exact path `D:\raven` and a governed `agentcore-gateway` client with a dedicated `raven` capability profile. It is not Trust Class A. It uses local EverOS memory and is not attached to AgentCore PG18, SwarmRecall, SwarmVault, or SwarmClaw.

## Storage

- Raven data: `I:\LocalApps\Raven` via `RAVEN_HOME`
- Dify data: `I:\LocalApps\Dify` plus Docker named volumes
- Backups: `E:\LocalApps\Backups\Raven` and `E:\LocalApps\Backups\Dify`
- Do not enroll `C:\Users\ynotf\.raven` or `C:\Users\ynotf\.dsh`

## Gateway

Preferred live route: `http://127.0.0.1:8080/mcp` with User-scope `BIFROST_MCP_VK_RAVEN`. Never write the resolved key into Git or Raven config. If Raven cannot expand env headers, do not paste a key; the process-attested `:18082` path would be required after `Raven.exe` identity is known.

## Operator-approved live apply still required

Do not treat repo render as live. After source commit, the operator must approve:

1. `D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe scripts\bifrost\render_bifrost_config.py`
2. `D:\github\agentcore-control-plane\ops\bifrost\Stop-AgentCoreBifrostGateway.ps1`
3. `D:\github\agentcore-control-plane\ops\bifrost\Start-AgentCoreBifrostGateway.ps1`

## Validation

- `scripts/bifrost/validate_contracts.py`: OK
- `scripts/bifrost/test_raven_bifrost_profile.py`: PASS
- Tracked-source secret scan: PASS
- `BIFROST_MCP_VK_RAVEN` User-scope existence: true (value not recorded)
- Rollback copies: `.agentcore/rollback/20261026-162721-raven-control-plane-enrollment/`

## Gateway health at enrollment

- Bifrost scheduled task running
- `http://127.0.0.1:8080/health` status=ok
- Builder `agentcore-memory` tools=10
- Builder Skills Hub tools were 0; not repaired in this task
- Live Bifrost config was not applied; repo renderers only

## Ready for Raven install

Source enrollment is complete. Raven install may proceed after the operator-approved live apply/restart above. Do not write the virtual key into Raven config.
