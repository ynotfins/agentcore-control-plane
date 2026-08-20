# Zoo Code Qdrant Runtime

Status: active on `setup/zoo-code-qdrant-nfa-20260820`

## Purpose

This runtime exists only for Zoo Code Codebase Indexing inside Cursor. It is a rebuildable semantic source-code index for NFA refactor work, not AgentCore memory, documentation authority, project evidence, or a second canonical database.

## Authority

- AgentCore authority: `D:\github\agentcore-control-plane`
- Consumer: Zoo Code extension in Cursor
- Runtime class: `REBUILDABLE_DERIVED_CODE_INDEX`
- Storage policy: neutral local app data under `I:\LocalApps\ZooCode\qdrant`
- Source remains canonical Git; loss of this Qdrant store must be recoverable by reindexing.

## Installed Target

- Qdrant version: `1.19.0`
- Release source: `https://github.com/qdrant/qdrant/releases/tag/v1.19.0`
- Windows asset: `qdrant-x86_64-pc-windows-msvc.zip`
- Runtime root: `I:\LocalApps\ZooCode\qdrant`
- Executable: `I:\LocalApps\ZooCode\qdrant\current\qdrant.exe`
- Config: `I:\LocalApps\ZooCode\qdrant\config\zoo-code-qdrant.yaml`
- Storage: `I:\LocalApps\ZooCode\qdrant\storage`
- Logs: `I:\LocalApps\ZooCode\qdrant\logs`
- HTTP: `http://127.0.0.1:6333`
- gRPC: `127.0.0.1:6334`
- Distributed port `6335`: disabled/not used

## Security Decision

Qdrant is bound to `127.0.0.1` only. No Qdrant API key is configured for this local developer index because Qdrant's own configuration guidance notes API keys should be paired with TLS, and this deployment is intentionally loopback-only with no LAN/tailnet listener. If the threat model changes, add TLS and an environment-provided API key together; do not put secrets on command lines or in Git.

## Lifecycle

Non-elevated Codex cannot create an SCM Windows Service. Current lifecycle owner is a governed hidden scheduled task:

- Task path/name: `\AgentCore\ZooCode-Qdrant`
- Trigger: current user logon
- Start command: `ops\zoo-code\Start-ZooCodeQdrant.ps1`
- Stop command: `ops\zoo-code\Stop-ZooCodeQdrant.ps1`
- Health command: `ops\zoo-code\Test-ZooCodeQdrant.ps1`
- Latest accepted report: `I:\LocalApps\ZooCode\qdrant\reports\zoo-code-qdrant-test-20260820-190800.json`

Promotion to a true Windows Service remains an admin-gated follow-up. If promoted, keep the same root, config, ports, logs, health check, registry id, and rollback procedure.

## Zoo Code Configuration

Installed Zoo Code version observed in Cursor:

- Extension ID: `zoocodeorganization.zoo-code`
- Version: `3.79.100392`
- Extension path: `C:\Users\ynotf\.cursor\extensions\zoocodeorganization.zoo-code-3.79.100392-universal`
- Global MCP config: `C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json`
- Global modes config: `C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\zoocodeorganization.zoo-code\settings\custom_modes.yaml`

Zoo Code stores non-secret Codebase Indexing config in extension state under `codebaseIndexConfig`; provider and Qdrant secrets use VS Code/Cursor secret storage. Do not patch Cursor's live `state.vscdb` directly while Cursor is running. Configure the indexer through the Zoo Code UI unless a supported Zoo CLI/API becomes available.

Recommended NFA setup values:

- `codebaseIndexEnabled`: true
- `codebaseIndexQdrantUrl`: `http://127.0.0.1:6333`
- `codebaseIndexEmbedderProvider`: keep the provider that passes Zoo's own test; OpenRouter is supported by the installed extension, but embedding model availability must be verified in the Zoo UI/provider route.
- `codebaseIndexSearchMinScore`: `0.4`
- `codebaseIndexSearchMaxResults`: `50`
- Target repositories for indexing: `D:\github\nfa-platform`; optionally `D:\github\nfa-alerts-enterprise` as read-only behavioral evidence. Do not add a Web target.

Current live-state boundary:

- Qdrant runtime is installed, registered, started, and health-checked.
- Zoo global NFA modes are installed in `custom_modes.yaml`.
- Zoo Code embedding-provider/API-key selection remains inside the Zoo Code UI and Cursor secret storage; no secret value was written by this setup.

## Validation

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\zoo-code\Test-ZooCodeQdrant.ps1
```

Acceptance requires:

- HTTP health/version reachable on `127.0.0.1:6333`
- gRPC listener on `127.0.0.1:6334`
- no listener on `6335`
- no `0.0.0.0`, LAN, or tailnet listener for Qdrant
- create/query/delete disposable collection passes
- no API key or token appears in Qdrant process command line
- `\AgentCore\ZooCode-Qdrant` exists and points at the governed start script

## Stop Gate

This setup does not start the NFA refactor. After Qdrant and Zoo Code indexing are validated, the next safe action is a separate NFA audit/refactor planning task for Android, iOS, Windows, and macOS only.
