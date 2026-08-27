# MAF Recall Realignment — Corrected Architecture

This document corrects common Copilot / generic-assistant mistakes about how AgentCore,
SwarmRecall, Bifrost, Docker, and future MAF fit together on this PC.

## Mistakes this realignment rejects

| Copilot-style claim | Correct fact |
|---------------------|--------------|
| Stand up Postgres on localhost:5432 for agent memory | Semantic memory is **SwarmRecall** (service Postgres **:65432**). AgentCore durable DB is PG18 **:55433**. No new MAF Postgres on F:. |
| Add SwarmRecall MCP to every IDE | Shared memory/tool policy goes through **agentcore-gateway**; Recall is reached **server-side** via agentcore-memory. Vendor-native local helpers may remain only as documented exceptions. |
| Put Docker VHDX on C: or next to repos on D: | Docker WSL VHDX belongs under **F:/Docker/wsl**. |
| MAF replaces Bifrost / LangGraph | MAF is a **later SDK host** behind :8080. Bifrost stays the MCP aggregator; LangGraph stays AgentCore workflow authority on F:. |
| Mount F: and H: into Devin/OpenHands for convenience | Devin Outpost and OpenHands bind only their approved `I:/LocalApps/...` and `D:/...Projects` roots; no docker.sock or production F:/H: mounts by default. |
| Foundry Local equals cloud memory | Foundry Local is **local GPU inference** (4070 SUPER), not Foundry cloud memory and not a Recall substitute. |

## Layer diagram

```mermaid
flowchart TB
  subgraph clients [IDE / Host Clients]
    Cursor[Cursor]
    Codex[Codex]
    Other[Claude / MiniMax / ...]
    MAF[MAF host spike later]
  end
  subgraph mcp [Common MCP plane]
    GW[agentcore-gateway :8080]
  end
  subgraph bifrost [Bifrost on F:]
    BF[Bifrost runtime]
    AM[agentcore-memory facade]
  end
  subgraph recall [Neutral SwarmRecall]
    REST[Recall REST :3300]
    MEILI[Meilisearch :7700]
    RPG[Recall PG :65432]
  end
  subgraph agentcore [AgentCore hot F:]
    PG18[PG18 :55433]
    LG[LangGraph / workflow]
  end
  subgraph swarm [Swarm hot H:]
    Vault[SwarmVault]
    Claw[SwarmClaw :3456]
  end
  subgraph docker [Docker]
    VHDX[WSL VHDX F:/Docker/wsl]
    Binds[App binds I:/LocalApps]
    OH[OpenHands :8003]
  end
  Cursor --> GW
  Codex --> GW
  Other --> GW
  MAF -. > GW
  GW --> BF
  BF --> AM
  AM --> REST
  REST --> RPG
  REST -. > MEILI
  BF --> LG
  LG --> PG18
  AM -. > Vault
  Claw --> REST
  OH --- Binds
  VHDX --- Binds
```

## Live ports (verify after reboot)

| Port | Service | Client rule |
|------|---------|-------------|
| **8080** | Bifrost / agentcore-gateway MCP | Only IDE MCP URL |
| **55433** | PostgreSQL 18 AgentCore | Trusted admin/ingest only; not IDE |
| **65432** | Neutral SwarmRecall Postgres | **Never** IDE or AgentCore direct SQL |
| **3300** | SwarmRecall REST | Server-side / adapter; not raw IDE MCP |
| **7700** | Meilisearch for SwarmRecall | Service-owned; not IDE baseline |
| **3456** | SwarmClaw runtime | Separate execution plane; not IDE baseline |
| 55432 | PG16 legacy | Offline rollback evidence only |
| 2024 | LangGraph Studio | Dev-only; separate from production threads |
| 8003 | OpenHands Agent Canvas | Localhost-only Docker runtime |

## Drive ownership

- **F:** AgentCore hot (Bifrost, PG18, Docker VHDX, LangGraph runtime data)
- **H:** Swarm hot (Vault / Claw / Swarm-local) — AgentCore read-only by default
- **I:/LocalApps:** Neutral local apps (Devin Outpost binds)
- **D:/OpenHandsProjects:** OpenHands project execution root
- **D:/github/...:** Git source authority
- **E:** Archive / cold backups (E:/LocalApps/Backups)

## Professional baseline

- Use one governed external gateway for shared memory, shared tools, and cross-IDE policy.
- Allow app-native built-ins only when they are explicitly documented and do not become a shadow memory or database plane.
- Keep active repositories off a OneDrive-backed Desktop. Desktop is fine for shortcuts and light documents, not for live repos, binds, or runtime state.
- Keep local Devin as the default coder path. Use Outposts only when you explicitly want isolated long-running execution.
- Keep OpenHands Docker-first for Agent Canvas. It is the fourth runtime, not a replacement for LangGraph, SwarmClaw, or Devin.

## MAF placement (future)

```
IDE / MAF SDK host
    -> agentcore-gateway :8080
        -> Bifrost
            -> agentcore-memory -> SwarmRecall :3300 semantic
            -> LangGraph / PG18 :55433 checkpoints / workflow
```

MAF must not open a second conflicting HTTP server on :8080 and must not create postgres://localhost:5432/agent_memory.

## Four runtime target

| Runtime | Execution | Staging | Collision rule |
|---------|-----------|---------|----------------|
| LangGraph | Native AgentCore workflow on F:/PG18 | Studio only on :2024 | Never write checkpoints to Recall/Vault/Claw |
| SwarmClaw | Native Swarm runtime on H: | Swarm-owned only | Never use Bifrost as its runtime memory |
| Devin | Local-first CLI/Desktop; optional Docker Outposts | I:/LocalApps/Devin | No docker.sock; no F:/H: mounts |
| OpenHands | Docker-first Agent Canvas | I:/LocalApps/OpenHands + D:/OpenHandsProjects | Localhost-only :8003; no F:/H: mounts |
