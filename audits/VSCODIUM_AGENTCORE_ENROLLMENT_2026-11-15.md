# VSCodium AgentCore gateway enrollment — 2026-11-15

**Host:** ChaosCentral  
**Operator approval:** Tony, 2026-11-15 1:01 AM America/New_York, "Yes add VSCodium to the control plane and installing the agentcore-gateway MCP in VSCodium".  
**Repo worktree:** `D:\github\agentcore-control-plane\.worktrees\feat-enroll-vscodium` on `feat/enroll-vscodium` (branched from local `main` `a53b638`; no fetch/pull).  

This report records source enrollment plus the approved live VSCodium MCP write. It does not claim `live_validated` native lifecycle.

## Scope and non-goals

- Added first-class client artifacts under `ide-profiles/vscodium/`, `renderers/gateway-clients/vscodium.json`, matrix/README, tests, and a contract-hint proposal.
- Did **not** edit operator-locked or governed-mutable authority files (`PROJECT_ANCHOR.md`, `AGENTS.md`, `DOC_AUTHORITY.md`, `BLUEPRINT.md`, `MASTER_CONFIG_AND_PROMPT.md`, `CONTEXT_BLOCK.md`, `contracts/agentcore-gateway-client.json`, `contracts/bifrost-upstream-mcp-registry.json`, `docs/agent-policy/**`).
- Did **not** touch `H:`, nfa-platform, or NFA sister projects. No reboot. No service restarts.
- Distinct from the Cursor-hosted `zoo-code` profile, which remains unchanged.

## Live MCP write (VSCodium only)

Timestamped backups (1:07 AM America/New_York, 2026-11-15):

- `C:\Users\ynotf\AppData\Roaming\VSCodium\User\mcp.json.bak-20261115-0107`
- `C:\Users\ynotf\AppData\Roaming\VSCodium\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json.bak-20261115-0107`

Both live files now contain one AgentCore entry, `agentcore-gateway`:

- URL: `http://127.0.0.1:8080/mcp`
- Type: `streamable-http`
- Auth: `Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}` (env reference only; no resolved value written)
- Existing `minimax-design` and `omniroute` servers were preserved

Rollback: copy each `.bak-20261115-0107` over the corresponding live file.

## Verification

| Check | Result |
| --- | --- |
| NFA `http://127.0.0.1:8787/health` before write | `{"status":"ok"}` |
| NFA `http://127.0.0.1:8787/health` after write | `{"status":"ok"}` |
| Bifrost `http://127.0.0.1:8080/health` | `{"status":"ok"}` (components.db_pings ok) |
| Authenticated `initialize` + `tools/list` with the same env-backed bearer the config references | HTTP 200; **168 tools** |
| `agentcore_memory-*` ten-tool surface present | yes (all ten names present) |
| Native VSCodium / Zoo Code UI restart and memory-lifecycle acceptance | **not done** — restart/reload required; do not mark `live_validated` |

The 168-tool count is a point-in-time authenticated gateway probe, not a value copied into the live MCP files or a certification of native host discovery.

## Repo validation

- `python scripts/bifrost/test_vscodium_profile.py` (Python 3.13): **5 passed**
- `python scripts/bifrost/validate_ide_enrollment_scope.py`: **OK**
- `python scripts/render_ide_rules.py --check`: **OK** (includes the new profile)
- `python scripts/bifrost/validate_contracts.py`: **OK**
- `python scripts/bifrost/test_contracts.py`: **228 passed / 8 failed** — failure names unchanged in kind from baseline `main` `a53b638` (220 passed / 8 failed). The 8 new passes are automatic IDE checks for the new profile. Failures are pre-existing on `main` (antigravity renderer, claude-desktop matrix/profile drift, Task 2 import, research MCP, nia/figma profile sets, depwire/tentra dormancy).
- `python -m pytest scripts/bifrost/test_client_secret_policy.py -q`: **4 failed, 4 passed** on both this branch and baseline `main` (same four failures; none reference VSCodium).

## Proposed governed-mutable contract change

See `governance/proposals/2026-11-15-vscodium-gateway-client-hint.md` for the exact `client_render_hints.vscodium` patch. It is not applied in this change.
