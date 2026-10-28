# Open Design — next-agent handoff (2026-10-28)

Canonical copy for AgentCore git. Operator-facing twin: `D:\open-design\docs\HANDOFF_NEXT_AGENT.md`.

## Objective

Open Design 0.26.1 desktop is the product. `D:\open-design` is the enrolled RGDS/npm folder only. Cursor uses one Bifrost gateway plus one official Open Design MCP companion. KIE is billed default where protocol works; backups are selectable.

## After PC restart

1. Start Open Design desktop (ports change each launch).
2. Confirm `AgentCore-Bifrost-Gateway` running and `GET http://127.0.0.1:8080/health` → ready / 2.0.0-prerelease.
3. Confirm User env `BIFROST_MCP_VIRTUAL_KEY` exists (do not print).
4. Refresh Cursor MCP.
5. Confirm enrollment row `open-design` → `D:\open-design` in live `contracts/agentcore-project-enrollment.json`.

Full checklist: `D:\open-design\docs\PC_SETUP.md`.

## Git

- Branch pushed: `feat/open-design-enrollment` @ `a13a9c0` (`origin/feat/open-design-enrollment`).
- Open PR URL (not created): https://github.com/ynotfins/agentcore-control-plane/pull/new/feat/open-design-enrollment
- Do not commit `.agentcore/rollback/**/cursor-mcp.json.pre-attach`.
- Dirty `D:\github\agentcore-control-plane` main may still hold Raven work — leave it.

## Docs-version-guardian (2026-10-28)

- bifrost 2.0.0: PASS (arabold exact).
- @r3lentless/rgds-web 1.1.0: FAIL (not in arabold; local DESIGN.md).
- react 19.3.1: FAIL (not in arabold).

## AUTH still in force

`AUTH-2026-10-26-OPEN-DESIGN-ENROLLMENT`. No Claude/Codex/MiniMax OD MCP. No AppData. No PG18. No OD Bifrost upstream.

## Memory

`session_open` requires `device_assertion`. Use this file.
