# Docker Relocation Audit + New API — Phase 8

**Date:** 2026-07-25

## Docker storage audit

| Item | Value |
| --- | --- |
| Docker Desktop | 4.81.0 (232925) / Engine 29.6.1 |
| Context | `desktop-linux` |
| VHDX (primary data) | `C:\Users\ynotf\AppData\Local\Docker\wsl\disk\docker_data.vhdx` (~**18.9 GB**) |
| Aux VHDX | `...\Docker\wsl\main\ext4.vhdx` (~0.11 GB) |
| Target plan path | `H:\AgentRuntime\docker` |

**Fact:** High-volume Docker data **is still on C:**.

**Relocation:** **Operator-gated / not executed this phase.** Moving the Docker Desktop disk image requires Docker Desktop’s supported disk-image relocation UI/API, a full Docker quit, and restart recovery validation. Manual VHDX moves are forbidden. Best-practice risk: Tier 4 storage move — do not auto-execute without an explicit operator maintenance window.

## Inventory (summary)

Running Compose projects:

- `newapi` → `D:\github\new-api\docker-compose.yml` (3 containers healthy)
- `deploy` → `D:\github\emu\deploy\docker-compose.yml` (`emu-postgres`)

Stopped leftovers: gitea, docker101 nginx, frappe/devcontainer stack.

## New API (already deployed)

Contrary to a greenfield deploy assumption, New API is **already live**:

| Container | Image | Status |
| --- | --- | --- |
| `agentcore-newapi` | `calciumion/new-api:latest` | healthy |
| `agentcore-newapi-postgres` | `postgres:15-alpine` | healthy (app-owned; **not** `agent_core` / `cognee_core`) |
| `agentcore-newapi-redis` | `redis:7-alpine` | healthy |

- Compose + data: `D:\github\new-api\` (data under `./data`, gitignored)
- Status API: `http://127.0.0.1:3000/api/status` → 200 `success`
- Docs: `docs/CHERRY_NEWAPI_INTEGRATION.md`

### Hardening applied this phase

Compose port binding tightened from `0.0.0.0:3000` to **`127.0.0.1:3000`** in `D:\github\new-api\docker-compose.yml`. Operator should recreate the service to apply:

```powershell
cd D:\github\new-api
docker compose up -d
```

## Cherry token

Least-privilege Cherry → New API token configuration remains operator UI work (secret materialization in Cherry LevelDB only). Do not commit tokens.

## Signals

- `DOCKER_DATA_ON_C_OPERATOR_RELOCATION_REQUIRED`
- `NEW_API_ALREADY_DEPLOYED_LOCALHOST_BIND_HARDENED`

**Phase 8 exit:** Audit complete; New API present; localhost bind patched in compose; Docker VHDX relocation deferred to operator window.
