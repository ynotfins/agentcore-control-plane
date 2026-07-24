# Codex CLI Rescue — 2026-07-24 01:44 EDT

> Operator: Mavis (mavis) on behalf of Tony.
> Scope: get `codex.exe v0.137.0` (OpenAI Codex CLI) back into a usable state **without** losing any project files, chat rollouts, or auth state. **All preservation goals met.**

---

## TL;DR

- `C:\Users\ynotf\.codex\config.toml` failed to load on every `codex` invocation.
- Root cause: a single line — `model_providers.custom.wire_api = "chat"` — was rejected by Codex 0.137.0, which dropped support for the chat wire format. Codex aborts config parsing on that error, so the entire profile / MCP / auth setup was unavailable.
- Fix: changed that one line to `wire_api = "responses"`. (One token, ~10 s.)
- Verified: `codex doctor` → **17 ok, 0 fail**; `codex mcp list` → 5 servers enabled; ChatGPT websocket handshake succeeds; **all 360 chat threads (238 active + 122 archived) still loadable**.

## What was wrong

`codex doctor` reported `config could not be loaded` with a generic message. A real `codex exec` call surfaced the actual error:

```
Error loading config.toml: `wire_api = "chat"` is no longer supported.
How to fix: set `wire_api = "responses"` in your provider config.
More info: https://github.com/openai/codex/discussions/7782
in `model_providers.custom.wire_api`
```

The TOML itself is valid (Python `tomllib` parses it cleanly), but Codex 0.137.0 enforces a stricter schema and refused to load the file at all.

The bad block was at `config.toml` line 154–159:

```toml
[model_providers.custom]
base_url = "https://api.minimax.io/v1"
experimental_bearer_token = "${env:MINIMAX_API_KEY}"
name = "Custom Endpoint"
requires_openai_auth = false
wire_api = "chat"     # <-- rejected
```

## What I did NOT touch

- `C:\Users\ynotf\.codex\sessions\` — every `rollout-*.jsonl` and the directory tree (≈3.6 GB).
- `C:\Users\ynotf\.codex\archived_sessions\`
- `C:\Users\ynotf\.codex\session_index.jsonl`
- `C:\Users\ynotf\.codex\auth.json` and the `auth.json.backup-*` family
- `C:\Users\ynotf\.codex\backups\`
- `C:\Users\ynotf\.codex\plugins\`, `skills\`, `memories\`, `sqlite\`, `state_5.sqlite`, `logs_2.sqlite`, `goals_1.sqlite`, `memories_1.sqlite`
- `D:\github\agentcore-control-plane` working tree (intact; HEAD = `main`)

The only write to the live codex home was a one-token edit to `config.toml`. Everything else was copied into this directory.

## The change (diff)

```diff
 [model_providers.custom]
 base_url = "https://api.minimax.io/v1"
 experimental_bearer_token = "${env:MINIMAX_API_KEY}"
 name = "Custom Endpoint"
 requires_openai_auth = false
-wire_api = "chat"
+wire_api = "responses"
```

## Verification evidence

| Check | Result |
|---|---|
| `codex doctor` | `17 ok · 1 idle · 3 notes · 0 warn · 0 fail` (config now loads; all sqlite DBs pass integrity) |
| `codex mcp list` | 5 servers enabled: `codex-security`, `node_repl`, `sites-design-picker`, `agentcore-gateway` (http://127.0.0.1:8080/mcp), `github` |
| ChatGPT reachability | websocket `HTTP 101 Switching Protocols` against `wss://chatgpt.com/backend-api/...` |
| OpenAI API reachability | `https://api.openai.com/v1` reachable |
| Sessions intact | state DB agrees with file inventory: 238 active + 122 archived rollouts, 0 scan errors, 0 malformed file names, 0 missing rows, 0 stale rows, 0 archive mismatches, 0 duplicate thread IDs |
| `codex exec` round-trip | session was created (id `019f92ab-3d9c-7d52-99c8-56298c3ce3f2`), config parsed, request reached ChatGPT — see Side Issue #1 below for the only remaining error |

## Side issues found (NOT fixed; flagged for operator decision)

### 1. `model = "gpt-5.6"` is not a real OpenAI/ChatGPT model

`config.toml` line 13 sets `model = "gpt-5.6"`. When the request reaches the ChatGPT backend (auth mode = `chatgpt`), it returns:

```
HTTP 400 invalid_request_error
"The 'gpt-5.6' model is not supported when using Codex with a ChatGPT account."
```

The local config loader is happy; only the network call fails. Likely intended values: `gpt-5`, `codex-1`, or one of the `[interpreter_app] profiles.*` IDs already defined in this file. **Decision needed from operator.**

### 2. `service_tier` declared twice with conflicting values

- Line 19 (top-level): `service_tier = "default"`
- Line 25 (`[desktop]`): `default-service-tier = 'priority'`

Top-level `service_tier` is not a recognized top-level Codex field; the desktop one is. Not blocking, but should be cleaned up.

### 3. `enabled-reasoning-efforts` contains an unknown variant

`config.toml` line 36:

```toml
enabled-reasoning-efforts = ["low", "medium", "high", "xhigh", "ultra", "max"]
```

`models_cache` complains: `unknown variant 'max', expected one of 'none', 'minimal', 'low', 'medium', 'high', 'xhigh'`. `"ultra"` is also non-standard. Not blocking — codex falls back to the recognized set. Suggest `["low", "medium", "high", "xhigh"]`.

### 4. `model_providers.custom` now uses `responses` wire, which `https://api.minimax.io/v1` may not speak

The custom provider points to the MiniMax API endpoint. If that endpoint only accepts the chat-completions wire, calls to that profile will fail at runtime (separate from the global `model = "gpt-5.6"` issue). Verify with `codex exec --profile <id>` after the model issue is resolved, or drop the custom provider if unused.

### 5. Non-UTF-8 byte in `C:\Users\ynotf\.codex\skills\mcp-tool-router\SKILL.md`

`failed to read file: invalid utf-8 sequence of 1 bytes from index 168`. Cosmetic; skill is silently skipped. Worth re-saving the file as UTF-8 (no BOM) when convenient.

### 6. Current `config.toml` is 12 KB; the last known-good was 105 KB

The known-good from 2026-06-24 (`config.toml.known-good-20260624-140603`) had a much larger `[interpreter_app] profiles` array, more MCP servers, more `model_providers`, and a bigger `[projects]` trust list. The current 12 KB file is a stripped-down version (last touched 2026-07-17 around the bifrost cutover). If the operator wants the full profile set back, the right move is to **diff the known-good against the current and graft forward only the keys that were intentionally removed**, not blindly overwrite — the current file is what is producing working sessions today.

A copy of the known-good is in this directory as `config.toml.known-good-20260624-140603`.

## Recovery / rollback

If the change needs to be reverted:

```powershell
# 1. Stop codex (interactive TUI / app-server)
# 2. Restore the pre-fix file from this directory:
Copy-Item `
  'D:\github\agentcore-control-plane\ops\maintenance\codex-rescue-20260724-0144\config.toml.bad' `
  'C:\Users\ynotf\.codex\config.toml' -Force
# 3. Re-validate. Note: this WILL re-break codex load, so this is only for
#    forensic comparison — the only safe way to load codex is with the
#    wire_api = "responses" change applied.
```

If codex is in a worse state for any reason, the full sessions + auth tree can be restored from the matching subdirectories in this rescue folder.

## Files in this directory

| File | Purpose |
|---|---|
| `README.md` | this document |
| `config.toml.bad` | the broken live config as it stood at 01:44 EDT (pre-fix) |
| `config.toml.known-good-20260624-140603` | the last known-good 105 KB config (pre-stripped) |
| `config.toml.bifrost-cutover-20260712-231448.bak` | snapshot from the 2026-07-12 bifrost cutover |
| `auth.json` | auth state as of 01:44 EDT |
| `session_index.jsonl` | session index as of 01:44 EDT |
| `sessions/` | full sessions tree snapshot (≈3.6 GB, 360 threads) |
| `archived_sessions/` | archived sessions snapshot |

## Resolution chain used

1. `codex doctor` → `config could not be loaded` (no detail)
2. `codex doctor --json` → still no detail
3. `codex exec "echo ok"` → real error: `wire_api = "chat"` not supported
4. `Select-String 'wire_api\s*=\s*"chat"' config.toml` → exactly one match (line 159)
5. Edit the one line; re-run doctor; re-run `codex mcp list`; sanity `codex exec` round-trip; read `state_5.sqlite` for thread inventory.

Total downtime: ≈10 s of CLI interaction, no agent process kill required.
