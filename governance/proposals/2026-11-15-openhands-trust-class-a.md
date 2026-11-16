# Proposal: OpenHands as a first-class Trust Class A AgentCore client

- Status: Proposed. The locked contracts and trust-class lists are unchanged.
- Date: 2026-11-15 (America/New_York)
- Requested by: Tony (t321u): "Make sure openhands is set up as a first class app and has the highest trust also and make sure agentcore-gateway mcp server is set up and omniroute is set up and optimized." and "put everything including terminal commands on auto-approve."

## Requested locked edits (Tony to accept)

1. Add OpenHands to the Trust Class A host list wherever it is enumerated: `contracts/global-agent-policy.yaml` / gateway-client contract, and the Trust classes section in `docs/bifrost/CAPABILITY_PROFILES.md`.
2. Add an `openhands` client to `contracts/agentcore-gateway-client.json` with `gateway_url: http://127.0.0.1:8080/mcp`, `gateway_auth_mode: bearer_encrypted_in_app_settings` and `capability_profile: builder`.
3. Record an approvals exception: Tony explicitly chose auto-approve, including terminal commands, for OpenHands (and other agent apps) on 2026-11-15, after being warned that agents could then run any command on ChaosCentral. The nfa-platform protections in `protect-nfa-platform-on-chaoscentral` still apply as policy.

## Already done live (2026-11-15, backups `*.bak-20261115-1612`)

- Gateway: the existing encrypted `agentcore-gateway` entry was kept. It now serves the progressive 27-tool surface (PR #17).
- LLM: added OmniRoute profiles `omniroute-default` (combo `default`), `omniroute-sol-kie-heavy`, `omniroute-agent-glm` and `omniroute-review`, using `os.environ/OMNIROUTE_API_KEY`. `active_profile` and the default agent profile now point at `omniroute-default`. The CLI `config.toml` also routes to OmniRoute.
- Approvals: `conversation_settings.confirmation_mode=false`. CLI `[security] confirmation_mode=false`.
- Skills: agentcore-project-lifecycle and agentcore-tool-discovery were refreshed from `.agents/skills`. OmniRoute skills cli-setup, cli-health, omni-inference and omni-combos-routing were installed from `cheaper-inference/OmniRoute` via `npx skills`.
