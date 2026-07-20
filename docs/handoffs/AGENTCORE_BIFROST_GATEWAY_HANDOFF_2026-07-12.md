# AgentCore Bifrost Gateway Handoff — 2026-07-12

> **Historical cutover evidence.** Architecture decisions below remain valid under `BLUEPRINT.md` / `PROJECT_ANCHOR.md`. For live status after 2026-07-12 (memory live, M6, OpenRouter OAuth/JIT, Cherry/LangGraph enrollment), prefer `CONTEXT_BLOCK.md` §0a, `docs/operations/OPENROUTER_MCP.md`, `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`, and dated audits under `audits/`.

**Source authority:** `D:\github\agentcore-control-plane`
**Runtime:** `H:\AgentRuntime\bifrost`
**Pin:** Bifrost native Windows `bifrost-http.exe` **v2.0.0-prerelease1**
**Endpoint:** `http://127.0.0.1:8080/mcp` (`agentcore-gateway`)
**Cursor global MCP:** `C:\Users\ynotf\.cursor\mcp.json` (no project-level gateway duplicates)

## Operator decisions (final)

1. Bifrost native Gateway is the workstation MCP gateway (not Go SDK).
2. Non-Swarm IDEs connect to one endpoint with Bearer `BIFROST_MCP_VIRTUAL_KEY`.
3. SwarmRecall/SwarmVault/SwarmClaw are a separate ecosystem — not required for non-Swarm IDEs.
4. Stable memory identity: `agentcore-memory` (ten-tool surface; now live via gateway — do not invent alternate memory MCP entries).
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

(In-repo run during docs update: schemas valid; current registry validates as 12 enabled / 4 disabled-deferred servers.)

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
- Authenticated MCP `initialize` and `tools/list` succeeded through Bifrost; current repaired visible tool count is 127.
- Expected prefixes present: `arabold_docs`, `depwire`, `tentra`, `sequential_thinking`, `context_fabric`, `playwright`, `cursor_agent_mcp`, `filesystem`, `agentcore_memory`, `agentcore_project_router`.
- Swarm tool prefixes and raw database/whole-drive tool indicators were not present in the visible catalog.
- Sanitized evidence is under `artifacts/bifrost-gateway-cutover-2026-07-12/`.

## Runtime repair — 2026-07-14

- Root cause of Cursor `net::ERR_CONNECTION_REFUSED`: no durable Bifrost listener was present on `127.0.0.1:8080`. The scheduled task could start Bifrost, but the start wrapper failed to recognize health and launched a direct fallback that stopped the working task-owned listener.
- Fixed startup owner: `\AgentCore\AgentCore-Bifrost-Gateway` runs `ops\bifrost\Launch-AgentCoreBifrostGateway.ps1` as a long-running foreground owner for `bifrost-http.exe`.
- Runtime bind: `H:\AgentRuntime\bifrost\bin\bifrost-http.exe -app-dir H:\AgentRuntime\bifrost -host 127.0.0.1 -port 8080 -log-level info -log-style json`.
- Logs: `H:\AgentRuntime\bifrost\logs\bifrost-gateway.stdout.log`, `H:\AgentRuntime\bifrost\logs\bifrost-gateway.stderr.log`, and `H:\AgentRuntime\bifrost\logs\logs.db`.
- Cursor global config now contains only `agentcore-gateway`; `MCP_DOCKER` was removed after profile audit showed overlap plus broken `desktop-commander.paths`.
- Direct MCP `initialize`, `tools/list`, and safe `arabold_docs-list_libraries` call passed after managed restart. Swarm tools were absent.
- Current upstream caveat: `obsidian_vault` and `serena` may be disconnected until their separate upstream health is repaired; the gateway itself remains healthy.

## Attach for continuation

See `DOC_AUTHORITY.md` “What to attach to a new chat”.
