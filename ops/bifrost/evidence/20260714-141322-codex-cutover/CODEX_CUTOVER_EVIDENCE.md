# AgentCore Bifrost Gateway Codex Cutover Evidence — 2026-07-14

## Scope

Install and validate the single non-Swarm AgentCore Bifrost MCP baseline in
Codex while preserving all non-MCP Codex settings and Codex-managed optional
MCP integrations.

No secret value was printed, copied into source control, or written to this
evidence file. No `.env` file was created. SwarmRecall, SwarmVault, SwarmClaw,
OpenClaw, and ClawX were not touched.

## Ecosystem Lock

| Item | Detected value |
| -- | -- |
| Repository | `D:\github\agentcore-control-plane` |
| Branch | `feature/bifrost-mcp-gateway-cutover` |
| Codex client | `codex-cli 0.137.0` |
| Codex live config | `C:\Users\ynotf\.codex\config.toml` |
| Config syntax | TOML |
| Gateway runtime | Native Bifrost `v2.0.0-prerelease1` |
| Gateway app directory | `H:\AgentRuntime\bifrost` |
| MCP protocol | `2025-06-18` |

## Documentation Evidence

- Local `arabold_docs-list_libraries` succeeded through Bifrost, but no Codex
  or OpenAI collection was indexed. This established the required local-docs
  miss.
- The current official OpenAI Codex configuration manual for the installed
  client was then checked. It defines `bearer_token_env_var` for
  `Authorization: Bearer`, and `startup_timeout_sec` / `tool_timeout_sec` for
  MCP timeouts. It defines `http_headers` as static header values.
- Result: use `bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"`; do not place
  `${env:BIFROST_MCP_VIRTUAL_KEY}` in Codex `http_headers`; map the shared
  300-second timeout to both supported Codex timeout fields.

## Pre-Edit Runtime Proof

| Check | Result |
| -- | -- |
| Scheduled task | `\AgentCore\AgentCore-Bifrost-Gateway` — `Running` |
| Task last result | `0x41301` (task is currently running) |
| Restart policy | 3 retries, 1-minute interval |
| Task action | PowerShell 7 launches `ops\bifrost\Launch-AgentCoreBifrostGateway.ps1` |
| Working directory / app directory | `H:\AgentRuntime\bifrost` |
| Bind | `127.0.0.1:8080` only, PID `36816` at validation time |
| Health | `GET http://127.0.0.1:8080/health` returned `200` |
| Bifrost binary SHA-256 | `201BB18F1427CAE4E02B03A85DDF689665E3B7A2A78ADDC16CE2822F1A63272A` |

Authenticated direct MCP validation used the Windows User environment key
without displaying it:

- `initialize`: HTTP 200, server `builder`, protocol `2025-06-18`
- `notifications/initialized`: HTTP 202
- `tools/list`: HTTP 200, 127 visible tools
- Safe read-only call: `arabold_docs-list_libraries`, HTTP 200, succeeded

Expected prefix counts:

| Prefix | Count |
| -- | --: |
| `arabold_docs` | 10 |
| `depwire` | 23 |
| `tentra` | 35 |
| `sequential_thinking` | 1 |
| `context_fabric` | 5 |
| `filesystem` | 14 |
| `playwright` | 24 |
| `cursor_agent_mcp` | 9 |
| `agentcore_memory` | 2 |
| `agentcore_project_router` | 4 |

Forbidden tool-name patterns `swarm`, `postgres`, `psql`, `whole_drive`, and
`bifrost_admin` each returned zero matches.

## Backup and Live Config

| Item | Value |
| -- | -- |
| Pre-edit SHA-256 | `BCA9D972C8621CF39CE92324F927ECA778125B839D13FD7C174D7E6185060676` |
| Backup | `C:\Users\ynotf\.codex\backups\agentcore-bifrost-cutover\20260714-141322\config.toml` |
| Backup SHA-256 | `BCA9D972C8621CF39CE92324F927ECA778125B839D13FD7C174D7E6185060676` |
| Backup hash match | Yes |
| Post-edit SHA-256 | `82024FCCEB0403A91EFC9A16079DE107253340265F6368E5CBB4F1247B737344` |

The live user-configured MCP entries are now:

- `agentcore-gateway` — the single AgentCore non-Swarm baseline
- `node_repl` — Codex-managed local runtime integration, preserved unchanged

`MCP_DOCKER` was removed because it duplicated capabilities served through
Bifrost. Plugin-provided MCP servers are managed separately by Codex and were
not edited.

Sanitized live gateway block:

```toml
[mcp_servers.agentcore-gateway]
url = "http://127.0.0.1:8080/mcp"
bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"
enabled = true
startup_timeout_sec = 300
tool_timeout_sec = 300
```

Validation proved:

- Python `tomllib` parsed the complete live file.
- Every parsed non-MCP setting is identical to the backup.
- The `node_repl` table is identical to the backup.
- `MCP_DOCKER`, static gateway `http_headers`, and generic
  `timeout_seconds` are absent.
- `codex mcp list --json` resolved the gateway as `streamable_http` with
  `bearer_token_env_var = BIFROST_MCP_VIRTUAL_KEY` and both 300-second
  timeout fields.

## Project Router and Fresh Codex Acceptance

The verified Git root `D:\github\agentcore-control-plane` was activated through
`agentcore_project_router-project_activate`; a subsequent
`agentcore_project_router-project_status` returned that same active project.

A fresh ephemeral Codex 0.137.0 host loaded the edited live config and used the
IDE MCP discovery layer. It invoked:

- server: `agentcore-gateway`
- tool: `arabold_docs-list_libraries`
- status: `completed`
- final marker: `CODEX_AGENTCORE_GATEWAY_OK tool=arabold_docs-list_libraries`

This is the IDE/client acceptance proof; `codex mcp list` alone was not treated
as sufficient.

## Source-of-Truth Alignment

Updated the Codex-specific contract note, renderer, cutover script, master
example, unified setup guide, and reusable global IDE prompt so future renders
use the native Codex environment-backed Bearer field and supported timeout
fields. The cutover script now also removes `MCP_DOCKER` from Cursor and Codex
where it would reintroduce the duplicate gateway.

Validation:

- `python scripts\bifrost\validate_contracts.py` — passed
- Codex renderer JSON parse and exact-value assertions — passed
- PowerShell cutover script parse — passed
- `git diff --check` for touched authority/renderer/script files — passed
- High-confidence source secret scan — passed; the only broad-pattern candidate
  was the literal environment variable name `BIFROST_MCP_VIRTUAL_KEY`, not a
  credential value

## Preserved Out-of-Scope Codex Warnings

These pre-existing issues did not block normal Codex gateway discovery and were
not changed because they are outside MCP cutover scope:

- `codex exec --strict-config` rejects the existing `[interpreter_app]` table.
- The models cache contains an unsupported `max` reasoning variant.
- Several local/plugin skill manifests emit validation warnings.
- The optional plugin-provided GitHub MCP lacks `GITHUB_PAT_TOKEN` in the fresh
  child process.

## Rollback

Fully quit Codex, restore the hash-verified backup over
`C:\Users\ynotf\.codex\config.toml`, then restart Codex and re-run TOML parsing,
`codex mcp list --json`, and a fresh gateway tool call. Rollback restores the
old `MCP_DOCKER` and stale gateway schema as well, so use it only if this
cutover must be reverted.
