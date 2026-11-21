# Bifrost context alignment + OmniRoute default model

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-gateway-client.json`,
`contracts/model-context-profiles.json`
**Approval:** `AUTH-2026-11-18-BIFROST-CONTEXT-AND-OMNIROUTE-DEFAULT`
**Runtime:** `F:\AgentCore\runtime\bifrost` (`\AgentCore\AgentCore-Bifrost-Gateway`)
**Updated:** 2026-11-18

---

## 1. What this pass changed

| Area | Before | After |
| --- | --- | --- |
| Virtual keys in the renderer | 9 (19 `app-*` keys existed only in `config.db`) | 30, all renderer-owned |
| Provider grants per key | builder + ide only | all 30 keys: openai, openrouter, omniroute |
| Bifrost inference providers | openai, openrouter | + `omniroute` custom provider (`127.0.0.1:20128/v1`, chat + responses only) |
| OmniRoute MCP | direct stdio/HTTP entry in every app (63–110 tools eager) | one Bifrost Code Mode upstream, 110 named tools, ~0 eager tokens |
| Code Mode flags | 4 in the registry, 20 in the live DB | 20 in the registry (drift closed) |
| Machine default model | `openrouter/z-ai/glm-5.3` | `deepseek-v4.1-flash` via OmniRoute |
| Context budget | 128k capability-class fallback | `deepseek-v4-flash-1m` (1,048,576) for agent clients |
| Eager gateway surface | 27 tools / ~7.7k tokens | 27 tools / ~7.7k tokens (unchanged, now guaranteed by the registry) |

Measured eager cost per virtual key (JSON-RPC `tools/list`, bytes ÷ 4):

| Profile | Tools | ≈Tokens |
| --- | --- | --- |
| builder, ide, grokbot, every `app-*` | 27 | 7,725 |
| omniroute | 23 | 6,005 |
| operator | 32 | 8,211 |
| reviewer | 25 | 7,180 |
| openclaw | 25 | 7,543 |
| chatgpt | 19 | 6,539 |
| docs-knowledge | 19 | 5,450 |
| database-validator | 22 | 4,992 |

The eager set is deliberately only four servers — `agentcore-capability-catalog`, `agentcore-memory`,
`arabold-docs`, `sequential-thinking` — plus the four Code Mode meta-tools. Everything else (serena,
context7, depwire, tentra, github, playwright, morph, nia, tavily, firecrawl, exa, apify, pi-agents,
cursor-agent, skills-hub, figma-framelink, mcp-prompt-optimizer, omniroute) is reached through
`listToolFiles → readToolFile → executeToolCode`.

## 2. The regression this pass caught

`render_bifrost_config.py` only emits `is_code_mode_client` when the **registry** sets it. Twenty clients
were Code Mode in the live `config.db` but only four were recorded in the registry. The first render
therefore promoted context7, depwire and tentra to eager exposure and the gateway jumped from
**27 tools / 7,725 tokens to 87 tools / 30,389 tokens** (+293%).

Lesson: the registry, not `config.db`, must carry every per-client flag. Any future dashboard-only change
will be reverted by the next render — deliberately — so dashboard edits must be back-ported to the
registry in the same change.

## 3. Adding or changing a virtual key

1. Add the profile/name to `APP_VIRTUAL_KEYS` or the explicit list in `build_virtual_keys`.
2. Generate the token **with the `sk-bf-` prefix** — Bifrost silently replaces any value without it and
   the key then 401s:

   ```powershell
   $t = 'sk-bf-' + [Convert]::ToBase64String((1..50 | ForEach-Object { Get-Random -Max 256 }))
   [Environment]::SetEnvironmentVariable('BIFROST_MCP_VK_APP_<NAME>', $t, 'User')
   ```

3. Render, restart. If the key already existed in `config.db` with a bad value, delete the
   `governance_virtual_keys` row and its `governance_virtual_key_mcp_configs` /
   `governance_virtual_key_provider_configs` children while Bifrost is stopped, then start — the key is
   re-seeded from `config.json`.
4. Verify with an authenticated `tools/list`.

## 4. OmniRoute routing

- Inference: `POST http://127.0.0.1:20128/v1/chat/completions`, canonical model id `deepseek-v4.1-flash`
  (combo: OpenRouter → Together → DeepInfra). `default` and `auto` also resolve to it.
- The direct `ds` connection (api.deepseek.com) is **out of credit** and returns 402. Nothing should pin
  a model to `ds/*`; use the combo alias.
- OmniRoute MCP is exposed through the gateway as `omniroute` (Code Mode, 110 named tools). Do not add a
  direct OmniRoute MCP entry to any client — `AGENTS.md` already forbids duplicate direct entries.
- OmniRoute binds `127.0.0.1` only. Containers (LobeHub, Cloud Mia) cannot reach it; do not widen the
  bind to solve that.

## 5. Rollback

- Renderer/registry: `git revert` the change, re-render, restart the scheduled task.
- Live `config.json`: restore `F:\AgentCore\runtime\bifrost\config.json.bak-*`.
- Virtual keys: delete the added rows and restart; env vars are inert without a matching key.
- Model defaults: reset `LLM_MODEL`, `OPENAI_BASE_URL`, `LLM_BASE_URL`, `ZERO_FORCE_PROVIDER` in the
  Windows User environment and re-login.

## 6. Known open items

- `eye2byte` and `windows-mcp` are registered with restored launch specs but Bifrost discovers zero tools
  for them on restart (both spawn cleanly by hand). Held `enabled: false` / `catalogued_unverified`.
- KIE: 10 catalogue models plus verified manual additions. KIE's Claude and Gemini families do not work
  through the single `responses` connection; 29 speculative additions were removed rather than left in
  the picker.
- Cherry Studio's LevelDB is exclusively locked while the app runs; its MCP/provider verification needs
  the app closed.
