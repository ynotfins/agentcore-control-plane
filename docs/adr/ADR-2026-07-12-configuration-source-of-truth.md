# ADR-2026-07-12 — Configuration Source of Truth

**Status:** Accepted (operator-final)
**Date:** 2026-07-12

## Context

Historically, each IDE held a full direct MCP server block. That drifted across clients and mixed secrets, Swarm entries, and whole-drive filesystem roots into live configs.

## Decision

Configuration flows one way:

```text
AgentCore contracts (Git)
  contracts/bifrost-upstream-mcp-registry.json
  contracts/agentcore-gateway-client.json
        |
        v
Renderers / scripts
  scripts/bifrost/render_bifrost_config.py
  renderers/bifrost/*.json          (sanitized, source-controlled)
  renderers/gateway-clients/*.json  (sanitized, source-controlled)
        |
        v
Live Bifrost runtime (H:)
  H:\AgentRuntime\bifrost\config.json
  sqlite stores under H:\AgentRuntime\bifrost\data and \logs
        |
        v
IDEs (C: app configs)
  ONLY the single agentcore-gateway client entry
  (from contracts/agentcore-gateway-client.json / gateway-clients renderers)
```

Rules:

1. **Git contracts are design authority.** Do not hand-edit H: live config as the long-term source of truth.
2. **IDEs receive only the gateway client entry** — not the upstream registry.
3. Secrets use Windows User env names (`env.NAME` in Bifrost; `${env:NAME}` in IDE clients). Never commit resolved values.
4. Live IDE cutover may materialize `BIFROST_MCP_VIRTUAL_KEY` into a live config **only** when the client cannot expand env headers — still never commit that live file.
5. Validators (`scripts/bifrost/validate_contracts.py`) must fail on contract/schema drift.

## Consequences

- Changing an upstream MCP server means editing the registry + re-render + restart Bifrost — not editing eight IDE files.
- Rollback restores backed-up IDE gateway configs and/or Bifrost runtime config from approved backup roots.
- Old direct per-IDE full-server blocks are historical/rollback-only (see `MASTER_CONFIG_AND_PROMPT.md` appendix).

## References

- `PROJECT_ANCHOR.md` §0–§8
- `docs/bifrost/MIGRATION_RUNBOOK.md`
- `docs/bifrost/ROLLBACK_RUNBOOK.md`
