# Proposal: enforce the progressive (Code Mode) agentcore-gateway tool surface

- Status: Proposed (not applied to locked docs or contracts)
- Date: 2026-11-15 (America/New_York)
- Requested by: Tony (t321u): "there are only supposed to be a handful of essential tools exposed ... the agent has to request a tool list and then activate and deactivate the tools as it needs them ... write a rule that enforces the proper setup of this in the future."
- Evidence: `audits/GATEWAY_TOOL_SURFACE_168_2026-11-15.md`
- Rollback of the live fix: `docs/bifrost/ROLLBACK-20261115-progressive-surface.md`

## Problem

On 2026-11-15 Zoo Code (VSCodium) reported 168 tools from `agentcore-gateway`. A live `tools/list` with the builder key (`BIFROST_MCP_VIRTUAL_KEY`) returned 168 tools and 177,588 bytes of tool schema. Every builder/ide client (Cursor, Codex, VSCodium, Zoo Code, Cline, Continue, Antigravity, Hermes, Pi, Open Interpreter, OpenHands and the :18082 attested clients) got the same surface. The intended design is Bifrost Code Mode (AGENTS.md "Code Mode tool discovery"; commit b24b34d "Shrink Bifrost eager MCP surface"). Agents get a small eager set plus `listToolFiles`, `readToolFile`, `getToolDocs` and `executeToolCode`, and load other tools on demand.

Four upstream clients were eager (`is_code_mode_client` false or unset):

| client | eager tools | how it became eager |
| --- | ---: | --- |
| eye2byte | 62 | Live-only upsert on 2026-11-09 (t286u, `F:\AgentCore\runtime\bifrost\backups\20261109-204959\patch-t286u.py`) with `is_code_mode_client: False`. All 62 tools were granted to builder, ide and openclaw. Not in the registry. |
| windows_mcp | 21 | Same t286u patch, same flag, same grants. Not in the registry. |
| tentra | 35 | PR #9 (e6d253d, 2026-11-04) moved the server to `enabled: true` without setting `is_code_mode_client: true`. It went live at the t286u restart on 2026-11-09. |
| depwire | 23 | Same as tentra. |

## Proposed rule (for Tony to adopt into AGENTS.md / global-agent-policy / registry schema)

1. **Code Mode by default.** Every enabled Bifrost MCP client must set `is_code_mode_client: true`. The only exceptions are on the essential eager allowlist: `agentcore_memory`, `sequential_thinking`, `agentcore_capability_catalog`, `arabold_docs` and `agentcore_project_router` (operator VK only). Adding to the allowlist requires Tony's explicit approval, recorded in a proposal.
2. **Eager budget.** A builder/ide/grokbot/openclaw `tools/list` must stay at or below 30 tools (27 on 2026-11-15). Any admission, upsert, restart or render that raises it fails closed.
3. **No live-only clients.** Do not add a client to the live `F:\AgentCore\runtime\bifrost\config.json` or `config.db` unless the same change is in `contracts/bifrost-upstream-mcp-registry.json` (or an accepted proposal). The t286u eye2byte/windows_mcp upsert broke this rule.
4. **Latency is not an exemption.** Interactive or desktop servers such as eye2byte and windows_mcp still go behind Code Mode. If one needs to be eager for latency, it goes through rule 1 with a measured token cost.
5. **Mandatory check.** Run `python scripts/bifrost/check_eager_tool_budget.py --live` (added in this PR) before and after any Bifrost admission, restart, render or client-config change, and record the output as evidence. A FAIL blocks completion.
6. **Client configs never fix discovery.** Never paste upstream servers into IDE configs to work around Code Mode visibility. This restates the existing AGENTS.md rule.

## Locked-contract changes requested (not applied)

In `contracts/bifrost-upstream-mcp-registry.json`:
- `servers.depwire.is_code_mode_client: true`
- `servers.tentra.is_code_mode_client: true`
- `servers.context7.is_code_mode_client: true` (already true live since t286u)
- Either admit `eye2byte` and `windows-mcp` with `is_code_mode_client: true` and a reviewed grant set, or remove them from live. The t286u proposal `docs/bifrost/contract-proposal-t286u-mcp-servers.md` (branch `chore/bifrost-mcp-t286u-20261109`) asked for `false`. This proposal supersedes that flag.
- Optional, for an even smaller "handful": move `arabold_docs` to Code Mode. That takes builder from 27 to 17 eager tools. It overrides the deliberate eager-Arabold decision (`scripts/bifrost/measure_arabold_eager_tokens.py`), so Tony must decide.

Until those contract edits land, an official re-render from the registry (`render_bifrost_config.py` via `Install-AgentCoreBifrostGateway.ps1`) would make depwire and tentra eager again. `Start-AgentCoreBifrostGateway.ps1` runs `sync_code_mode_live_clients.py`, which prefers the live config.json flags, so a plain restart keeps the fix.

## Profiles

The existing virtual-key capability profiles (builder, ide, reviewer, docs-knowledge, database-validator, operator, chatgpt, openclaw, grokbot) set what a client may reach. Code Mode sets what gets pushed into the context window. With this rule every profile shares the same small eager core, and the rest of each profile's grants are reachable on demand. Proposed per-app assignment (needs Tony's approval):
- coding hosts (Cursor, Codex, VSCodium/Zoo Code, OpenHands, OpenCode, Cline, Continue, ZCode): builder
- review-only runs: reviewer (`BIFROST_MCP_VK_REVIEWER`)
- research/docs agents: docs-knowledge (`BIFROST_MCP_VK_DOCS_KNOWLEDGE`)
- gateway administration: operator only

## Attribution

- eye2byte + windows_mcp eager: the t286u session on 2026-11-09, roughly 8:50 PM to 11:53 PM EST. The `t286u` id is a Grok Bot turn id. Artifacts are under `F:\AgentCore\runtime\bifrost\backups\20261109-204959\`, and commit 217015f is on `chore/bifrost-mcp-t286u-20261109`. All local agents commit as `R3lentless_Grind`, so git author alone cannot name the agent.
- depwire + tentra eager: commit 83ce674 (2026-11-04 10:18 PM EST, local agent under Tony's git identity), merged as PR #9 (e6d253d). PR #10 (Cursor Agent) hardened them without adding Code Mode.
- Surfaced, not caused: Grok Bot's 2026-11-15 ~1:07 AM EST VSCodium/Zoo Code enrollment. It pointed those clients at the builder key, which was already exposing 168 tools.
