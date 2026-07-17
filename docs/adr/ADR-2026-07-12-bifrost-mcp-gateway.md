# ADR-2026-07-12 — Bifrost MCP Gateway Deployment

**Status:** Accepted (operator-final)
**Date:** 2026-07-12
**Authority:** `PROJECT_ANCHOR.md` §0 Bifrost Gateway Override

## Context

AgentCore needs a single workstation MCP aggregation plane for non-Swarm IDEs so each client does not maintain a divergent full-server MCP baseline. A prior Go SDK smoke (`experiments/bifrost-go-sdk-smoke/`) validated in-process model routing only — it does **not** expose `/mcp` aggregation.

## Decision

1. Use **Bifrost native Gateway** on Windows — `bifrost-http.exe` — as the workstation MCP gateway (**not** the Go SDK).
2. Pin installed build: **v2.0.0-prerelease1** native Windows binary.
3. Runtime root: **`H:\AgentRuntime\bifrost`** (bin, config.json, sqlite config/logs stores, state, backups).
4. Config authority remains **`D:\github\agentcore-control-plane`** (contracts + renderers). Live config is rendered to H:.
5. MCP client auth mode: **headers** virtual-key auth (`mcp_server_auth_mode: headers`). IDEs send `Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}` to `http://127.0.0.1:8080/mcp`.
6. Persistence: **config.json + sqlite** (`config_store` / `logs_store`), not Docker.
7. **No Docker** for the Bifrost Gateway runtime itself.
8. Bind to localhost only (`127.0.0.1:8080`).

## Consequences

- Non-Swarm IDEs carry a single `agentcore-gateway` entry.
- Upstream servers are governed in `contracts/bifrost-upstream-mcp-registry.json`.
- SwarmRecall/SwarmVault/SwarmClaw remain a separate ecosystem and are excluded from the non-Swarm baseline.
- Go SDK smoke stays quarantined under `experiments/bifrost-go-sdk-smoke/`.
- Rollback is file/config restore from `E:\AgentCore-Backups\...` and `ops/bifrost/Restore-AgentCoreBifrostConfig.ps1` — not a container rollback.

## Non-goals

- Replacing Swarm product internals.
- Using Bifrost Go SDK as the MCP gateway.
- Putting Postgres credentials or whole-drive filesystem roots in IDE configs.

## References

- `docs/adr/ADR-2026-07-12-configuration-source-of-truth.md`
- `contracts/agentcore-gateway-client.json`
- `ops/bifrost/Install-AgentCoreBifrostGateway.ps1`
- https://docs.getbifrost.ai (index via arabold-docs library `bifrost` / `2.0.0-prerelease1`)
