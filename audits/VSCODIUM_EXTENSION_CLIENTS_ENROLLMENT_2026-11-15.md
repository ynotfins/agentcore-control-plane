# VSCodium extension clients (Continue, Cline, Zoo Code) AgentCore enrollment - 2026-11-15

**Host:** ChaosCentral
**Operator approval:** Tony, 2026-11-15 (America/New_York), in chat: "Yes add it to continue, you need to add continue as a first class app in agentcore-control-plane first and give both zoocode, cline and continue the highest trust. ... Make sure all three are set up properly."
**Worktree:** `D:\github\agentcore-control-plane\.worktrees\feat-enroll-continue-zoo-cline` on `feat/enroll-continue-zoo-cline`, based on `feat/enroll-vscodium` (`8f26996`, PR #15).

## Scope and non-goals

- Added first-class profiles `ide-profiles/continue`, `ide-profiles/cline`, `ide-profiles/zoo-code-vscodium`, their renderers, matrix rows, README rows and `scripts/bifrost/test_vscodium_extension_clients.py`.
- Corrected the VSCodium profile from PR #15: the live VSCodium profile is `I:\LocalApps\VSCodium\user-data` (`Launch-VSCodium.cmd` passes `--user-data-dir` and `--extensions-dir I:\LocalApps\VSCodium\extensions`). `%APPDATA%\VSCodium` is not read by the running VSCodium, so the 2026-11-15 1:07 AM writes there did not reach the running app.
- Trust Class A: **not applied** (governed_mutable policy). See `governance/proposals/2026-11-15-continue-cline-zoo-trust-class-a.md`.
- Did not edit PROJECT_ANCHOR, AGENTS.md, CLAUDE.md, DOC_AUTHORITY, BLUEPRINT, MASTER_CONFIG, CONTEXT_BLOCK, `contracts/**` governed files, or `docs/agent-policy/**`. No H:, nfa-platform or sister-project access. No reboot, no service restarts.
- The Cursor-hosted `zoo-code` profile is unchanged.

## Live config writes (backups `.bak-20261115-1400`, 2:00 PM America/New_York)

| Client | Live file the client actually reads | Change |
| --- | --- | --- |
| Continue 2.0.0 | `C:\Users\ynotf\.continue\config.yaml` (CONTINUE_GLOBAL_DIR unset) | Added `agentcore-gateway` (streamable-http, `requestOptions.headers.Authorization: Bearer ${{ secrets.BIFROST_MCP_VIRTUAL_KEY }}`); kept `serena`. Replaced stale OmniRoute model ids (`default`, `agent`, `cheap`... not present in OmniRoute 3.8.53 `/v1/models`) with current combo ids plus three KIE models, all with `apiKey: ${{ secrets.OMNIROUTE_API_KEY }}` and `capabilities: [tool_use]`. OpenRouter entry left unchanged. |
| Cline 4.1.26 | `C:\Users\ynotf\.cline\data\settings\cline_mcp_settings.json` (was `{"mcpServers":{}}`) | Added `agentcore-gateway` (streamableHttp, `Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}`, timeout 300). The VSCodium globalStorage `saoudrizwan.claude-dev` copy is a one-time legacy migration source only and was not edited. |
| Zoo Code 3.95 (VSCodium) | `I:\LocalApps\VSCodium\user-data\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json` | Already had `agentcore-gateway`; env reference changed from `BIFROST_MCP_VK_IDE` to `BIFROST_MCP_VIRTUAL_KEY` (builder key for the requested Trust Class A). |

Observed but not changed: `I:\LocalApps\VSCodium\user-data\User\mcp.json` (VSCodium built-in chat) has `agentcore-gateway` with `${env:BIFROST_MCP_VK_IDE}` and `serena`. `I:\LocalApps\VSCodium\user-data\User\.continue\config.yaml` is not read by Continue.

Rollback: copy each `.bak-20261115-1400` over its live file.

## Verification

| Check | Result |
| --- | --- |
| NFA `http://127.0.0.1:8787/health` before / after | 200 / 200 |
| Continue config.yaml parses (PyYAML) | ok; 11 models, mcpServers `serena`, `agentcore-gateway` |
| Cline and Zoo JSON parse | ok |
| `initialize` + `tools/list` using each file's own URL and header, env reference resolved in memory | Continue 168, Cline 168, Zoo 168 tools; all ten `agentcore_memory` tools present |
| OmniRoute via gateway | no OmniRoute tools in `tools/list` or Code Mode `listToolFiles`; OmniRoute is a model provider (ADR-2026-11-04: not a Bifrost upstream) |
| OmniRoute combos referenced by Continue exist in `/v1/models` | yes |
| Native in-extension discovery / memory lifecycle | **not done**: VSCodium window reload required; do not mark `live_validated` |

Extension behavior was checked against the installed code: Continue 2.0.0 `LocalPlatformClient` resolves `${{ secrets.X }}` from `~/.continue/.env`, workspace `.continue/.env`, workspace `.env`, then `process.env`; Cline 4.1.26 expands `${env:VAR}` in MCP config and resolves its settings path as `CLINE_MCP_SETTINGS_PATH` > `CLINE_DATA_DIR` > `CLINE_DIR`/`~/.cline` + `data/settings`.