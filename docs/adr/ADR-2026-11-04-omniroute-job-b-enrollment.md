# ADR-2026-11-04 — OmniRoute Job-B enrollment

- Status: Accepted
- Date: 2026-11-04
- Approval: `AUTH-2026-11-04-LOCKED-DOC-HARDENING-OMNIROUTE`

## Context

OmniRoute `3.8.49` was previously documented as a disabled, benchmark-gated inference-compression candidate. Live workstation needs a loopback Job-B companion that can call AgentCore MCP tools through Bifrost without becoming a second IDE MCP front door.

## Decision

1. Install/runtime data lives under `I:\LocalApps\OmniRoute` (DATA_DIR `I:\LocalApps\OmniRoute\data\.omniroute`).
2. Bind `OMNIROUTE_SERVER_HOST=127.0.0.1` on port `20128` (health/API). Run the process at Windows priority BelowNormal.
3. OmniRoute MCP clients `agentcore-gateway` and `agentcore-memory` target `http://127.0.0.1:8080/mcp` with `Authorization: Bearer ${env:BIFROST_MCP_VK_OMNIROUTE}` (dedicated Bifrost virtual key; never the operator/builder key).
4. IDEs keep a single AgentCore MCP entry (`agentcore-gateway`). OmniRoute does not replace Bifrost and does not auto-intercept IDE model prompts.
5. Optional inference compression/routing remains behind Bifrost governance and requires explicit client routing plus fidelity tests before any claim of prompt savings.

## Non-goals

- Not a Bifrost upstream MCP server.
- Not Trust Class A.
- No AgentCore PG18 database for OmniRoute itself.
- No merge of OmniRoute into nfa-platform ports/services.

## Consequences

- Launcher/scheduled task `AgentCore-OmniRoute` owns process lifecycle.
- Progress/recovery notes: `I:\LocalApps\OmniRoute\PROGRESS.md`.
- Rollback: stop OmniRoute task/process; leave Bifrost and NFA untouched; revert this ADR + CONTEXT_BLOCK rows on the control-plane branch.
