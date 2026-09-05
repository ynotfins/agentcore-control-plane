# Bifrost v2 Runtime Acceptance - 2026-09-05

Scope: AgentCore Bifrost gateway upgrade and reliability hardening for the local
developer PC.

Local evidence timestamp: 2026-09-04T23:40:44-04:00.

Branch: `setup/zoo-code-qdrant-nfa-20260820`

Baseline commit before this audit note: `55bdd82`

## Official Version Basis

- Bifrost v2.0.0 is the current stable 2.0 HTTP transport target documented by
  Bifrost: https://docs.getbifrost.ai/changelogs/v2.0.0
- Bifrost MCP auth modes include per-user and Virtual Key identity mapping:
  https://docs.getbifrost.ai/mcp/auth/overview
- Bifrost Guardrails are Enterprise-only and require the Enterprise image:
  https://docs.getbifrost.ai/deployment-guides/config-json/guardrails

## Passed Evidence

- Runtime Bifrost version: `/api/version` returned `v2.0.0`.
- Runtime health: `/health` returned HTTP 200.
- Gateway endpoint: TCP `127.0.0.1:8080` was listening.
- Authenticated MCP handshake succeeded through `agentcore-gateway`.
- Authenticated MCP `tools/list` returned 46 tools.
- Cursor global MCP config had exactly one MCP server entry: `agentcore-gateway`.
- Cursor global MCP endpoint matched `http://127.0.0.1:8080/mcp`.
- Cursor global MCP used environment placeholders and contained no obvious secret literals.
- OpenRouter MCP was registered exactly once through Bifrost.
- OpenRouter MCP state was `healthy`.
- OpenRouter MCP authenticated tool count was 22.
- Semantic cache plugin was registered exactly once and reported `active`.
- Redis Stack cache backend was running as Docker container
  `agentcore-bifrost-redis-stack` with restart policy `unless-stopped` and port
  `127.0.0.1:6381`.
- Code Mode meta-tools exposed Morph and Playwright tool files.
- Forbidden ordinary IDE tool patterns were absent from builder exposure:
  `swarm`, `postgres`, `psql`, `whole_drive`, `bifrost_admin`.
- Contract and renderer validation passed:
  - `scripts/bifrost/validate_contracts.py`
  - `scripts/bifrost/test_contracts.py`
  - focused pytest set for Bifrost renderer/watchdog and Cursor hook gates
- Tracked source secret scan passed.
- Live Codex config was sanitized so raw OpenRouter/related key literals are no
  longer present in `C:\Users\ynotf\.codex\config.toml`.

## v2 OAuth Migration Finding

Bifrost v2 owns `oauth_config_id` and OAuth token persistence in
`F:\AgentCore\runtime\bifrost\data\config.db`. Runtime state file
`F:\AgentCore\runtime\bifrost\state\oauth-clients.json` is operator evidence
only. Rendered Bifrost config must keep public `oauth_config` values and must
not emit `oauth_config_id`.

Source changes now enforce that:

- `scripts/bifrost/render_bifrost_config.py` never renders `oauth_config_id`.
- `scripts/bifrost/test_rendered_config_drift.py` has regression coverage for
  the above behavior.
- `contracts/bifrost-upstream-mcp-registry.json` and
  `docs/operations/OPENROUTER_MCP.md` no longer instruct agents to render
  `oauth_config_id` into config.json.

## Cursor Cost-Control Finding

Cursor entered a suspected prompt/agent loop and consumed approximately 60% of
the operator's monthly expensive-model budget. Codex stopped Cursor processes
twice during this run. Cursor later relaunched via `explorer.exe`; no
AgentCore/Cursor scheduled task launch path was proven. The only matching
scheduled task, `CursorElevationTest`, currently runs `cmd /c exit 0` and does
not launch Cursor.

Current policy/hook source now fails closed before model submission when
AgentCore cannot establish a healthy durable project session. This is deliberate:
the prior fail-open behavior allowed expensive prompts to run while the gateway
or recovery path was unhealthy.

## Remaining Gates

This audit is not final acceptance. These gates remain open:

- Watchdog is registered but currently disabled and not installed as
  SYSTEM/Highest. Non-elevated enable attempts returned `Access is denied`.
- Zero-popup watchdog behavior is source-configured but not live-proven until the
  elevated registration is applied.
- Failure-recovery proof is not complete until the watchdog is enabled in
  noninteractive service context and a bounded restart/recovery test passes.
- Post-PC-restart proof is not complete. Gateway, Redis Stack, OpenRouter MCP,
  semantic cache, and watchdog state must be rechecked after a real restart.
- Git history still previously contained exposed provider keys in tracked
  recovered MiniMax artifacts and local Codex config. Current source/live config
  are cleaned, but those provider keys should be rotated.

## Next Operator Command

Run from an elevated PowerShell session:

```powershell
cd D:\github\agentcore-control-plane
pwsh -NoProfile -ExecutionPolicy Bypass -File .\ops\bifrost\Install-AgentCoreBifrostGateway.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File .\ops\bifrost\Test-AgentCoreBifrostGateway.ps1 -RequireWatchdogEnabled -RequireSemanticCacheHealthy -RequireOpenRouterMcpHealthy
```

After the elevated verifier passes, restart the PC once and rerun:

```powershell
cd D:\github\agentcore-control-plane
pwsh -NoProfile -ExecutionPolicy Bypass -File .\ops\bifrost\Test-AgentCoreBifrostGateway.ps1 -RequireWatchdogEnabled -RequireSemanticCacheHealthy -RequireOpenRouterMcpHealthy
pwsh -NoProfile -ExecutionPolicy Bypass -File .\ops\bifrost\Invoke-AgentCoreOpenRouterMcpReauth.ps1 -Json
```
