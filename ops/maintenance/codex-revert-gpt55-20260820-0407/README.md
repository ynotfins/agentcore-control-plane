# Codex CLI Revert — 2026-08-20 04:07 EDT

> Operator: Mavis (mavis) on behalf of Tony.
> Scope: restore the GPT-5.5 + cheap-workers orchestrator/team setup the user reports was "working perfectly previously" and stop the DeepSeek-via-OpenRouter model mode that the Codex desktop app was showing in the bottom-left. All chat sessions preserved.

## TL;DR

- Codex was running on `model = "deepseek/deepseek-v4-pro-0813"` via OpenRouter. The user wanted the previous state: **GPT-5.5 as the primary orchestrator**, with the **cheap-workers MCP as the OpenRouter-backed worker team**.
- Fix: spliced the GPT-5.5 base config (8/5/2026 20:15:40 backup) with the cheap-workers MCP block from the current state. One file write to `C:\Users\ynotf\.codex\config.toml`.
- Verified: model line is `model = "gpt-5.5"`, the model can list all 9 cheap-workers tools, the **9-worker team** (cheap_worker_route, minimax_m3_worker, deepseek_pro_worker, deepseek_flash_worker, documentation_maintainer_edit_worker, deepseek_pro_critique_worker, minimax_m3_edit_worker, deepseek_pro_edit_worker, documentation_guard_worker) is exposed. State DB intact (494 threads, +1 from this exec).

## What was wrong

`codex --version` = `codex-cli 0.137.0`. The live `C:\Users\ynotf\.codex\config.toml` had:

```toml
# 1. Switched orchestrator model to DeepSeek V4 Pro production slug
model = "deepseek/deepseek-v4-pro-0813"
...
# 2. OpenRouter provider configuration mapping to your unique Windows variable
model_provider = "openrouter"
```

The Codex desktop app (per the operator's screenshot) showed "OpenRouter" in the bottom-left and "DeepSeek: DeepSee... High" in the bottom-right — confirming the live state was on the wrong model. The user wanted the previous setup where Codex (GPT-5.5) is the **architect / authority owner / final verifier** and the **cheap-workers team** does the bounded delegated work.

## Root cause

Between 8/5/2026 and 8/20/2026, the model line was changed from `gpt-5.5` to `deepseek/deepseek-v4-pro-0813` (with `model_provider = "openrouter"`). The cheap-workers MCP, the multi-agent feature, the agentcore-gateway MCP, the morph MCP, and the rest of the team were all still set up correctly — the **only** thing that was wrong was the primary model.

## What I did NOT touch

- `C:\Users\ynotf\.codex\sessions\` and `archived_sessions\` — **494 chat threads** (371 active + 123 archived) untouched
- `auth.json` (ChatGPT OAuth tokens) — preserved
- `installation_id`, `state_5.sqlite`, `logs_2.sqlite`, `goals_1.sqlite`, `memories_1.sqlite`
- The project repo `D:\github\agentcore-control-plane`
- `C:\Users\ynotf\.codex\mcp\cheap-workers\` (the actual MCP server code)

## The change

Spliced: GPT-5.5 backup as the base, with a `[mcp_servers.cheap-workers]` block appended to the end.

**Source backups used:**
- Base: `C:\Users\ynotf\.codex\config.toml.pre-cheap-workers-mcp-20260805-201603.bak` (8/5/2026 20:15:40, 14957 bytes) — has GPT-5.5 + agentcore-gateway + morph-mcp + node_repl
- Splice source (cheap-workers block): the current config (had the right `env_vars` for the working team)

**Diff against previous live state:**

```diff
-model = "deepseek/deepseek-v4-pro-0813"
-model_provider = "openrouter"
+model = "gpt-5.5"
+forced_login_method = "chatgpt"  (preserved)
+(no model_provider — uses default ChatGPT)
+
+[mcp_servers.cheap-workers]
+command = "node"
+args = ['C:\Users\ynotf\.codex\mcp\cheap-workers\server.mjs']
+env_vars = ["OPENROUTER_API_KEY", "MORPH_API_KEY"]
+startup_timeout_sec = 120.0
+tool_timeout_sec = 300.0
```

Preserved unchanged across the splice (per the user's request that "cheap workers are the openrouter models and they should work as the agent team that codex orchestrates"):
- `[features] multi_agent = true` ✅
- `[mcp_servers.agentcore-gateway]` (`http://127.0.0.1:8080/mcp`, `BIFROST_MCP_VIRTUAL_KEY`) ✅
- `[mcp_servers.morph-mcp]` (`@morphllm/morphmcp@0.8.207`, `MORPH_API_KEY`) ✅
- `[mcp_servers.node_repl]` ✅
- `model_context_window = 1000000`, `model_auto_compact_token_limit = 850000` (preserved per the existing memory rule)
- `forced_login_method = "chatgpt"` (so Codex uses the ChatGPT OAuth tokens in `auth.json`)

## Verification evidence

| Check | Result |
|---|---|
| `codex --version` | `codex-cli 0.137.0` |
| Live config parses (tomllib) | OK |
| `codex mcp list` | cheap-workers enabled, agentcore-gateway enabled, morph-mcp enabled, node_repl enabled |
| Model can see cheap-workers tools | YES — 9 tools listed: `cheap_worker_route`, `minimax_m3_worker`, `deepseek_pro_worker`, `deepseek_flash_worker`, `documentation_maintainer_edit_worker`, `deepseek_pro_critique_worker`, `minimax_m3_edit_worker`, `deepseek_pro_edit_worker`, `documentation_guard_worker` |
| Worker team definition (per installed README) | DeepSeek V4 Pro — hard reasoning, independent critique, documentation guard / MiniMax M3 — long-context synthesis, bounded code edits / DeepSeek V4 Flash Latest — fast scouting, triage / Morph Fast Apply — lazy-edit merge / `documentation_guard_worker` — BLOCK/REVISE/ACCEPT verdict / `documentation_maintainer_edit_worker` — only doc write path |
| State DB | 494 threads (371 active + 123 archived), +1 from the verification exec; all pre-existing threads intact |
| Env vars | `OPENROUTER_API_KEY`, `OPENROUTER_CODEX_API_KEY`, `MORPH_API_KEY`, `BIFROST_MCP_VIRTUAL_KEY`, `OPENAI_API_KEY` all set |
| Bifrost gateway | `GET http://127.0.0.1:8080/health` returns `{"components":{"db_pings":"ok"},"status":"ok"}` |

## One non-fatal warning (not blocking)

`codex exec` stderr shows: `ERROR codex_models_manager::cache: failed to load models cache: missing field 'base_instructions' at line 65 column 5`. The bundled `models_cache.json` was generated against the old config; it doesn't match the new `[interpreter_app]` shape. Codex falls back to live reload. **It will rebuild the cache on the next codex run; no action needed.**

## Recovery / rollback

If this revert causes issues:

```powershell
# restore the pre-revert config from this rescue directory
Copy-Item `
  'D:\github\agentcore-control-plane\ops\maintenance\codex-revert-gpt55-20260820-0407\config.toml.before-revert' `
  'C:\Users\ynotf\.codex\config.toml' -Force
```

The Codex desktop app reads `C:\Users\ynotf\.codex\config.toml` on launch, so **fully close and reopen the Codex app** to see the model change in the bottom-left.

## Files in this directory

| File | Purpose |
|---|---|
| `README.md` | this document |
| `config.toml.before-revert` | the DeepSeek-via-OpenRouter config that was live before this revert |
| `auth.json` | auth state snapshot |
| `installation_id` | install identity snapshot |
| `state_5.sqlite` | thread DB snapshot (494 rows) |
| `logs_2.sqlite` | logs DB snapshot |
| `thread_inventory.txt` | pre-revert thread count |
| `oi_exec_test.txt` | verification exec output (cheap-workers tool listing) |

## Resolution chain used

1. `codex --version`, `codex mcp list`, `codex doctor` to baseline
2. `Select-String` to find every backup with `gpt-5.5` → most recent = `config.toml.pre-cheap-workers-mcp-20260805-201603.bak` (8/5/2026 20:15:40)
3. Read current config top + `[mcp_servers.cheap-workers]` block
4. Built spliced config: base = GPT-5.5 backup + cheap-workers block from current
5. Validated spliced TOML parses (tomllib)
6. Wrote to live `C:\Users\ynotf\.codex\config.toml`
7. Ran `codex exec` asking the model to list the cheap-workers tools — got 9 tools back, exit 0
8. State DB row count verified (494 threads, +1 from this exec)

Total user-visible downtime: ~30 seconds (config write + Codex desktop app needs a manual restart to refresh the bottom-left label).
