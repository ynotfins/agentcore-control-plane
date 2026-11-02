# Audit — ZCode Laptop Gateway Tailnet Route (2026-11-01)

## Authorization

Operator instruction, verbatim (ZCode session on chaoscentral, 2026-11-01):

> "all the mcp servers are working except the most important one agentcore-gateway. We
> need to hardcode this mcp server if possible or whatever you think is best to make
> sure it always works."

This constitutes operator authorization for a cross-host client route to the canonical
AgentCore gateway — the decision both control planes previously left UNDEFINED for a
second machine. Design chosen: extend the existing sanctioned bearer route
(`contracts/agentcore-gateway-client.json` auth block, the route already used by
Cursor/Codex/OpenClaw/Raven) over the operator's existing Tailscale tailnet. No new
trust class, no master-key exposure, no second AgentCore stack (a second stack would
fork the canonical memory database).

## Change

1. **chaoscentral (source PC) — `tailscale serve`**: added mount
   `https://chaoscentral.tailb71e7e.ts.net/mcp` → `http://127.0.0.1:8080/mcp`
   (`tailscale serve --bg --set-path /mcp http://127.0.0.1:8080/mcp`).
   Tailnet-only (never funnel/public). Pre-existing mounts untouched:
   `/` → 127.0.0.1:18789, `/v1/ingest` → 127.0.0.1:8787/v1/ingest.
   The gateway binary itself was NOT modified; it remains loopback-bound.
2. **Laptop ZCode client** (`~/.zcode/cli/config.json`): `agentcore-gateway` entry is a
   stdio launcher (`agentcore-gateway-mcp-launch.cmd` in the laptop's ZCode MCP dir)
   that runs `npx -y mcp-remote https://chaoscentral.tailb71e7e.ts.net/mcp
   --transport http-only --header "Authorization: Bearer ${BIFROST_MCP_VK_OPERATOR}"`.
   The VK is read from the Windows User environment at launch (same pattern as the
   github/claude-context companions); no credential is stored in any file or IDE JSON.
   Delivered via `C:\Users\ynotf\zcode-laptop-migration\Install-Laptop.ps1`
   (gateway enabled by default; `-DisableGateway` switch).
3. **Virtual key**: existing dedicated `BIFROST_MCP_VK_OPERATOR` (User-scope env on both
   machines). The master `BIFROST_MCP_VIRTUAL_KEY` is NOT issued to the laptop. The
   OPERATOR key maps to the dedicated `operator` capability profile and can be revoked
   independently without affecting other clients.

## Evidence (2026-11-01, chaoscentral)

- Local bearer route: `POST http://127.0.0.1:8080/mcp` + `Bearer $BIFROST_MCP_VIRTUAL_KEY`
  → `200` (serverInfo `builder v2.0.0`); no auth → `401`.
- Dedicated VKs on :8080: `BIFROST_MCP_VK_OPERATOR` / `BIFROST_MCP_VK_RAVEN` /
  `BIFROST_MCP_VK_OPENCLAW` → all `200`.
- End-to-end through tailnet: `POST https://chaoscentral.tailb71e7e.ts.net/mcp` +
  `Bearer $BIFROST_MCP_VK_OPERATOR` → `200` (serverInfo **`operator v2.0.0`** — the
  dedicated profile, confirming key→profile mapping); no auth → `401`.
- Serve config after change (status): `/` → 127.0.0.1:18789; `/mcp` → 127.0.0.1:8080/mcp;
  `/v1/ingest` → 127.0.0.1:8787/v1/ingest.
- Laptop peer on tailnet: `book4chaos` (100.105.26.72, Windows, online).

## Security properties preserved

- `:18082` process-attested compat route remains source-PC-exclusive (unchanged, fail-closed).
- Remote exposure is tailnet-only, TLS-terminated by Tailscale (Let's Encrypt cert for
  `chaoscentral.tailb71e7e.ts.net`), and still requires a valid Bifrost virtual key (401 otherwise).
- No resolved VK in Git, config files, or this audit; secrets remain Windows User-scope env only.

## Rollback

1. Remove the mount on chaoscentral (restore state captured in
   `ops/bifrost/evidence/tailscale-serve-config-20261101-pre-mcp.json`):
   remove only the `/mcp` mount — do NOT `tailscale serve reset` (it would also drop
   the pre-existing `/` and `/v1/ingest` mounts).
2. Revoke `BIFROST_MCP_VK_OPERATOR` via Bifrost admin if the laptop is decommissioned.
3. Laptop side: re-run `Install-Laptop.ps1 -DisableGateway`, or delete the
   `agentcore-gateway` entry; config backups exist as `config.json.bak-*` per convention.

## Residual risks / notes

- Availability of gateway tools on the laptop now depends on chaoscentral being online
  and both Tailscale daemons up — inherent to the single-canonical-gateway architecture.
- `mcp-remote` is unpinned (matches the figma companion precedent); pin it if supply
  chain policy tightens.
- The laptop is NOT Trust Class A and is not process-attested; its access is exactly the
  `operator` capability profile of the VK.
