# AgentCore Bifrost Gateway Handoff — 2026-07-12

**Source authority:** `D:\github\agentcore-control-plane`
**Runtime:** `H:\AgentRuntime\bifrost`
**Pin:** Bifrost native Windows `bifrost-http.exe` **v2.0.0-prerelease1**
**Endpoint:** `http://127.0.0.1:8080/mcp` (`agentcore-gateway`)
**Cursor global MCP:** `C:\Users\ynotf\.cursor\mcp.json` (no project-level gateway duplicates)

## Operator decisions (final)

1. Bifrost native Gateway is the workstation MCP gateway (not Go SDK).
2. Non-Swarm IDEs connect to one endpoint with Bearer `BIFROST_MCP_VIRTUAL_KEY`.
3. SwarmRecall/SwarmVault/SwarmClaw are a separate ecosystem — not required for non-Swarm IDEs.
4. Stable memory identity: `agentcore-memory` (may be degraded until memory platform lands).
5. Drive map includes H (runtime), I (scratch), J (portable) — see `PROJECT_ANCHOR.md`.
6. Config authority = this Git repo; runtime = H:\AgentRuntime\bifrost.
7. Go SDK experiment remains `experiments/bifrost-go-sdk-smoke` only.

## What is implemented in repo (do not invent extra validation)

| Area | Path / status |
| -- | -- |
| Upstream registry | `contracts/bifrost-upstream-mcp-registry.json` |
| Gateway client contract | `contracts/agentcore-gateway-client.json` |
| Schemas | `contracts/schemas/*bifrost*`, `*agentcore-gateway*` |
| Render / validate | `scripts/bifrost/render_bifrost_config.py`, `validate_contracts.py` |
| Project router | `scripts/project_router/` + wrappers |
| Memory health MCP | `scripts/agentcore_memory/server.py` |
| Ops lifecycle | `ops/bifrost/*.ps1` |
| IDE renderers | `renderers/gateway-clients/` |
| Sanitized Bifrost render | `renderers/bifrost/` |
| Authority docs | `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, `AGENTS.md`, `MASTER_CONFIG_AND_PROMPT.md` |
| ADRs / bifrost docs | `docs/adr/ADR-2026-07-12-*.md`, `docs/bifrost/` |
| Install prompt | `docs/prompts/install-agentcore-gateway-in-ide.md` |
| Backup manifest | `artifacts/bifrost-gateway-cutover-2026-07-12/BACKUP_MANIFEST.md` |

Contract validation available via:

```powershell
python D:\github\agentcore-control-plane\scripts\bifrost\validate_contracts.py
```

(In-repo run during docs update: schemas valid; 14 enabled / 2 deferred servers.)

## Swarm exclusion

Do not modify Swarm product code. Do not require Swarm MCP in non-Swarm IDEs. OpenClaw/ClawX out of cutover scope.

## Next agent priorities

1. Complete/verify live IDE cutover evidence per client (migration runbook checkboxes — only mark when evidenced).
2. Keep `agentcore-memory` identity stable while building the memory platform.
3. Enable `depwire-cloud` / `github-mcp` only after health gates.
4. Index Bifrost docs in arabold-docs (`bifrost` / `2.0.0-prerelease1` / docs.getbifrost.ai) if not already current.
5. Do not treat Go SDK smoke as gateway.

## Cursor global validation — 2026-07-13

- Canonical live file: `C:\Users\ynotf\.cursor\mcp.json`.
- Canonical entry: `agentcore-gateway` → `http://127.0.0.1:8080/mcp` with `Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}`.
- Project-level duplicate scan across `D:\github\agentcore-control-plane`, `D:\github\memory-context-database`, and `D:\github` found no active project `.cursor\mcp.json` / `.mcp.json` gateway duplicates.
- Authenticated MCP `initialize` and `tools/list` succeeded through Bifrost; visible tool count was 139.
- Expected prefixes present: `arabold_docs`, `depwire`, `tentra`, `sequential_thinking`, `context_fabric`, `playwright`, `cursor_agent_mcp`, `filesystem`, `agentcore_memory`, `agentcore_project_router`.
- Swarm tool prefixes and raw database/whole-drive tool indicators were not present in the visible catalog.
- Sanitized evidence is under `artifacts/bifrost-gateway-cutover-2026-07-12/`.

## Attach for continuation

See `DOC_AUTHORITY.md` “What to attach to a new chat”.
