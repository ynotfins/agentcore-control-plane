# Audit: agentcore-gateway exposed 168 eager tools (2026-11-15)

All times are America/New_York (EST, UTC-5).

## Before the fix (2026-11-15 ~4:00 PM EST)

`tools/list` at `http://127.0.0.1:8080/mcp` with Bearer `BIFROST_MCP_VIRTUAL_KEY` (builder):

```
TOOLS=168 SCHEMA_BYTES=177588
  62 eye2byte   35 tentra   23 depwire   21 windows_mcp   10 agentcore_memory   10 arabold_docs
   2 agentcore_capability_catalog   1 each: executeToolCode getToolDocs listToolFiles readToolFile sequential_thinking
```

Live `F:\AgentCore\runtime\bifrost\config.json` (mtime 2026-11-09 11:13 PM, `source_of_truth=config.json`): eye2byte and windows_mcp had `is_code_mode_client=False`; depwire and tentra had it unset. Every other non-essential client was Code Mode. The Bifrost process (pid 23704) had been running since 2026-11-14 8:43 PM.

Reference: `.agentcore/runtime/gateway-tool-inventory.md` (2026-08-31) recorded 46 eager tools.

## Fix applied (2026-11-15 4:03 PM EST)

1. Backups were taken first:
   - `F:\AgentCore\runtime\bifrost\backups\20261115-160312\` (official `Backup-AgentCoreBifrostConfig.ps1`)
   - `config.json.bak-20261115-1603` (both copies)
   - secret-bearing DB snapshot `D:\Autonomy\secrets-backups\bifrost\20261115-1603\config.db` (sqlite online backup)
2. Sent `PUT /api/mcp/client/{id}` with `{is_code_mode_client: true}` for depwire, tentra, eye2byte and windows_mcp. This is the same admin API path as `scripts/bifrost/sync_code_mode_live_clients.py`. No restart.
3. Set the same flags in both live config.json copies so a restart keeps them.

## After the fix

| key | tools | schema bytes |
| --- | ---: | ---: |
| BIFROST_MCP_VIRTUAL_KEY (builder: Cursor, Codex, VSCodium, Zoo Code, Cline, Continue, Hermes, Pi, OpenHands, Antigravity, Open Interpreter, OpenMausBot; :18082 attested clients) | 27 | 30,721 |
| BIFROST_MCP_VK_IDE | 27 | 30,721 |
| BIFROST_MCP_VK_GROKBOT | 27 | 30,721 |
| BIFROST_MCP_VK_OPENCLAW | 25 | 29,993 |
| BIFROST_MCP_VK_OPERATOR | 30 | 27,968 |

`listToolFiles` still lists depwire, eye2byte, tentra, windows_mcp and the other Code Mode servers, so on-demand discovery works. `scripts/bifrost/check_eager_tool_budget.py --skip-registry --live` passes. Without `--skip-registry` it reports the pending locked-registry flags: depwire, tentra, context7. NFA `http://127.0.0.1:8787/health` returned `{"status":"ok"}` before and after.

## Observation (not changed)

`%APPDATA%\Claude\claude_desktop_config.json` holds a literal Bifrost virtual key, not an env reference. That breaks the "never materialize virtual keys in client apps" rule (AGENTS.md). Tony should rotate the key and switch to the :18082 attested route or an env reference.
