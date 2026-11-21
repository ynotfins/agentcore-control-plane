# Gateway connection stability — Bifrost P1 ADDON (2026-09-16 / verified 2026-09-17)

## Verdict

Mid-session `agentcore-gateway` drops observed in Cursor are a **client streamable-HTTP session lifecycle** issue, not a Bifrost process crash. Bifrost `/health` stayed `status=ok` during drops. Do **not** recycle Bifrost to "fix" reconnects unless `/health` is failed and the operator approves a recycle.

## Evidence (this machine)

| Check | Result |
| --- | --- |
| `GET http://127.0.0.1:8080/health` | `200` `{"status":"ok","components":{"db_pings":"ok"}}` |
| Serena shim `GET http://127.0.0.1:18090/health` | healthy after clean Direct start |
| Code Mode live `tools/list` absence | PASS — `audits/bifrost/CODE_MODE_LIVE_TOOLSLIST_ABSENCE_2026-09-16.json` |
| Serena identity injection (arg, no sticky STDIO) | PASS — `audits/bifrost/SERENA_IDENTITY_INJECTION_EVIDENCE_2026-09-16.json` |

## Root cause (Cursor / streamable HTTP)

1. Cursor opens a Bifrost MCP session with streamable HTTP (`Authorization: Bearer` via User-scope `BIFROST_MCP_VIRTUAL_KEY`).
2. Long idle, IDE sleep, or transport reset closes the MCP session id.
3. The next tool call fails until Cursor reconnects / re-initializes.
4. Operators may interpret that as "gateway died." `/health` still returns ok — Bifrost did not need a recycle.

## Mitigations (no policy weaken)

- Prefer reconnect / reload MCP in the IDE before touching Bifrost.
- Optional: raise client-side tool timeout toward 5 minutes where the client schema supports it (contract already uses `timeout_seconds: 300`).
- Keep `disable_content_logging: true`. Do not enable content logging to debug reconnects.
- Do not weaken `device_assertion`, enrollment, or Stage B to paper over drops.

## Trust Class A expansion (eigent / zed)

As of 2026-09-17 source enrollment:

- `contracts/agentcore-gateway-client.json` — eigent + zed `gateway_auth_mode=process_attested_proxy`, `gateway_url=http://127.0.0.1:18082/mcp`, enabled.
- `ops/bifrost/Resolve-AgentCoreBuilderCaller.ps1` allowlists:
  - `%LOCALAPPDATA%\Programs\Eigent\Eigent.exe`
  - `%LOCALAPPDATA%\Programs\Zed\Zed.exe`
- Renderers: `renderers/gateway-clients/{eigent,zed}.json` active headerless templates.
- Live import still requires `Reconcile-AgentCoreTrustAClients.ps1` + client restart. Never paste the VK into live JSON.

## memory_status

Cursor/builder path (2026-09-17T21:17:33Z): `agentcore-memory` via gateway returned `ok=true`, `status=healthy`, PG18 `127.0.0.1:55433` reachable, neutral SwarmRecall health 200, device identity legacy_compat with 1 active key. Secrets never returned.

Eigent/Zed native memory lifecycle remains `awaiting_operator_import` until each client completes a post-reconcile `memory_status` call through `:18082` after live MCP import + restart.

## Residual (session-scope declare expansion required)

Source Trust A for eigent/zed is in contract/resolver/renderers/profiles. Still blocked by Stage B undeclared targets:
- `ide-profiles/IDE_CAPABILITY_MATRIX.yaml` (matrix↔profile sync)
- `ide-profiles/{eigent,zed}/MCP_CONFIG_TEMPLATE.json`
- `scripts/bifrost/test_client_secret_policy.py`
- `scripts/render_ide_rules.py` + derived GLOBAL_RULES/INSTALL/VALIDATION

## Non-goals

- No Bifrost recycle in this task.
- No NFA / Swarm work.
- No secret material in Git or live client files.
