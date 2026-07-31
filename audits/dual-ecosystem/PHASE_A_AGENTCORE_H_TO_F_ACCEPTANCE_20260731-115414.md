# Phase A Acceptance — AgentCore H: → F:\AgentCore\runtime

**Timestamp:** 2026-07-31T15:59:00Z (local evidence stamp `20260731-115414`)  
**Gate for Swarm H: writes:** PASSED

## Result

AgentCore Bifrost and hot AgentRuntime leaves now run from `F:\AgentCore\runtime`. Public gateway identity remains `http://127.0.0.1:8080/mcp`. Durable rollback is on E: only. `H:\AgentRuntime` removed after cutover.

## Evidence

| Check | Result |
|---|---|
| Live bifrost-http `-app-dir` | `F:\AgentCore\runtime\bifrost` |
| Scheduled task RuntimeRoot | `F:\AgentCore\runtime\bifrost` |
| Kill → task restart from F: | PASS (PID recovered on F:) |
| `Test-AgentCoreBifrostGateway.ps1` | **RESULT: PASSED** |
| MCP initialize + tools/list | 161 tools; `agentcore_memory` / `agentcore_project_router` present |
| Forbidden Swarm/postgres tool patterns | Absent |
| Cursor global MCP still agentcore-gateway only | PASS |
| Rendered `config.json` H:\AgentRuntime refs | 0 |
| `validate_contracts.py` | PASS |
| Durable rollback | `E:\AgentCore-Backups\pre-h-relocation-20260731-115414\` |
| Residual H: archive after clearance | `E:\AgentCore-Backups\retired-h-agentruntime-after-f-cutover-20260731-115414\` |
| `H:\AgentRuntime` exists | **False** |
| `TENTRA_DATA_DIR` (User) | `F:\AgentCore\runtime\tentra\data` |

## Authority / ops updates

- `PROJECT_ANCHOR.md`, `BLUEPRINT.md`, `CONTEXT_BLOCK.md` drive ownership (F: AgentCore hot; H: Swarm-reserved)
- `contracts/bifrost-upstream-mcp-registry.json` `runtime_root`
- Bifrost launch/install/start/stop/test/backup/restore/rotate scripts
- `scripts/bifrost/render_bifrost_config.py`, `scripts/agentcore_memory/server.py`
- Validators / health / durability path defaults
- Install/Test scripts resolve `py`/`python`/`Python313` (PATH robustness)

## Non-authoritative leftovers on H:

`H:\DevCache`, `H:\AgentScratch`, `H:\AIModels`, `H:\Scratch`, etc. remain rebuildable/non-canonical and are not AgentCore rollback. Swarm Phase B may use H: for Swarm roots; these leftovers should be cleaned or ignored without treating them as AgentCore authority.

## Rollback

Restore from `E:\AgentCore-Backups\pre-h-relocation-20260731-115414\AgentRuntime` into `F:\AgentCore\runtime` (or re-register task to a restored tree). Do not re-colonize H: once Swarm Phase B begins.
