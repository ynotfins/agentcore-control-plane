# Handoff — OpenRouter MCP OAuth Bind (2026-07-20)

## Claim

`OPENROUTER MCP AVAILABLE THROUGH AGENTCORE-GATEWAY`

## What changed

- Scheduled-task restart rebound authorized OAuth config `aa25b02d-…` to live client `56631c8f-…`.
- Client connected; encrypted token retained; no new consent; no `complete-oauth` call needed.
- Authenticated live inventory captured (20 tools).
- Discovery lease activate / revoke / expiry proofs passed on operator VK.
- Docs/registry/MASTER/AGENTS updated to the new completion string.

## Operator remaining

1. OpenRouter Keys dashboard: revoke only orphan keys from failed pending flows.
2. Do not revoke the working authorized MCP OAuth grant.

## Evidence

- `audits/OPENROUTER_MCP_OAUTH_BIND_2026-07-20.md`
- `docs/operations/OPENROUTER_MCP.md`
- `contracts/bifrost-upstream-mcp-registry.json` — registry `status: "dormant"` (zero default exposure); lifecycle posture `authenticated_dormant` after OAuth bind (see `docs/operations/OPENROUTER_MCP.md` vocabulary)
