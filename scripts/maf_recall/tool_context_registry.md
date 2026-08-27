# Tool / Context Registry (MAF Recall Realignment)

Canonical locations for tools and context planes. Do **not** invent alternate URLs.

## SwarmRecall REST
| Field | Value |
|-------|-------|
| Role | Neutral semantic memory / context plane API |
| Endpoint | http://127.0.0.1:3300 |
| Client path | Server-side via agentcore-gateway then agentcore-memory only |
| Forbidden | Raw Recall MCP in IDE; Recall API keys in IDE JSON; direct SQL |

## SwarmRecall Postgres (service-owned)
| Field | Value |
|-------|-------|
| Port | 127.0.0.1:65432 |
| Rule | No AgentCore or IDE direct connection |

## SwarmVault filesystem
| Field | Value |
|-------|-------|
| Hot root | H: (Swarm ecosystem) |
| Access | Adapter-only from AgentCore; mutable facts owned by swarm-ecosystem-control |

## LangGraph runtime
| Field | Value |
|-------|-------|
| Authority | AgentCore workflow (not SwarmClaw) |
| Checkpoints | PostgreSQL 18 127.0.0.1:55433 database agent_core (public.checkpoints*) |
| Studio | Dev-only 127.0.0.1:2024 — never share production thread IDs |
| Hot disk | F: |

## Docker CLI / engine
| Field | Value |
|-------|-------|
| Engine / WSL VHDX | F:/Docker/wsl |
| App binds | I:/LocalApps (e.g. Devin Outpost) |
| Forbidden defaults | VHDX on C: or D:; mounting F:/H: production trees into third-party workers |

## OpenHands runtime
| Field | Value |
|-------|-------|
| Role | Fourth execution runtime / Agent Canvas |
| Mode | Docker-first local runtime |
| Image | ghcr.io/openhands/agent-canvas:1.13.0 |
| Container | openhands-local-8003 |
| URL | http://127.0.0.1:8003/canvas/ |
| Ready probe | http://127.0.0.1:8003/ready |
| State bind | I:/LocalApps/OpenHands/state |
| Project bind | D:/OpenHandsProjects |
| Forbidden | F:/ production mounts; H:/ Swarm mounts; non-localhost publish |

## Foundry Local
| Field | Value |
|-------|-------|
| Role | Local GPU inference on 4070 SUPER |
| Not | Foundry cloud memory; not SwarmRecall; not LangGraph checkpointer |

## OpenRouter
| Field | Value |
|-------|-------|
| Inference | Allowed via configured model routes / IDE model settings |
| MCP | Dormant behind Bifrost; do not add https://mcp.openrouter.ai/mcp to IDE baselines |
| Tools | Appear only under M6 lease + JIT VK bridge as exact openrouter-* names through :8080 |

## Explicit non-URLs
- Forbidden fiction: postgres://localhost:5432/agent_memory
- Forbidden fiction: New MAF-owned Postgres data directory on F: for agent memory
- Correct semantic store: SwarmRecall (:3300 / :65432 service-owned)
- Correct AgentCore durable DB: PG18 :55433

## Mandatory reasoning / discovery toolchain

For a high-assistance vibe-coder workflow, agents should not freehand complex tasks.

| Tool | When it is mandatory | Purpose |
|------|----------------------|---------|
| Sequential Thinking | Any non-trivial planning, migration, debugging, or multi-step task | Force explicit stepwise reasoning and critique before acting |
| AgentCore memory (`startup_context`, `retrieve_context`, `build_handoff`) | Any task that spans sessions, long prompts, architecture, or recovery | Restore durable context so the operator does not have to restate large prompts |
| Serena (or project-local semantic equivalent) | Cross-file edits, refactors, unfamiliar execution flow, symbol tracing | Semantic code understanding before modification |
| Depwire / Depra-class dependency tooling | Structural edits, dependency changes, repo graph questions | Reveal dependency edges and affected surfaces |
| Tentra | Milestone entry/exit or architecture graph evidence when required | Produce higher-level structure evidence instead of ad-hoc guessing |

If a required tool is unavailable, the agent should say so explicitly and use the safest bounded fallback rather than pretending the tool path happened.
