# ZCode Host-Native MCP Companions — Exception Record — 2026-10-31

**Approval:** `AUTH-2026-10-31-ZCODE_DIRECT_MCP_COMPANIONS`
**Host:** ZCode 3.10.1 (`C:\Program Files\ZCode\ZCode.exe`), Trust Class A
**Live target:** `C:\Users\ynotf\.zcode\cli\config.json`
**Backup:** `C:\Users\ynotf\.zcode\cli\config.json.bak-20261031-051205`
**Authority gates:** `contracts/global-agent-policy.yaml` → `single-gateway`; `ide-profiles/IDE_CAPABILITY_MATRIX.yaml` → `direct_mcp_companion_policy`

## Decision

The operator requires five MCP servers exposed as **direct tool surfaces** in ZCode, not as
gateway-mediated or Code Mode-only routes. This record grants a host-scoped, named, version-pinned
exception. `agentcore-gateway` remains the only AgentCore memory/governance MCP front door; this
exception adds no memory, Swarm, administrative, or model-routing authority.

Scope is exactly five stdio servers in ZCode, each launched from
`I:\LocalApps\ZCode\mcp\<name>-mcp-launch.cmd`. No other IDE, no Bifrost runtime change, no
registry change.

## Per-server parity evidence (live capability catalog, 2026-10-31)

| Server (ZCode name) | Catalog status | Gateway tools | Parity finding |
| --- | --- | --- | --- |
| `playwright` | active, builder, Code Mode | 24, none first-class | Gateway exposes Playwright only through `executeToolCode`; ZCode has no direct `browser_*` tool. Route also failed `initializeServer` until the Chrome path repair below. |
| `sequential-thinking` | active, builder | 1 (`sequential_thinking-sequentialthinking`) | Direct duplicate, operator-requested: one prefixed gateway tool vs. the server's own `sequentialthinking`. |
| `filesystem` | `dormant_project_scoped`, `enabled=false` | 0 (no profile) | Not executable through Bifrost; native IDE filesystem access exists but is not an MCP tool surface. |
| `github-mcp` / `github` | `deferred`, `enabled=false` | 0 | Not executable; replacement was task-scoped `gh` CLI only, which is not a tool surface available to the model directly. |
| `postgresql-mcp` / `postgres` | `rejected` | 0 | Not executable; replacement (`agentcore-memory`) exposes no raw SQL. |

The catalog was queried through `agentcore_capability_catalog-get_capability_detail`, not inferred
from the registry snapshot.

## Exact pins

| ZCode name | Package | Pin | Note |
| --- | --- | --- | --- |
| `playwright` | `@playwright/mcp` | `0.0.78` | Mirrors the Bifrost registry pin; verified working. |
| `sequential-thinking` | `@modelcontextprotocol/server-sequential-thinking` | `2.0.0` | Registry pin `2026.7.4` is deprecated (date-based); 2.0.0 is the current semver release. |
| `filesystem` | `@modelcontextprotocol/server-filesystem` | `2.1.0` | Registry pin `2026.7.10` is deprecated (date-based); 2.1.0 is the current semver release. |
| `github` | `@modelcontextprotocol/server-github` | `2025.4.8` | Final release; package archived but functional (26 tools). |
| `postgres` | `@modelcontextprotocol/server-postgres` | `0.6.2` | Final release; package archived but functional (1 tool). |

No `@latest` and no floating ranges. Every launcher pins the full version.

## Secret handling

No secret appears in `config.json` or in any launcher file.

- `github`: launcher reads `GITHUB_PERSONAL_ACCESS_TOKEN` from the Windows **User** environment
  at launch and fails closed (`exit /b 1`) when absent.
- `postgres`: launcher reads `AGENT_CORE_POSTGRES_PASSWORD` from the Windows User environment
  into process-local `PGPASSWORD`; it is never echoed.
- `playwright`, `filesystem`, `sequential-thinking`: no credentials.

`config.json` secret-pattern scan (`ghp_|gho_|password=|PGPASSWORD=`) returned 0 matches.

## Security review

| Surface | Access | Residual risk (operator accepted) |
| --- | --- | --- |
| `filesystem` | read + write over `D:\`, `E:\`, `C:\Users\ynotf` | Whole-drive roots are otherwise Forbidden by `MCP_CLASSIFICATION_MATRIX`. `E:\Swarm` and profile secrets (`.ssh`, `.zcode`, browser data) are reachable. This grants no capability Trust Class A native tools did not already have, but it is an MCP-visible write surface. |
| `github` | 26 tools, write-capable (`push_files`, `merge_pull_request`, `create_repository`) | PAT scopes include `admin:org`, `repo`, `workflow`, `write:packages`. Archived package. Tool calls act as `ynotfins`. |
| `postgres` | 1 tool (`query`), superuser `postgres` on `agent_core` | RLS is bypassed by superuser. Hardened with `default_transaction_read_only=on`; a `CREATE TABLE` probe is rejected with `cannot execute CREATE TABLE in a read-only transaction`. Archived package. |
| `playwright` | 24 tools, bounded write, isolated `mcp-chrome-*` profiles | Can drive a real Chrome instance and reach the network. `browser_run_code_unsafe` executes arbitrary JS in page context. |
| `sequential-thinking` | 1 tool, read-only | None material; state is per-process. |

## Deviations granted

1. Five direct MCP entries where current policy prefers one gateway entry.
2. Whole-drive filesystem roots (`D:\`, `E:\`) plus the user profile.
3. Raw SQL against PG18 `agent_core` from an IDE.
4. Two archived packages (`server-github`, `server-postgres`).

All four are explicit operator decisions, dated above. They do not amend `single-gateway` for any
other IDE and do not authorize pasting the upstream registry into other clients.

## Pre-existing defect repaired

The Bifrost Playwright upstream was `active` in the catalog but failed at
`initializeServer: Chromium distribution 'chrome' is not found at
C:\Users\ynotf\AppData\Local\Google\Chrome\Application\chrome.exe`. Chrome 156.0.8078.74 is
installed machine-wide under `C:\Program Files\Google\Chrome\Application`.

Repair (host-scoped, no config change):
`cmd /c mklink /J "C:\Users\ynotf\AppData\Local\Google\Chrome\Application" "C:\Program Files\Google\Chrome\Application"`.
The gateway route then passed `browser_navigate` → `browser_snapshot` → `browser_close`.

## Verification (2026-10-31, all commands run locally)

| Check | Result |
| --- | --- |
| `config.json` parses (`ConvertFrom-Json`) | `JSON_OK`, 9 servers |
| secrets in `config.json` | 0 matches |
| `sequential-thinking` `tools/list` | `ok`, server `2.0.0`, 1 tool |
| `filesystem` `tools/list` | `ok`, server `2.1.0`, 14 tools |
| `filesystem` `list_allowed_directories` | `D:\`, `E:\`, `C:\Users\ynotf` |
| `playwright` `tools/list` | `ok`, 24 tools |
| `playwright` `browser_navigate` | `ok`, `https://example.com` → `Example Domain` |
| `github` `search_repositories` | `ok`, live result `modelcontextprotocol/servers` |
| `postgres` `query` | `ok`, `db=agent_core`, `usr=postgres`, `ro=on` |
| `postgres` write probe | rejected: `cannot execute CREATE TABLE in a read-only transaction` |

ZCode must be restarted for the new entries to appear; the config change is
`configured_restart_required`, not yet `live_validated` in-product.

## Rollback

1. Restore `C:\Users\ynotf\.zcode\cli\config.json` from `config.json.bak-20261031-051205`.
2. Delete `I:\LocalApps\ZCode\mcp\{playwright,filesystem,github,postgres,sequential-thinking}-mcp-launch.cmd`.
3. Restart ZCode.
4. Optional: remove the Chrome junction if the gateway Playwright route is retired.

No Bifrost, registry, database, or gateway state was changed; nothing else needs reverting.

## Not changed

- `agentcore-gateway` entry and the process-attested loopback contract
- `contracts/bifrost-upstream-mcp-registry.json` and Bifrost runtime
- PostgreSQL schema, roles, and data
- Swarm routes, memory authority, model routing
- Other IDE profiles
