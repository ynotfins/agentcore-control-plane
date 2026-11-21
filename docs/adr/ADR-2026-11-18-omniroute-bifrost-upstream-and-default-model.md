# ADR-2026-11-18 — OmniRoute as a Bifrost upstream and the default model plane

- Status: Accepted
- Date: 2026-11-18
- Approval: `AUTH-2026-11-18-BIFROST-CONTEXT-AND-OMNIROUTE-DEFAULT`
- Supersedes: `ADR-2026-11-04-omniroute-job-b-enrollment` non-goal 1 ("not a Bifrost upstream MCP server") and decision 5 ("explicit client routing only")

## Context

ADR-2026-11-04 admitted OmniRoute as a loopback Job-B companion and deliberately kept it out of Bifrost,
with a dedicated virtual key and no interception of IDE prompts. Two facts have since changed:

1. The key it referenced (`BIFROST_MCP_VK_OMNIROUTE`) was never created, so OmniRoute's two gateway MCP
   entries returned `401 virtual key not found` for the whole interval.
2. Every agent client carried a direct OmniRoute MCP entry. The HTTP MCP surface is **110 tools**; as an
   eager client that is roughly 20–25k tokens of schema per agent — by far the largest single context cost
   on the workstation, and it duplicated `agentcore-memory`, `skills-hub` and the research servers.

The operator's requirement is the opposite of interception: one front door, all providers reachable by
every agent, and no tool schema loaded that the current task does not need.

## Decision

1. OmniRoute is admitted as a **Bifrost Code Mode MCP upstream** (`http://127.0.0.1:20128/api/mcp/stream`)
   with a named 110-tool inventory. Its eager context cost is zero; agents reach it through
   `listToolFiles → readToolFile → executeToolCode`.
2. OmniRoute is registered as a **Bifrost custom inference provider** (`base_provider_type: openai`,
   `base_url: http://127.0.0.1:20128/v1`, chat + responses only). Bifrost remains the default front door;
   direct `:20128` stays allowed for clients that cannot carry a Bifrost header.
3. Every virtual key receives provider grants for openai, openrouter and omniroute, so no agent is
   limited by which key it happens to hold.
4. `deepseek/deepseek-v4.1-flash-1017` is the machine default model, resolved through OmniRoute's combo chain
   (OpenRouter → Together → DeepInfra). The direct `ds` connection stays out of credit and must not be
   pinned.
5. OmniRoute stays loopback-only. Containers cannot reach it and that is accepted; the bind address is
   not widened to serve a Docker product.
6. OmniRoute remains neutral local infrastructure: not Trust Class A, not a canonical store, not a
   second gateway.

## Non-goals

- Not a replacement for Bifrost MCP governance, capability profiles, or virtual keys.
- No AgentCore PostgreSQL database for OmniRoute itself.
- No per-client wildcard tool grants.
- No change to Stage B, device assertion, or process attestation.

## Consequences

- One agent-visible MCP entry per client (`agentcore-gateway`); direct OmniRoute MCP entries are removed.
- A render of `config.json` is now the single source for 30 virtual keys and 20 Code Mode flags; dashboard
  edits must be back-ported to the registry or they will be reverted.
- Rollback: remove `omniroute` from the four capability profiles and the `providers` block, re-render,
  restart. Direct `:20128` inference keeps working because it never depended on Bifrost.
