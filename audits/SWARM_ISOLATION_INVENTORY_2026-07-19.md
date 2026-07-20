# Desplega / Agent Swarm Isolation Inventory (read-only)

**Date:** 2026-07-19  
**Mutation policy:** **NONE** — no clean, commit, start, stop, rebuild, edit, or Docker changes  
**Bifrost:** no Swarm/Desplega upstream added to registry

## Path disambiguation

| Path | Identity | Notes |
| -- | -- | -- |
| `D:\github\agent-swarm` | **Desplega** `@desplega.ai/agent-swarm` | Product source; Git `main` @ `6c5e972c`; package version **1.101.0** |
| `D:\AgentSwarm` | **AgentCore runtime root** | artifacts/cache/runs (~28.4 MB); **not** Desplega product |
| Desplega-specific alternate install | not found as a separate product root | Names alone are not identity |

## Git / dirty state (`D:\github\agent-swarm`)

- Branch: `main`
- HEAD: `6c5e972c` (observed at inventory time)
- Dirty: **yes** — untracked includes `.serena/`, designs, migrations, templates (exact set may drift)
- **Operator instruction:** preserve dirty state; do not clean or commit from AgentCore rollout

## Runtime / Docker

- Desplega/Swarm containers: **none running** at inventory time
- Unrelated exited Docker containers may exist; ignored
- Docker services: **not started** by this plan

## Storage footprint (approx)

| Path | Size |
| -- | -- | 
| `D:\AgentSwarm` | ~28.4 MB |
| `D:\github\agent-swarm` | ~46.2 MB |

## Isolation contract

- Do **not** point Desplega at AgentCore PostgreSQL 18 (`127.0.0.1:55433`)
- Do **not** point Desplega at Bifrost / `agentcore-gateway` virtual keys
- Do **not** route non-Swarm IDE memory through SwarmRecall/SwarmVault
- SwarmRecall/SwarmVault/SwarmClaw remain a **separate ecosystem**

## Operator-approved future test plan (not executed)

1. Explicit operator approval for a disposable Desplega sandbox only
2. Separate Docker/network namespace; no shared AgentCore DB or Bifrost VK
3. Read-only health probes; no production Swarm data mutation
4. Evidence under `artifacts/` only; no Bifrost registry enrollment

## Status

`SWARM ISOLATION INVENTORIED — NO MUTATION`
