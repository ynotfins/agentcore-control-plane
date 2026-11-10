# Dual control-plane continuity cookbook

Do **not** merge these repos. Open together via `D:\github\agentcore-control-plane\agentcore-and-postgresql18.code-workspace` (shortcut already working — do not rebuild).

| Plane | Path | `project_key` | Role |
| --- | --- | --- | --- |
| AgentCore | `D:\github\agentcore-control-plane` | `agentcore-control-plane` | Architecture, Bifrost, MCP, enrollment, IDE policy |
| PostgreSQL 18 | `D:\postgreSQL18-control-plane` | `postgresql18-control-plane` | DB ops only; defers architecture to AgentCore |

## Continuity contract

1. One MCP front door: `agentcore-gateway` via Bifrost.
2. Memory only through `agentcore-memory`.
3. Use the **exact enrolled** `project_key` that matches the active write root. Never cross-write the other plane’s key.
4. Enrollment is path-exact in `contracts/agentcore-project-enrollment.json`.

## Grok Bot (canonical cloud — one recipe)

- URL: `https://agentcore-grokbot.4axe.com/mcp`
- Header: `x-bf-vk` = raw `BIFROST_MCP_VK_GROKBOT` (no Bearer prefix in Grok UI)
- Client ID blank; no OAuth Connect
- Task: `\AgentCore-Grokbot-Cloudflare-Tunnel` (Hidden; do not recreate)
- Non-canonical: loopback `:8080` Bearer (local), Tailnet Serve (alternate), Funnel (optional fallback only)
- Details: `ide-profiles/grokbot/MCP_ENROLLMENT_UI.md`

## Docs after every material task

`documentation-reconciliation` always covers `MASTER_CONFIG_AND_PROMPT.md`, `ide-profiles/**`, and `contracts/agentcore-gateway-client.json`. Run docs-guardian before claiming done. Governed files need AUTH + documentation maintainer path.

## Automations

- Silence AgentCore/NFA/OmniRoute flashers only.
- Keep SwarmClaw-required startups.
- Leave `\AgentCore\DailyDriftCheck` Disabled.
- Do not take ownership of Grokbot automations; Paperclip inventory recording is separate.
